from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal # For comparing price

from app.core.config import settings
from app.schemas.reservation import ReservationCreate, ReservationUpdate # Ensure ReservationStatus is available for test data
from app.models.reservation import ReservationStatus # Direct import for test data clarity
from tests.utils.guest import create_random_guest
from tests.utils.room import create_random_room
from tests.utils.reservation import create_random_reservation_data, create_random_reservation # For API payloads and setup

API_V1_RESERVATIONS_URL = f"{settings.API_V1_STR}/reservations"

def test_create_reservation_api(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_api_cres")
    room = create_random_room(db, room_number_suffix="_api_cres")
    room.price = 120.50 # Set a known price for the room for predictable total_price
    db.add(room)
    db.commit()
    db.refresh(room)

    payload_schema = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id, days_in_future=5, duration_days=2)

    json_payload = payload_schema.model_dump()
    json_payload["check_in_date"] = payload_schema.check_in_date.isoformat()
    json_payload["check_out_date"] = payload_schema.check_out_date.isoformat()
    json_payload["status"] = payload_schema.status.value

    response = client.post(f"{API_V1_RESERVATIONS_URL}/", json=json_payload)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["guest_id"] == guest.id
    assert content["room_id"] == room.id
    assert "id" in content
    # Expected price: 120.50 * 2 nights = 241.00
    assert Decimal(content["total_price"]) == Decimal("241.00")


def test_read_reservations_api(client: TestClient, db: Session) -> None:
    # Create a couple of reservations
    res1 = create_random_reservation(db, days_in_future=10)
    res2 = create_random_reservation(db, days_in_future=12)

    response = client.get(f"{API_V1_RESERVATIONS_URL}/")
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2
    res_ids = [r['id'] for r in content]
    assert res1.id in res_ids
    assert res2.id in res_ids


def test_read_single_reservation_api(client: TestClient, db: Session) -> None:
    reservation = create_random_reservation(db, days_in_future=15)
    response = client.get(f"{API_V1_RESERVATIONS_URL}/{reservation.id}")
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == reservation.id
    assert content["guest"]["id"] == reservation.guest_id # Check nested guest
    assert content["room"]["id"] == reservation.room_id   # Check nested room

def test_update_reservation_api(client: TestClient, db: Session) -> None:
    reservation = create_random_reservation(db, days_in_future=20, status=ReservationStatus.PENDING)
    new_notes = "Updated notes via API"
    # Ensure dates are in ISO format for JSON payload
    new_check_in_date = (date.today() + timedelta(days=21)).isoformat()
    new_check_out_date = (date.today() + timedelta(days=23)).isoformat()

    update_data = {
        "notes": new_notes,
        "status": ReservationStatus.CONFIRMED.value,
        "check_in_date": new_check_in_date,
        "check_out_date": new_check_out_date
    }

    response = client.put(f"{API_V1_RESERVATIONS_URL}/{reservation.id}", json=update_data)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["notes"] == new_notes
    assert content["status"] == ReservationStatus.CONFIRMED.value
    assert content["check_in_date"] == new_check_in_date
    assert content["id"] == reservation.id

def test_update_reservation_status_api(client: TestClient, db: Session) -> None:
    reservation = create_random_reservation(db, days_in_future=25, status=ReservationStatus.PENDING)

    response = client.patch(f"{API_V1_RESERVATIONS_URL}/{reservation.id}/status?new_status={ReservationStatus.CONFIRMED.value}")
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["status"] == ReservationStatus.CONFIRMED.value

def test_cancel_reservation_api(client: TestClient, db: Session) -> None:
    reservation = create_random_reservation(db, days_in_future=30, status=ReservationStatus.CONFIRMED)

    response = client.post(f"{API_V1_RESERVATIONS_URL}/{reservation.id}/cancel")
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["status"] == ReservationStatus.CANCELLED.value

def test_create_reservation_api_room_not_available(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_api_unavailable")
    room = create_random_room(db, room_number_suffix="_api_unavailable")

    # Create an initial reservation that makes the room unavailable
    create_random_reservation(db, guest_id=guest.id, room_id=room.id, days_in_future=35, duration_days=3, status=ReservationStatus.CONFIRMED)

    # Attempt to create another reservation for the same overlapping dates
    payload_conflict = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id, days_in_future=35, duration_days=3)
    json_payload_conflict = payload_conflict.model_dump()
    json_payload_conflict["check_in_date"] = payload_conflict.check_in_date.isoformat()
    json_payload_conflict["check_out_date"] = payload_conflict.check_out_date.isoformat()
    json_payload_conflict["status"] = payload_conflict.status.value

    response = client.post(f"{API_V1_RESERVATIONS_URL}/", json=json_payload_conflict)
    assert response.status_code == 409, response.text # Conflict
    assert "not available" in response.json()["detail"].lower()

def test_create_reservation_api_guest_blacklisted(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_api_blisted")
    guest.is_blacklisted = True # Blacklist the guest
    db.add(guest)
    db.commit()
    db.refresh(guest)

    room = create_random_room(db, room_number_suffix="_api_blisted")

    payload = create_random_reservation_data(db, guest_id=guest.id, room_id=room.id, days_in_future=40)
    json_payload = payload.model_dump()
    json_payload["check_in_date"] = payload.check_in_date.isoformat()
    json_payload["check_out_date"] = payload.check_out_date.isoformat()
    json_payload["status"] = payload.status.value

    response = client.post(f"{API_V1_RESERVATIONS_URL}/", json=json_payload)
    assert response.status_code == 403, response.text # Forbidden
    assert "blacklisted" in response.json()["detail"].lower()

def test_read_single_reservation_api_not_found(client: TestClient) -> None:
    response = client.get(f"{API_V1_RESERVATIONS_URL}/999999")
    assert response.status_code == 404

def test_update_reservation_api_not_found(client: TestClient) -> None:
    update_data = {"notes": "Trying to update non-existent reservation"}
    response = client.put(f"{API_V1_RESERVATIONS_URL}/999999", json=update_data)
    assert response.status_code == 404

def test_update_reservation_status_api_not_found(client: TestClient) -> None:
    response = client.patch(f"{API_V1_RESERVATIONS_URL}/999999/status?new_status={ReservationStatus.CONFIRMED.value}")
    assert response.status_code == 404

def test_cancel_reservation_api_not_found(client: TestClient) -> None:
    response = client.post(f"{API_V1_RESERVATIONS_URL}/999999/cancel")
    assert response.status_code == 404
