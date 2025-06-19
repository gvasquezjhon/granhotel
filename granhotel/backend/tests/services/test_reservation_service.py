import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date, timedelta
from decimal import Decimal

from app import schemas, models
from app.services import reservation_service, guest_service, room_service # guest_service needed for blacklisting
from app.models.reservation import ReservationStatus
from app.models.room import Room # For direct manipulation if needed
from tests.utils.guest import create_random_guest
from tests.utils.room import create_random_room
from tests.utils.reservation import create_random_reservation_data, create_random_reservation

def test_calculate_price(db: Session):
    room = create_random_room(db, room_number_suffix="_pricecalc")
    # Ensure room.price is a float for Decimal conversion if it's not already
    room_price_decimal = Decimal(str(room.price)) # Convert from float to Decimal via string
    room.price = float(room_price_decimal) # Store as float if that's model type
    db.add(room) # Add room to session if create_random_room doesn't
    db.commit()
    db.refresh(room) # Ensure price is refreshed if changed

    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=3) # 3 nights

    # Use the refreshed room price for expectation
    expected_price = Decimal(str(room.price)) * Decimal("3")

    price = reservation_service.calculate_reservation_price(db, room.id, check_in, check_out)
    assert price == expected_price

def test_is_room_available(db: Session):
    room = create_random_room(db, room_number_suffix="_avail")
    guest = create_random_guest(db, suffix="_avail")

    check_in1 = date.today() + timedelta(days=10)
    check_out1 = check_in1 + timedelta(days=2)

    # Initially available
    assert reservation_service.is_room_available(db, room.id, check_in1, check_out1)

    # Create a confirmed reservation
    res_data1 = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id, days_in_future=10, duration_days=2, status=ReservationStatus.CONFIRMED)
    # We use create_reservation_data and then construct the model directly for this specific test
    # to bypass the availability check in create_reservation service for setting up the scenario.
    # However, it's better to use create_reservation if it's designed to allow creating PENDING first.
    # Let's assume create_random_reservation already sets status to CONFIRMED as per its default.
    # For this test, we want to ensure that an *existing* confirmed reservation makes the room unavailable.
    # So, we need to call the service to make a reservation.

    # To avoid issues with the service's own availability check during setup,
    # let's ensure the room is available for this setup reservation.
    reservation_service.create_reservation(db, reservation_in=res_data1)

    # Now should be unavailable for same dates
    assert not reservation_service.is_room_available(db, room.id, check_in1, check_out1)
    # Unavailable for overlapping dates
    assert not reservation_service.is_room_available(db, room.id, check_in1 - timedelta(days=1), check_out1 - timedelta(days=1)) # Overlaps start
    assert not reservation_service.is_room_available(db, room.id, check_in1 + timedelta(days=1), check_out1 + timedelta(days=1)) # Overlaps end
    # Available for non-overlapping dates
    assert reservation_service.is_room_available(db, room.id, check_out1 + timedelta(days=1), check_out1 + timedelta(days=3))


def test_create_reservation_service(db: Session):
    guest = create_random_guest(db, suffix="_c_res")
    room = create_random_room(db, room_number_suffix="_c_res")
    # Ensure room.price is set for calculation
    room_price = Decimal(str(room.price)) # Assuming price is float in model, convert for precise calc

    reservation_in_data = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id, days_in_future=5, duration_days=2)
    reservation = reservation_service.create_reservation(db=db, reservation_in=reservation_in_data)

    assert reservation is not None
    assert reservation.guest_id == guest.id
    assert reservation.room_id == room.id
    expected_total_price = room_price * Decimal("2") # duration_days = 2
    assert reservation.total_price == expected_total_price
    assert reservation.status == ReservationStatus.PENDING # Default from schema if not overridden by create_random_reservation_data

def test_create_reservation_room_not_available(db: Session):
    guest = create_random_guest(db, suffix="_c_res_na")
    room = create_random_room(db, room_number_suffix="_c_res_na")

    # Book the room first
    create_random_reservation(db, guest_id=guest.id, room_id=room.id, days_in_future=20, duration_days=3, status=ReservationStatus.CONFIRMED)

    # Try to book overlapping period
    reservation_in_data_conflict = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id, days_in_future=20, duration_days=3)
    with pytest.raises(HTTPException) as excinfo:
        reservation_service.create_reservation(db=db, reservation_in=reservation_in_data_conflict)
    assert excinfo.value.status_code == 409 # Conflict

