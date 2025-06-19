from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal
import uuid

from app.core.config import settings
from app.models.user import UserRole
from app.models.pos import POSSaleStatus, PaymentMethod
from app.models.inventory import StockMovementType
from app import schemas, services # Added services for inventory_service call
from tests.utils.user import create_user_in_db
from tests.utils.product import create_random_product
from tests.utils.guest import create_random_guest
from tests.utils.inventory import ensure_inventory_item_exists
from tests.utils.pos import create_pos_sale_items_data_for_api, create_random_pos_sale
from app.core.security import create_access_token # Use this directly for test tokens
from tests.utils.common import random_email, random_lower_string


API_V1_POS_SALES_URL = f"{settings.API_V1_STR}/pos/sales"

# Local get_auth_headers
def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}


def test_create_pos_sale_api_as_receptionist(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_cpossale"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    guest = create_random_guest(db, suffix="_cpossale_g")

    items_payload = create_pos_sale_items_data_for_api(db, num_items=2)

    sale_data = {
        "guest_id": str(guest.id),
        "payment_method": PaymentMethod.CASH.value,
        "items": items_payload,
        "notes": "API Test Sale - Cash"
    }

    response = client.post(f"{API_V1_POS_SALES_URL}/", json=sale_data, headers=rec_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["cashier_user_id"] == str(receptionist.id)
    assert content["guest_id"] == str(guest.id)
    assert len(content["items"]) == 2
    assert content["status"] == POSSaleStatus.COMPLETED.value
    assert Decimal(content["total_amount_after_tax"]) > Decimal("0.00")

    prod_id_item0 = items_payload[0]["product_id"]
    qty_sold_item0 = items_payload[0]["quantity"]
    # inv_item0 = services.inventory_service.get_inventory_item_by_product_id(db, prod_id_item0) # Already checked by service
    movements = services.inventory_service.get_stock_movement_history(db, prod_id_item0, movement_type=StockMovementType.SALE)
    assert any(m.quantity_changed == -qty_sold_item0 and m.reason and f"Sale ID: {content['id']}" in m.reason for m in movements)


def test_create_pos_sale_api_room_charge_needs_guest(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_cposrc"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    items_payload = create_pos_sale_items_data_for_api(db, num_items=1)
    sale_data_no_guest = {
        "payment_method": PaymentMethod.ROOM_CHARGE.value,
        "items": items_payload,
        "guest_id": None
    }
    response = client.post(f"{API_V1_POS_SALES_URL}/", json=sale_data_no_guest, headers=rec_headers)
    assert response.status_code == 400, response.text
    assert "guest id is required for room charge" in response.json()["detail"].lower()


def test_read_all_pos_sales_api_as_manager(client: TestClient, db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_rpossales"))
    mgr_headers = get_auth_headers(manager.id, manager.role)
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cash_rpossales"))

    create_random_pos_sale(db, cashier_user_id=cashier.id)
    create_random_pos_sale(db, cashier_user_id=manager.id)

    response = client.get(f"{API_V1_POS_SALES_URL}/", headers=mgr_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2

def test_read_single_pos_sale_api_own_sale_as_receptionist(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_rsinglepos"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    sale = create_random_pos_sale(db, cashier_user_id=receptionist.id)

    response = client.get(f"{API_V1_POS_SALES_URL}/{sale.id}", headers=rec_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == sale.id
    assert content["cashier_user_id"] == str(receptionist.id)

def test_read_single_pos_sale_api_other_sale_as_receptionist_fail(client: TestClient, db: Session):
    cashier1 = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec1_rsingleposf"))
    cashier2 = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec2_rsingleposf"))
    c1_headers = get_auth_headers(cashier1.id, cashier1.role)

    sale_by_cashier2 = create_random_pos_sale(db, cashier_user_id=cashier2.id)

    response = client.get(f"{API_V1_POS_SALES_URL}/{sale_by_cashier2.id}", headers=c1_headers)
    assert response.status_code == 403, response.text

def test_void_pos_sale_api_as_manager(client: TestClient, db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_vpossale"))
    mgr_headers = get_auth_headers(manager.id, manager.role)
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cash_vpossale"))

    sale_to_void = create_random_pos_sale(db, cashier_user_id=cashier.id) # Default status is COMPLETED

    void_data = {"void_reason": "API Test Void"}
    response = client.post(f"{API_V1_POS_SALES_URL}/{sale_to_void.id}/void", json=void_data, headers=mgr_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["status"] == POSSaleStatus.VOIDED.value
    assert content["void_reason"] == "API Test Void"
    assert content["voided_by_user_id"] == str(manager.id)

def test_void_pos_sale_api_as_receptionist_fail(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_vpossalef"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    sale_to_void = create_random_pos_sale(db, cashier_user_id=receptionist.id)

    void_data = {"void_reason": "Attempt by receptionist"}
    response = client.post(f"{API_V1_POS_SALES_URL}/{sale_to_void.id}/void", json=void_data, headers=rec_headers)
    assert response.status_code == 403, response.text

def test_create_pos_sale_api_insufficient_stock_fail(client: TestClient, db: Session):
    receptionist = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_cpos_is"))
    rec_headers = get_auth_headers(receptionist.id, receptionist.role)
    product = create_random_product(db, name_suffix="_cpos_is_p")
    ensure_inventory_item_exists(db, product.id, initial_quantity=1) # Only 1 in stock

    items_payload = [{"product_id": product.id, "quantity": 2}] # Try to sell 2
    sale_data = {"payment_method": PaymentMethod.CASH.value, "items": items_payload}

    response = client.post(f"{API_V1_POS_SALES_URL}/", json=sale_data, headers=rec_headers)
    assert response.status_code == 400, response.text
    assert "insufficient stock" in response.json()["detail"].lower()

def test_void_already_voided_sale_api_fail(client: TestClient, db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_vpos_av"))
    mgr_headers = get_auth_headers(manager.id, manager.role)
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cash_vpos_av"))

    sale_to_void = create_random_pos_sale(db, cashier_user_id=cashier.id)
    # First void
    client.post(f"{API_V1_POS_SALES_URL}/{sale_to_void.id}/void", json={"void_reason": "Initial void"}, headers=mgr_headers)

    # Attempt to void again
    void_data = {"void_reason": "Second void attempt"}
    response = client.post(f"{API_V1_POS_SALES_URL}/{sale_to_void.id}/void", json=void_data, headers=mgr_headers)
    assert response.status_code == 400, response.text
    assert "already voided" in response.json()["detail"].lower()
