from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import date, timedelta, datetime
from decimal import Decimal

from app import models
from app import schemas
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from fastapi import HTTPException, status

# Helper function (can be in a utils file later)
def is_room_available(db: Session, room_id: int, check_in_date: date, check_out_date: date, reservation_id_to_exclude: Optional[int] = None) -> bool:
    '''
    Check if a room is available for the given date range, excluding a specific reservation if provided (for updates).
    A room is unavailable if it has any confirmed or checked-in reservation that overlaps with the desired period.
    '''
    overlapping_reservations_query = db.query(models.Reservation).filter(
        models.Reservation.room_id == room_id,
        models.Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]),
        models.Reservation.check_in_date < check_out_date, # Existing reservation starts before new one ends
        models.Reservation.check_out_date > check_in_date    # Existing reservation ends after new one starts
    )
    if reservation_id_to_exclude:
        overlapping_reservations_query = overlapping_reservations_query.filter(models.Reservation.id != reservation_id_to_exclude)

    return overlapping_reservations_query.first() is None


def calculate_reservation_price(db: Session, room_id: int, check_in_date: date, check_out_date: date) -> Decimal:
    '''
    Calculate the total price for a reservation.
    For now: room.price * number_of_nights.
    IGV (18%) should be incorporated later.
    '''
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found for price calculation.")

    if check_out_date <= check_in_date:
        # This check is also in Pydantic schema, but good to have in service layer for direct calls
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Check-out date must be after check-in date.")

    number_of_nights = (check_out_date - check_in_date).days
    if number_of_nights <= 0: # Should be caught by above, but defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Number of nights must be positive.")

    total_price = Decimal(room.price) * Decimal(number_of_nights)
    # Placeholder for IGV:
    # igv_rate = Decimal("0.18")
    # total_price_with_igv = total_price * (1 + igv_rate)
    return total_price


def create_reservation(db: Session, reservation_in: schemas.ReservationCreate) -> models.Reservation:
    '''
    Create a new reservation.
    - Checks for guest and room existence.
    - Checks for room availability.
    - Calculates total price.
    '''
    guest = db.query(models.Guest).filter(models.Guest.id == reservation_in.guest_id).first()
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Guest with ID {reservation_in.guest_id} not found.")
    if guest.is_blacklisted:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Guest with ID {reservation_in.guest_id} is blacklisted.")

    room = db.query(models.Room).filter(models.Room.id == reservation_in.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with ID {reservation_in.room_id} not found.")

    if not is_room_available(db, room_id=reservation_in.room_id, check_in_date=reservation_in.check_in_date, check_out_date=reservation_in.check_out_date):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Room {reservation_in.room_id} is not available for the selected dates.")

    calculated_price = calculate_reservation_price(db, room_id=reservation_in.room_id, check_in_date=reservation_in.check_in_date, check_out_date=reservation_in.check_out_date)

    db_reservation_data = reservation_in.model_dump()
    db_reservation_data["total_price"] = calculated_price

    db_reservation = models.Reservation(**db_reservation_data)
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def get_reservation(db: Session, reservation_id: int) -> Optional[models.Reservation]:
    '''Retrieve a reservation by ID, including guest and room details.'''
    return db.query(models.Reservation).options(
        joinedload(models.Reservation.guest),
        joinedload(models.Reservation.room)
    ).filter(models.Reservation.id == reservation_id).first()

def get_reservations(
    db: Session, skip: int = 0, limit: int = 100,
    guest_id: Optional[int] = None,
    room_id: Optional[int] = None,
    status: Optional[ReservationStatus] = None,
    date_from: Optional[date] = None, # Consider this as check_in_date >= date_from
    date_to: Optional[date] = None    # Consider this as check_out_date <= date_to
                                      # Or more practically, reservations active *within* this range
) -> List[models.Reservation]:
    '''Retrieve list of reservations with optional filters, including guest and room details.'''
    query = db.query(models.Reservation).options(
        joinedload(models.Reservation.guest),
        joinedload(models.Reservation.room)
    )
    if guest_id:
        query = query.filter(models.Reservation.guest_id == guest_id)
    if room_id:
        query = query.filter(models.Reservation.room_id == room_id)
    if status:
        query = query.filter(models.Reservation.status == status)

    # Date filtering: find reservations that *overlap* with the given [date_from, date_to] period.
    # A reservation overlaps if its start is before date_to AND its end is after date_from.
    if date_from:
        query = query.filter(models.Reservation.check_out_date > date_from) # Ends after the filter period starts
    if date_to:
        query = query.filter(models.Reservation.check_in_date < date_to)   # Starts before the filter period ends

    return query.order_by(models.Reservation.check_in_date.desc()).offset(skip).limit(limit).all()


def get_reservations_for_room_date_range(db: Session, room_id: int, start_date: date, end_date: date) -> List[models.Reservation]:
    '''Get reservations for a specific room that overlap with a given date range.'''
    return db.query(models.Reservation).filter(
        models.Reservation.room_id == room_id,
        # Consider which statuses make a room "occupied" or relevant for this check
        models.Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN, ReservationStatus.PENDING]),
        models.Reservation.check_in_date < end_date,
        models.Reservation.check_out_date > start_date
    ).all()


