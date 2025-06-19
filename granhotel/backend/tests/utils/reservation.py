from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional # Added Optional

from app import models, schemas
from app.services import reservation_service # Removed room_service, guest_service as they are not directly used here
from app.models.reservation import ReservationStatus
from tests.utils.guest import create_random_guest
from tests.utils.room import create_random_room # Assuming this exists and works

def create_random_reservation_data(
    db: Session,
    guest_id: Optional[int] = None,
    room_id: Optional[int] = None,
    days_in_future: int = 1,
    duration_days: int = 2,
    status: ReservationStatus = ReservationStatus.PENDING
) -> schemas.ReservationCreate:

    if guest_id is None:
        # guest_service is not imported, create_random_guest should handle DB session
        guest = create_random_guest(db, suffix="_res_util")
        guest_id = guest.id

    if room_id is None:
        # room_service is not imported, create_random_room should handle DB session
        room = create_random_room(db, room_number_suffix="_res_util")
        room_id = room.id

    check_in = date.today() + timedelta(days=days_in_future)
    check_out = check_in + timedelta(days=duration_days)

    return schemas.ReservationCreate(
        guest_id=guest_id,
        room_id=room_id,
        check_in_date=check_in,
        check_out_date=check_out,
        status=status,
        # total_price will be calculated by service
        notes="Test reservation notes"
    )

def create_random_reservation(
    db: Session,
    guest_id: Optional[int] = None,
    room_id: Optional[int] = None,
    days_in_future: int = 1,
    duration_days: int = 2,
    status: ReservationStatus = ReservationStatus.CONFIRMED # Default to confirmed for availability tests
) -> models.Reservation:
    reservation_data = create_random_reservation_data(
        db, guest_id, room_id, days_in_future, duration_days, status
    )
    # The create_reservation service function handles all logic including availability checks.
    # If a test requires a reservation to exist *despite* availability (e.g. to test conflict),
    # it might need to manipulate room status or use a more direct DB insertion,
    # but for most cases, using the service is preferred.
    return reservation_service.create_reservation(db=db, reservation_in=reservation_data)
