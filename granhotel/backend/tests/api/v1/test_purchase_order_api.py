from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal
import uuid # For user_id if needed by get_auth_headers directly

from app.core.config import settings
from app.models.user import UserRole
from app.models.inventory import PurchaseOrderStatus, StockMovementType
from app.schemas.inventory import PurchaseOrderCreate, PurchaseOrderItemCreate, PurchaseOrderStatusUpdate, PurchaseOrderItemReceive
from tests.utils.user import create_user_in_db
from tests.utils.product import create_random_product
from tests.utils.inventory import create_random_supplier, create_random_purchase_order, ensure_inventory_item_exists, create_random_po_items_data
from app.core.security import create_access_token # Use this directly for test tokens
from app.services import inventory_service # For checking stock after PO receipt
from tests.utils.common import random_email, random_lower_string


API_V1_PO_URL = f"{settings.API_V1_STR}/purchase-orders"

# Local get_auth_headers, similar to the one in other API test files
def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}


def test_create_purchase_order_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_cpo"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    supplier = create_random_supplier(db, suffix="_po_api")

    product1 = create_random_product(db, name_suffix="_po_p1")
    product2 = create_random_product(db, name_suffix="_po_p2")

    po_items_data = [
        {"product_id": product1.id, "quantity_ordered": 10, "unit_price_paid": "15.50"},
        {"product_id": product2.id, "quantity_ordered": 5, "unit_price_paid": "20.00"}
    ]
    po_create_data = {
        "supplier_id": supplier.id,
        "items": po_items_data,
        "order_date": date.today().isoformat(),
        "notes": "API Test PO"
    }

    response = client.post(f"{API_V1_PO_URL}/", json=po_create_data, headers=manager_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["supplier_id"] == supplier.id
    assert len(content["items"]) == 2
    assert content["items"][0]["product_id"] == product1.id
    assert content["items"][0]["quantity_ordered"] == 10
    assert content["status"] == PurchaseOrderStatus.PENDING.value

def test_create_purchase_order_api_no_items_fail(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_cponi"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    supplier = create_random_supplier(db, suffix="_po_api_ni")
    po_create_no_items = {"supplier_id": supplier.id, "items": []} # Empty items list
    response = client.post(f"{API_V1_PO_URL}/", json=po_create_no_items, headers=manager_headers)
    assert response.status_code == 400, response.text
    assert "purchase order must contain at least one item" in response.json()["detail"].lower()


def test_read_all_purchase_orders_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_rpo"))
    user_headers = get_auth_headers(user.id, user.role)
    create_random_purchase_order(db, num_items=1, po_notes_suffix="_api_rpo1")
    create_random_purchase_order(db, num_items=1, po_notes_suffix="_api_rpo2")

    response = client.get(f"{API_V1_PO_URL}/", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2

def test_read_single_purchase_order_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_rsingle_po"))
    user_headers = get_auth_headers(user.id, user.role)
    po = create_random_purchase_order(db, num_items=1, po_notes_suffix="_api_single_po")

    response = client.get(f"{API_V1_PO_URL}/{po.id}", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == po.id
    assert content["supplier"]["id"] == po.supplier_id
    assert len(content["items"]) == 1
    assert content["items"][0]["product"]["id"] == po.items[0].product_id

def test_update_purchase_order_status_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_upostat"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    po = create_random_purchase_order(db, status=PurchaseOrderStatus.ORDERED, po_notes_suffix="_api_upd_stat")

    status_update_data = {"status": PurchaseOrderStatus.CANCELLED.value}
    response = client.patch(f"{API_V1_PO_URL}/{po.id}/status", json=status_update_data, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["status"] == PurchaseOrderStatus.CANCELLED.value

def test_receive_purchase_order_item_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_recpoitem"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)

    po = create_random_purchase_order(db, num_items=1, status=PurchaseOrderStatus.ORDERED, po_notes_suffix="_api_rec")
    po_item_to_receive = po.items[0]
    product_id = po_item_to_receive.product_id
    quantity_ordered = po_item_to_receive.quantity_ordered

    ensure_inventory_item_exists(db, product_id=product_id, initial_quantity=0)
    initial_inv_item = inventory_service.get_inventory_item_by_product_id(db, product_id)
    initial_stock_qty = initial_inv_item.quantity_on_hand if initial_inv_item else 0

    receive_data = {"quantity_received": quantity_ordered}
    url = f"{API_V1_PO_URL}/{po.id}/items/{po_item_to_receive.id}/receive"
    response = client.post(url, json=receive_data, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["quantity_received"] == quantity_ordered

    updated_inv_item = inventory_service.get_inventory_item_by_product_id(db, product_id)
    assert updated_inv_item is not None
    assert updated_inv_item.quantity_on_hand == initial_stock_qty + quantity_ordered

    updated_po_response = client.get(f"{API_V1_PO_URL}/{po.id}", headers=manager_headers)
    assert updated_po_response.json()["status"] == PurchaseOrderStatus.RECEIVED.value

def test_receive_po_item_api_over_receive_fail(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_recpo_over"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    po = create_random_purchase_order(db, num_items=1, status=PurchaseOrderStatus.ORDERED)
    po_item = po.items[0]
    ensure_inventory_item_exists(db, product_id=po_item.product_id)

    receive_data = {"quantity_received": po_item.quantity_ordered + 1}
    url = f"{API_V1_PO_URL}/{po.id}/items/{po_item.id}/receive"
    response = client.post(url, json=receive_data, headers=manager_headers)
    assert response.status_code == 400, response.text
    assert "cannot exceed quantity ordered" in response.json()["detail"].lower()
