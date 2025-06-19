from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from decimal import Decimal
import uuid

from app.core.config import settings
from app.models.user import UserRole
from app.models.billing import FolioStatus, FolioTransactionType
from app.schemas.billing import FolioTransactionCreate, FolioStatusUpdate
from tests.utils.user import create_user_in_db
from tests.utils.guest import create_random_guest
from tests.utils.reservations import create_random_reservation
from tests.utils.billing import create_random_guest_folio, create_random_folio_transaction_data, add_sample_transactions_to_folio
from app.core.security import create_access_token # Use this directly for test tokens
from tests.utils.common import random_email, random_lower_string
from app import services # For direct service calls in test setup

API_V1_BILLING_URL = f"{settings.API_V1_STR}/billing"

# Local get_auth_headers
def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}

def test_read_folios_for_guest_api(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_rfg"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    guest = create_random_guest(db, suffix="_rfg_g")

    # Create folios using the utility which calls the service
    create_random_guest_folio(db, guest_id=guest.id) # creator_user_id not needed by util's service call
    create_random_guest_folio(db, guest_id=guest.id)

    response = client.get(f"{API_V1_BILLING_URL}/folios/guest/{guest.id}", headers=rec_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2
    assert all(f["guest"]["id"] == str(guest.id) for f in content) # guest should be nested

def test_get_or_create_folio_for_guest_api_creates_new(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_goc_new"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    guest = create_random_guest(db, suffix="_goc_new_g")
    # Create a reservation to link (creator_user_id not needed by create_random_reservation)
    reservation = create_random_reservation(db, guest_id=guest.id)

    payload = {"reservation_id": reservation.id}
    response = client.post(f"{API_V1_BILLING_URL}/folios/guest/{guest.id}/get-or-create", json=payload, headers=rec_headers)
    # The endpoint is POST. If it creates, 201 is more RESTful. If it finds, 200.
    # For a "get_or_create" POST, usually 200 if found, 201 if created. Let's assume API handles this.
    # The service returns the object. The API endpoint does not change status code based on create/get.
    # So, POST that returns an object usually is 200 or 201. For now, let's stick to 200 as per prior test.
    # However, the endpoint definition for create_new_X_api generally uses 201.
    # Since this can create, 200 is fine if it implies "request successful, here is the resource".
    assert response.status_code == 200, response.text # Or check for 200/201

    content = response.json()
    assert content["guest_id"] == str(guest.id)
    assert content["reservation_id"] == reservation.id
    assert content["status"] == FolioStatus.OPEN.value

def test_get_or_create_folio_for_guest_api_returns_existing(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_goc_exist"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    existing_folio = create_random_guest_folio(db, guest_id=create_random_guest(db, suffix="_goc_exist_g2").id) # Ensure guest exists

    payload = {"reservation_id": existing_folio.reservation_id}
    response = client.post(f"{API_V1_BILLING_URL}/folios/guest/{existing_folio.guest_id}/get-or-create", json=payload, headers=rec_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == existing_folio.id
    assert content["status"] == FolioStatus.OPEN.value


def test_read_folio_details_api(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_rfd"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    folio = create_random_guest_folio(db)
    add_sample_transactions_to_folio(db, folio_id=folio.id, created_by_user_id=receptionist.id, num_charges=1, num_payments=1)

    # Re-fetch folio from DB to get accurate totals after transactions for assertion
    db.refresh(folio)
    folio_from_db = services.billing_service.get_folio_details(db, folio.id)


    response = client.get(f"{API_V1_BILLING_URL}/folios/{folio.id}", headers=rec_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == folio.id
    assert len(content["transactions"]) == 2
    # Compare balance after converting JSON string to Decimal
    assert Decimal(content["balance"]).quantize(Decimal("0.01")) == folio_from_db.balance.quantize(Decimal("0.01"))

def test_add_transaction_to_folio_api(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_addtrans"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    folio = create_random_guest_folio(db)

    transaction_payload = {
        "description": "API Test Charge - Minibar",
        "charge_amount": "25.50",
        "payment_amount": "0.00",
        "transaction_type": FolioTransactionType.POS_CHARGE.value
    }
    response = client.post(f"{API_V1_BILLING_URL}/folios/{folio.id}/transactions", json=transaction_payload, headers=rec_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert Decimal(content["total_charges"]).quantize(Decimal("0.01")) == Decimal("25.50")
    assert len(content["transactions"]) == 1
    assert content["transactions"][0]["description"] == "API Test Charge - Minibar"


def test_update_folio_status_api_settle(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_updfolio_settle"))
    mgr_headers = get_auth_headers(manager_user.id, manager_user.role)

    folio = create_random_guest_folio(db)
    charge_data = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.ROOM_CHARGE, amount=Decimal("100.00"))
    services.billing_service.add_transaction_to_folio(db, folio.id, charge_data, manager_user.id)
    payment_data = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.PAYMENT, amount=Decimal("100.00"))
    services.billing_service.add_transaction_to_folio(db, folio.id, payment_data, manager_user.id)

    reloaded_folio = services.billing_service.get_folio_details(db, folio.id)
    assert reloaded_folio.balance == Decimal("0.00")

    status_update_payload = {"status": FolioStatus.SETTLED.value}
    response = client.patch(f"{API_V1_BILLING_URL}/folios/{folio.id}/status", json=status_update_payload, headers=mgr_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["status"] == FolioStatus.SETTLED.value
    assert content["closed_at"] is not None

def test_update_folio_status_api_settle_with_balance_fail(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_updfolio_bal_fail"))
    mgr_headers = get_auth_headers(manager_user.id, manager_user.role)
    folio = create_random_guest_folio(db)
    charge_data = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.ROOM_CHARGE, amount=Decimal("50.00"))
    services.billing_service.add_transaction_to_folio(db, folio.id, charge_data, manager_user.id)

    status_update_payload = {"status": FolioStatus.SETTLED.value}
    response = client.patch(f"{API_V1_BILLING_URL}/folios/{folio.id}/status", json=status_update_payload, headers=mgr_headers)
    assert response.status_code == 400, response.text
    assert "cannot set to settled until balance is zero" in response.json()["detail"].lower()
