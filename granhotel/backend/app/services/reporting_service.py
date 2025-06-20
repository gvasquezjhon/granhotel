from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func as sql_func, and_, or_, distinct, case
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app import models
from app.models.room import Room
from app.models.reservations import Reservation, ReservationStatus
from app.models.pos import POSSale, POSSaleItem, POSSaleStatus, PaymentMethod # Added PaymentMethod from models
from app.models.product import Product, ProductCategory
from app.models.inventory import InventoryItem, StockMovement, StockMovementType
from app.models.billing import GuestFolio, FolioTransaction, FolioStatus, FolioTransactionType
from app.models.guest import Guest


# --- Occupancy Reports ---

def get_daily_occupancy_data(db: Session, target_date: date) -> Dict[str, Any]:
    '''Calculates occupancy data for a specific target_date.'''
    total_physical_rooms_query = db.query(sql_func.count(Room.id))
    # Add filter for active/operational rooms if such a status exists on Room model
    # total_physical_rooms_query = total_physical_rooms_query.filter(Room.status == "OPERATIONAL")
    total_physical_rooms = total_physical_rooms_query.scalar()

    if total_physical_rooms is None or total_physical_rooms == 0: # Check for None as well
        return {"date": target_date.isoformat(), "total_rooms": 0, "occupied_rooms": 0, "occupancy_rate": 0.0, "error": "No rooms in system or no operational rooms."}

    # Rooms considered occupied are those with CONFIRMED or CHECKED_IN reservations covering the target_date.
    # A reservation covers target_date if: check_in_date <= target_date < check_out_date
    occupied_rooms_count = db.query(sql_func.count(distinct(Reservation.room_id))).filter(
        Reservation.check_in_date <= target_date,
        Reservation.check_out_date > target_date, # check_out_date is the day of departure, so room is free on check_out_date
        Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN])
    ).scalar() or 0

    occupancy_rate = (occupied_rooms_count / total_physical_rooms) * 100 if total_physical_rooms > 0 else 0.0

    return {
        "date": target_date.isoformat(),
        "total_rooms": total_physical_rooms,
        "occupied_rooms": occupied_rooms_count,
        "occupancy_rate": round(occupancy_rate, 2)
    }

def get_occupancy_rate_over_period(db: Session, date_from: date, date_to: date) -> Dict[str, Any]:
    '''Calculates average daily occupancy and other metrics over a period.'''
    if date_from > date_to:
        raise ValueError("date_from cannot be after date_to")

    total_physical_rooms_query = db.query(sql_func.count(Room.id))
    # Add filter for active/operational rooms if such a status exists
    total_physical_rooms = total_physical_rooms_query.scalar()

    if total_physical_rooms is None or total_physical_rooms == 0:
        return {"date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "total_room_nights_available": 0, "total_room_nights_occupied": 0, "average_occupancy_rate": 0.0, "error": "No rooms in system."}

    num_days = (date_to - date_from).days + 1
    total_room_nights_available = total_physical_rooms * num_days

    # Sum of occupied room-nights: for each day in the period, count occupied rooms.
    # This can be optimized with a more complex SQL query if performance is critical for long periods.
    # For now, iterate daily using the existing get_daily_occupancy_data.
    total_room_nights_occupied = 0
    current_date_iter = date_from
    while current_date_iter <= date_to:
        daily_data = get_daily_occupancy_data(db, current_date_iter)
        total_room_nights_occupied += daily_data.get("occupied_rooms", 0)
        current_date_iter += timedelta(days=1)

    average_occupancy_rate = (total_room_nights_occupied / total_room_nights_available) * 100 if total_room_nights_available > 0 else 0.0

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "number_of_days": num_days,
        "total_physical_rooms": total_physical_rooms,
        "total_room_nights_available": total_room_nights_available,
        "total_room_nights_occupied": total_room_nights_occupied,
        "average_occupancy_rate": round(average_occupancy_rate, 2)
    }

def get_revpar_over_period(db: Session, date_from: date, date_to: date) -> Dict[str, Any]:
    '''Calculates Revenue Per Available Room (RevPAR) over a period.'''
    if date_from > date_to:
        raise ValueError("date_from cannot be after date_to")

    total_physical_rooms = db.query(sql_func.count(Room.id)).scalar() # Consider operational rooms only
    if total_physical_rooms is None or total_physical_rooms == 0:
        return {"date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "total_room_revenue": "0.00", "total_available_room_nights": 0, "revpar": "0.00", "error": "No rooms in system."}

    num_days = (date_to - date_from).days + 1
    total_available_room_nights = total_physical_rooms * num_days

    # Using datetime.combine with min.time() for start of day, and < start of next day for end of range.
    # Assuming FolioTransaction.transaction_date is DateTime with timezone.
    start_datetime = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    total_room_revenue = db.query(sql_func.sum(FolioTransaction.charge_amount)).filter(
        FolioTransaction.transaction_type == FolioTransactionType.ROOM_CHARGE,
        FolioTransaction.transaction_date >= start_datetime,
        FolioTransaction.transaction_date < end_datetime
    ).scalar() or Decimal("0.00")

    revpar = (total_room_revenue / total_available_room_nights) if total_available_room_nights > 0 else Decimal("0.00")

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_room_revenue": str(total_room_revenue.quantize(Decimal("0.01"))),
        "total_available_room_nights": total_available_room_nights,
        "revpar": str(revpar.quantize(Decimal("0.01")))
    }


