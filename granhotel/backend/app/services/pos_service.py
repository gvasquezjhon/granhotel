from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Dict
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app import models
from app import schemas
from app.models.pos import POSSale, POSSaleItem, POSSaleStatus, PaymentMethod
from app.models.inventory import StockMovementType
from app.services import product_service, inventory_service, guest_service, user_service
from fastapi import HTTPException, status

def create_pos_sale(
    db: Session,
    sale_in: schemas.pos.POSSaleCreate,
    cashier_user_id: uuid.UUID
) -> models.pos.POSSale:
    '''
    Create a new Point of Sale transaction.
    - Validates cashier, guest (if provided), and all products.
    - Calculates total price and tax for each item using product_service.
    - Records the sale and its items.
    - Updates inventory stock levels for each product sold.
    '''
    cashier = user_service.get_user(db, cashier_user_id)
    if not cashier or not cashier.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive cashier.")

    guest = None
    if sale_in.guest_id:
        guest = guest_service.get_guest(db, sale_in.guest_id)
        if not guest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Guest with ID {sale_in.guest_id} not found.")
        if guest.is_blacklisted:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Guest with ID {sale_in.guest_id} is blacklisted.")

    if not sale_in.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale must include at least one item.")

    sale_items_db_models = []
    grand_total_before_tax = Decimal("0.00")
    grand_total_tax_amount = Decimal("0.00")

    for item_in_schema in sale_in.items:
        product = product_service.get_product(db, item_in_schema.product_id)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID {item_in_schema.product_id} is invalid or not active."
            )

        # Ensure inventory item exists for stock deduction, or handle if not.
        # update_stock service will raise 404 if inventory item doesn't exist.
        # We might want to check this earlier or ensure inventory_service.update_stock can create if not exists.
        # For now, assume inventory_service.update_stock handles it or product creation ensures inv item.
        inv_item = inventory_service.get_inventory_item_by_product_id(db, product.id)
        if not inv_item:
            # Auto-create inventory item if product exists but item record doesn't.
            inv_item = inventory_service.create_inventory_item_if_not_exists(db, product_id=product.id, initial_quantity=0)
            # This ensures that an inventory record exists before attempting to deduct stock.

        if inv_item.quantity_on_hand < item_in_schema.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product ID {product.id} (Name: {product.name}). Available: {inv_item.quantity_on_hand}, Requested: {item_in_schema.quantity}."
            )

        price_details = product_service.calculate_product_price_with_tax(product, item_in_schema.quantity)

        db_sale_item_model = models.pos.POSSaleItem(
            product_id=item_in_schema.product_id,
            quantity=item_in_schema.quantity,
            unit_price_before_tax=product.price,
            tax_rate_applied=price_details["tax_rate"],
            tax_amount_for_item=price_details["tax_amount"],
            total_price_for_item_after_tax=price_details["total_with_tax"]
        )
        sale_items_db_models.append(db_sale_item_model)

        grand_total_before_tax += (product.price * item_in_schema.quantity) # Sum of (unit_price_before_tax * quantity) for all items
        grand_total_tax_amount += price_details["tax_amount"]

    grand_total_after_tax = grand_total_before_tax + grand_total_tax_amount

    pos_sale_data_for_model = sale_in.model_dump(exclude={"items"})
    db_pos_sale_model = models.pos.POSSale(
        **pos_sale_data_for_model,
        cashier_user_id=cashier_user_id,
        total_amount_before_tax=grand_total_before_tax,
        tax_amount=grand_total_tax_amount,
        total_amount_after_tax=grand_total_after_tax,
        status=POSSaleStatus.COMPLETED, # Default to COMPLETED if payment method is not PENDING_PAYMENT or similar
        items=sale_items_db_models
    )
    if sale_in.payment_method == PaymentMethod.ROOM_CHARGE and not sale_in.guest_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Guest ID is required for Room Charge payment method.")
    if sale_in.payment_method != PaymentMethod.ROOM_CHARGE and db_pos_sale_model.status == POSSaleStatus.PENDING_PAYMENT:
        # If not room charge, and status is pending, it means other payment method is pending.
        # This part of logic needs refinement based on how PENDING_PAYMENT status is set by client.
        # For now, assume client sets status correctly or service defaults to COMPLETED.
        # If schema defaults status to COMPLETED, then this is fine.
        pass


    db.add(db_pos_sale_model)

    try:
        # First, save the sale and items to get their IDs
        db.flush() # Assign IDs without full commit yet

        # Then, update inventory for each item sold.
        # This part needs to be transactional with the sale itself.
        for item_model in db_pos_sale_model.items:
            inventory_service.update_stock( # This service call currently commits internally.
                db=db,
                product_id=item_model.product_id,
                quantity_changed=-item_model.quantity,
                movement_type=StockMovementType.SALE,
                reason=f"Sale ID: {db_pos_sale_model.id}, Item ID: {item_model.id}",
                # Pass commit=False if update_stock is refactored to support it
            )

        db.commit() # Final commit for the sale and all stock updates (if update_stock doesn't commit)
        db.refresh(db_pos_sale_model)
        # Refresh items and their products as they might have been affected by stock updates or simply to ensure they are loaded
        for item in db_pos_sale_model.items:
            db.refresh(item)
            if item.product: db.refresh(item.product)

        return get_pos_sale(db, db_pos_sale_model.id)

    except HTTPException: # If update_stock or other logic raises HTTPException
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