def update_reservation_status(db: Session, reservation_id: int, new_status: ReservationStatus) -> Optional[models.Reservation]:
    '''Update the status of a reservation.'''
    db_reservation = get_reservation(db, reservation_id) # This already loads guest/room
    if not db_reservation:
        # Raise HTTPException here or let the API layer handle it based on None return?
        # For consistency with create_reservation, raising here might be better.
        # However, typical update patterns often return None if not found, and API layer raises 404.
        # Let's stick to returning None for now for simple status updates.
        return None

    db_reservation.status = new_status
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def update_reservation_details(db: Session, reservation_id: int, reservation_in: schemas.ReservationUpdate) -> Optional[models.Reservation]:
    '''Update details of a reservation (e.g., dates, notes). Price may need recalculation.'''
    db_reservation = get_reservation(db, reservation_id) # This already loads guest/room
    if not db_reservation:
        return None # API layer should handle 404

    update_data = reservation_in.model_dump(exclude_unset=True)

    new_check_in = update_data.get("check_in_date", db_reservation.check_in_date)
    new_check_out = update_data.get("check_out_date", db_reservation.check_out_date)
    new_room_id = update_data.get("room_id", db_reservation.room_id)

    recalculate_price = False
    if "room_id" in update_data and update_data["room_id"] != db_reservation.room_id:
        recalculate_price = True
    if "check_in_date" in update_data and update_data["check_in_date"] != db_reservation.check_in_date:
        recalculate_price = True
    if "check_out_date" in update_data and update_data["check_out_date"] != db_reservation.check_out_date:
        recalculate_price = True

    # Check availability if room or dates are changing for reservations that block availability
    if db_reservation.status in [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN] and \
       ("room_id" in update_data or "check_in_date" in update_data or "check_out_date" in update_data):
        if not is_room_available(db, room_id=new_room_id, check_in_date=new_check_in, check_out_date=new_check_out, reservation_id_to_exclude=reservation_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Room {new_room_id} is not available for the new dates/room.")

    for field, value in update_data.items():
        setattr(db_reservation, field, value)

    if recalculate_price:
        db_reservation.total_price = calculate_reservation_price(db, room_id=new_room_id, check_in_date=new_check_in, check_out_date=new_check_out)

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


def cancel_reservation(db: Session, reservation_id: int) -> Optional[models.Reservation]:
    '''Cancel a reservation by setting its status to CANCELLED.'''
    # Add any cancellation specific logic here, e.g., logging, notifications, refund policies
    # For now, it's just a status update.
    return update_reservation_status(db, reservation_id, ReservationStatus.CANCELLED)