def test_create_reservation_guest_blacklisted(db: Session):
    guest = create_random_guest(db, suffix="_c_res_bl")
    # guest_service.blacklist_guest(db, guest.id, blacklist_status=True) # Use service to blacklist
    guest.is_blacklisted = True # Or direct manipulation for test setup simplicity
    db.add(guest)
    db.commit()
    db.refresh(guest)

    room = create_random_room(db, room_number_suffix="_c_res_bl")
    reservation_in_data = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id)
    with pytest.raises(HTTPException) as excinfo:
        reservation_service.create_reservation(db=db, reservation_in=reservation_in_data)
    assert excinfo.value.status_code == 403 # Forbidden

def test_get_reservation_service(db: Session):
    created_res = create_random_reservation(db, days_in_future=30, duration_days=2)
    fetched_res = reservation_service.get_reservation(db, reservation_id=created_res.id)
    assert fetched_res is not None
    assert fetched_res.id == created_res.id
    assert fetched_res.guest is not None # Check joinedload
    assert fetched_res.room is not None  # Check joinedload

def test_update_reservation_status_service(db: Session):
    reservation = create_random_reservation(db, status=ReservationStatus.PENDING, days_in_future=40)
    updated_res = reservation_service.update_reservation_status(db, reservation.id, ReservationStatus.CONFIRMED)
    assert updated_res is not None
    assert updated_res.status == ReservationStatus.CONFIRMED

def test_cancel_reservation_service(db: Session):
    reservation = create_random_reservation(db, status=ReservationStatus.CONFIRMED, days_in_future=50)
    cancelled_res = reservation_service.cancel_reservation(db, reservation.id)
    assert cancelled_res is not None
    assert cancelled_res.status == ReservationStatus.CANCELLED

def test_update_reservation_details_service(db: Session):
    reservation = create_random_reservation(db, days_in_future=60, duration_days=2, status=ReservationStatus.CONFIRMED)
    room2 = create_random_room(db, room_number_suffix="_upd_details") # new room

    new_check_in = reservation.check_in_date + timedelta(days=1)
    new_check_out = new_check_in + timedelta(days=3) # 3 nights now

    update_payload = schemas.ReservationUpdate(
        room_id=room2.id,
        check_in_date=new_check_in,
        check_out_date=new_check_out,
        notes="Updated details test"
    )
    updated_res = reservation_service.update_reservation_details(db, reservation.id, update_payload)
    assert updated_res is not None
    assert updated_res.room_id == room2.id
    assert updated_res.check_in_date == new_check_in
    assert updated_res.notes == "Updated details test"

    # Price should be recalculated
    expected_price = reservation_service.calculate_reservation_price(db, room2.id, new_check_in, new_check_out)
    assert updated_res.total_price == expected_price

def test_update_reservation_details_room_becomes_unavailable(db: Session):
    guest1 = create_random_guest(db, suffix="_upd_unavail1")
    guest2 = create_random_guest(db, suffix="_upd_unavail2")
    room_target = create_random_room(db, room_number_suffix="_upd_unavail_target")
    room_other = create_random_room(db, room_number_suffix="_upd_unavail_other")

    # Reservation 1 (original reservation to be updated)
    res1_check_in = date.today() + timedelta(days=70)
    res1_check_out = res1_check_in + timedelta(days=2)
    reservation1 = create_random_reservation(db, guest_id=guest1.id, room_id=room_other.id, days_in_future=70, duration_days=2, status=ReservationStatus.CONFIRMED)

    # Reservation 2 (blocks the target room and dates for Reservation 1's update)
    create_random_reservation(db, guest_id=guest2.id, room_id=room_target.id, days_in_future=70, duration_days=2, status=ReservationStatus.CONFIRMED)

    # Try to update reservation1 to move into room_target's dates (which are now booked by reservation2)
    update_payload_conflict = schemas.ReservationUpdate(
        room_id=room_target.id, # Target room
        check_in_date=res1_check_in, # Same dates as reservation2
        check_out_date=res1_check_out
    )

    with pytest.raises(HTTPException) as excinfo:
        reservation_service.update_reservation_details(db, reservation1.id, update_payload_conflict)
    assert excinfo.value.status_code == 409 # Conflict
    assert "not available for the new dates/room" in excinfo.value.detail