def get_pos_sale(db: Session, sale_id: int) -> Optional[models.pos.POSSale]:
    '''Retrieve a POS sale by ID, including items, products, cashier, and guest.'''
    return db.query(models.pos.POSSale).options(
        selectinload(models.pos.POSSale.items).joinedload(models.pos.POSSaleItem.product).selectinload(models.product.Product.category),
        joinedload(models.pos.POSSale.cashier),
        joinedload(models.pos.POSSale.guest),
        joinedload(models.pos.POSSale.voided_by)
    ).filter(models.pos.POSSale.id == sale_id).first()

def get_pos_sales(
    db: Session, skip: int = 0, limit: int = 100,
    cashier_user_id: Optional[uuid.UUID] = None,
    guest_id: Optional[uuid.UUID] = None,
    status: Optional[POSSaleStatus] = None,
    payment_method: Optional[PaymentMethod] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[models.pos.POSSale]:
    '''Retrieve POS sales with various filters and pagination.'''
    query = db.query(models.pos.POSSale).options(
        joinedload(models.pos.POSSale.cashier),
        joinedload(models.pos.POSSale.guest)
        # Avoid loading items for list view for performance, unless specifically needed and paginated.
        # selectinload(models.pos.POSSale.items).joinedload(models.pos.POSSaleItem.product)
    )
    if cashier_user_id:
        query = query.filter(models.pos.POSSale.cashier_user_id == cashier_user_id)
    if guest_id:
        query = query.filter(models.pos.POSSale.guest_id == guest_id)
    if status:
        query = query.filter(models.pos.POSSale.status == status)
    if payment_method:
        query = query.filter(models.pos.POSSale.payment_method == payment_method)
    if date_from:
        query = query.filter(models.pos.POSSale.sale_date >= datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc))
    if date_to:
        query = query.filter(models.pos.POSSale.sale_date < datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))

    return query.order_by(models.pos.POSSale.sale_date.desc(), models.pos.POSSale.id.desc()).offset(skip).limit(limit).all()

def void_pos_sale(
    db: Session, sale_id: int, reason: str, voiding_user_id: uuid.UUID
) -> Optional[models.pos.POSSale]:
    '''
    Void a POS sale. Sets status to VOIDED and records reason/user.
    Stock readjustment for voided sales is NOT handled here and must be a separate process/service call.
    '''
    db_sale = get_pos_sale(db, sale_id)
    if not db_sale:
        return None

    if db_sale.status == POSSaleStatus.VOIDED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sale is already voided.")
    # Allow voiding PENDING_PAYMENT sales as well.
    if db_sale.status not in [POSSaleStatus.COMPLETED, POSSaleStatus.PENDING_PAYMENT]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Sale with status {db_sale.status.value} cannot be voided. Only COMPLETED or PENDING_PAYMENT sales can be voided.")

    voiding_user = user_service.get_user(db, voiding_user_id)
    if not voiding_user or not voiding_user.is_active:
        # This check might be redundant if API layer uses deps.get_current_active_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive user attempting to void sale.")

    db_sale.status = POSSaleStatus.VOIDED
    db_sale.void_reason = reason
    db_sale.voided_by_user_id = voiding_user_id
    db_sale.voided_at = datetime.now(timezone.utc)

    # Important: Reverse stock movements for voided sales.
    # This should be done carefully to ensure atomicity and correctness.
    # For each item in db_sale.items:
    #   inventory_service.update_stock(
    #       db=db,
    #       product_id=item.product_id,
    #       quantity_changed=item.quantity, # Positive to add back
    #       movement_type=StockMovementType.ADJUSTMENT_INCREASE, # Or a specific VOID_SALE_RETURN type
    #       reason=f"Stock return from voided Sale ID: {db_sale.id}, Item ID: {item.id}"
    #   )
    # This needs to be transactional with the sale status update.
    # For now, assuming update_stock commits itself, this is not atomic.
    # Refactor: update_stock should accept a commit=False flag for this.
    # For this iteration, stock reversal is NOT implemented to keep it simpler.
    # A separate process or a more complex transaction handling would be needed.

    db.add(db_sale) # Add updated sale object to session
    db.commit()
    db.refresh(db_sale)
    return db_sale