# --- Sales Reports (POS) ---

def get_total_sales_by_period(db: Session, date_from: date, date_to: date, payment_method: Optional[PaymentMethod] = None) -> Dict[str, Any]:
    '''Calculates total sales from POS over a period, optionally filtered by payment method.'''
    start_datetime = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    query = db.query(
        sql_func.sum(POSSale.total_amount_after_tax).label("total_sales_after_tax"),
        sql_func.sum(POSSale.total_amount_before_tax).label("total_sales_before_tax"),
        sql_func.sum(POSSale.tax_amount).label("total_tax_amount"),
        sql_func.count(POSSale.id).label("number_of_sales")
    ).filter(
        POSSale.status == POSSaleStatus.COMPLETED,
        POSSale.sale_date >= start_datetime,
        POSSale.sale_date < end_datetime
    )
    if payment_method:
        query = query.filter(POSSale.payment_method == payment_method)

    result = query.first()
    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "payment_method_filter": payment_method.value if payment_method else None,
        "total_sales_after_tax": str((result.total_sales_after_tax or Decimal("0.00")).quantize(Decimal("0.01"))),
        "total_sales_before_tax": str((result.total_sales_before_tax or Decimal("0.00")).quantize(Decimal("0.01"))),
        "total_tax_amount": str((result.total_tax_amount or Decimal("0.00")).quantize(Decimal("0.01"))),
        "number_of_sales": result.number_of_sales or 0
    }

def get_sales_by_product_category(db: Session, date_from: date, date_to: date) -> List[Dict[str, Any]]:
    '''Calculates total sales grouped by product category.'''
    start_datetime = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    results = db.query(
        ProductCategory.name.label("category_name"),
        sql_func.sum(POSSaleItem.total_price_for_item_after_tax).label("total_sales_for_category")
    ).join(Product, POSSaleItem.product_id == Product.id)\
     .join(ProductCategory, Product.category_id == ProductCategory.id)\
     .join(POSSale, POSSaleItem.pos_sale_id == POSSale.id)\
     .filter(
        POSSale.status == POSSaleStatus.COMPLETED,
        POSSale.sale_date >= start_datetime,
        POSSale.sale_date < end_datetime
    ).group_by(ProductCategory.name).order_by(ProductCategory.name).all()

    return [{"category_name": r.category_name, "total_sales": str((r.total_sales_for_category or Decimal("0.00")).quantize(Decimal("0.01")))} for r in results]


# --- Inventory Reports ---

def get_inventory_summary(db: Session) -> List[Dict[str, Any]]:
    '''Provides current stock levels and value for all active products.'''
    results = db.query(
        Product.id.label("product_id"),
        Product.name.label("product_name"),
        InventoryItem.quantity_on_hand,
        Product.price.label("unit_value"),
        (InventoryItem.quantity_on_hand * Product.price).label("total_stock_value")
    ).join(InventoryItem, Product.id == InventoryItem.product_id)\
     .filter(Product.is_active == True)\
     .order_by(Product.name).all()

    return [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "quantity_on_hand": r.quantity_on_hand if r.quantity_on_hand is not None else 0,
            "unit_value": str((r.unit_value or Decimal("0.00")).quantize(Decimal("0.01"))),
            "total_stock_value": str((r.total_stock_value or Decimal("0.00")).quantize(Decimal("0.01")))
        } for r in results
    ]

# --- Financial Reports (Folios) ---

def get_folio_financial_summary(db: Session, date_from: date, date_to: date) -> Dict[str, Any]:
    '''Summarizes charges and payments from folio transactions over a period.'''
    start_datetime = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    total_charges = db.query(sql_func.sum(FolioTransaction.charge_amount)).filter(
        FolioTransaction.transaction_date >= start_datetime,
        FolioTransaction.transaction_date < end_datetime
    ).scalar() or Decimal("0.00")

    total_payments = db.query(sql_func.sum(FolioTransaction.payment_amount)).filter(
        FolioTransaction.transaction_date >= start_datetime,
        FolioTransaction.transaction_date < end_datetime
    ).scalar() or Decimal("0.00")

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_charges_posted": str(total_charges.quantize(Decimal("0.01"))),
        "total_payments_received": str(total_payments.quantize(Decimal("0.01")))
    }
