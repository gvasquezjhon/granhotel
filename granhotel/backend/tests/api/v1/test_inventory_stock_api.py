from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta # Not directly used here, but good for reference if date params were added
import uuid # For user_id if needed by get_auth_headers directly

from app.core.config import settings
from app.models.user import UserRole # For creating users with specific roles
from app.models.inventory import StockMovementType
from app.schemas.inventory import InventoryAdjustment, InventoryItemLowStockThresholdUpdate
from tests.utils.user import create_user_in_db
from tests.utils.product import create_random_product
from tests.utils.inventory import ensure_inventory_item_exists
# from tests.api.v1.test_users_endpoints import get_auth_headers # Re-use from user API tests
# Re-defining for clarity in this file or ensure it's in a common test util
from app.core.security import create_access_token
from tests.utils.common import random_email


API_V1_INV_STOCK_URL = f"{settings.API_V1_STR}/inventory-stock"

# Local get_auth_headers, similar to the one in test_users_endpoints or test_supplier_api
def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}


def test_read_inventory_item_for_product_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_rinv"))
    user_headers = get_auth_headers(user.id, user.role) # Use user.id (UUID) and user.role (Enum)
    product = create_random_product(db, name_suffix="_inv_read")
    inv_item_created = ensure_inventory_item_exists(db, product.id, initial_quantity=10, low_stock_threshold=3)

    response = client.get(f"{API_V1_INV_STOCK_URL}/products/{product.id}", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["product_id"] == product.id
    assert content["quantity_on_hand"] == 10
    assert content["low_stock_threshold"] == 3
    assert content["product"]["name"] == product.name

def test_read_inventory_item_for_non_existent_product_fail(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_rinv_np"))
    user_headers = get_auth_headers(user.id, user.role)
    response = client.get(f"{API_V1_INV_STOCK_URL}/products/99999", headers=user_headers)
    assert response.status_code == 404
    assert "product with id 99999 not found" in response.json()["detail"].lower()


def test_read_inventory_item_product_exists_no_inv_item_fail(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_rinv_ni"))
    user_headers = get_auth_headers(user.id, user.role)
    product_no_inv = create_random_product(db, name_suffix="_no_inv_item")

    response = client.get(f"{API_V1_INV_STOCK_URL}/products/{product_no_inv.id}", headers=user_headers)
    assert response.status_code == 404
    assert "inventory record for product id" in response.json()["detail"].lower()


def test_adjust_product_stock_api_increase_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_adjinc"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    product = create_random_product(db, name_suffix="_adj_inc")
    ensure_inventory_item_exists(db, product.id, initial_quantity=5)

    adjustment_data = {
        "quantity_changed": 10,
        "movement_type": StockMovementType.ADJUSTMENT_INCREASE.value,
        "reason": "API Stock Correction Increase"
    }
    response = client.post(f"{API_V1_INV_STOCK_URL}/products/{product.id}/adjust-stock", json=adjustment_data, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["quantity_on_hand"] == 15

def test_adjust_product_stock_api_decrease_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, email=random_email("_admin_adjdec"))
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    product = create_random_product(db, name_suffix="_adj_dec")
    ensure_inventory_item_exists(db, product.id, initial_quantity=20)

    adjustment_data = {
        "quantity_changed": -5,
        "movement_type": StockMovementType.ADJUSTMENT_DECREASE.value,
        "reason": "API Stock Write-off"
    }
    response = client.post(f"{API_V1_INV_STOCK_URL}/products/{product.id}/adjust-stock", json=adjustment_data, headers=admin_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["quantity_on_hand"] == 15

def test_adjust_product_stock_api_invalid_movement_type_fail(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_adjinvmov"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    product = create_random_product(db, name_suffix="_adj_invmov")
    ensure_inventory_item_exists(db, product.id, initial_quantity=5)

    adjustment_data = {"quantity_changed": 5, "movement_type": StockMovementType.SALE.value}
    response = client.post(f"{API_V1_INV_STOCK_URL}/products/{product.id}/adjust-stock", json=adjustment_data, headers=manager_headers)
    assert response.status_code == 400, response.text
    assert "invalid movement type for stock adjustment" in response.json()["detail"].lower()

def test_adjust_product_stock_api_below_zero_fail(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_adjneg"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    product = create_random_product(db, name_suffix="_adj_neg")
    ensure_inventory_item_exists(db, product.id, initial_quantity=3)

    adjustment_data = {"quantity_changed": -5, "movement_type": StockMovementType.ADJUSTMENT_DECREASE.value}
    response = client.post(f"{API_V1_INV_STOCK_URL}/products/{product.id}/adjust-stock", json=adjustment_data, headers=manager_headers)
    assert response.status_code == 400, response.text
    assert "cannot go below zero" in response.json()["detail"].lower()


def test_set_product_low_stock_threshold_api(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_setlow"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    product = create_random_product(db, name_suffix="_set_low")
    ensure_inventory_item_exists(db, product.id)

    threshold_data = {"low_stock_threshold": 10}
    response = client.put(f"{API_V1_INV_STOCK_URL}/products/{product.id}/low-stock-threshold", json=threshold_data, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["low_stock_threshold"] == 10

def test_get_low_stock_items_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_getlow"))
    user_headers = get_auth_headers(user.id, user.role)

    prod_low = create_random_product(db, name_suffix="_low", is_active=True)
    ensure_inventory_item_exists(db, prod_low.id, initial_quantity=5, low_stock_threshold=10) # 5 <= 10, threshold > 0

    prod_ok = create_random_product(db, name_suffix="_ok_stock", is_active=True)
    ensure_inventory_item_exists(db, prod_ok.id, initial_quantity=15, low_stock_threshold=10) # 15 > 10

    response = client.get(f"{API_V1_INV_STOCK_URL}/low-stock", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert any(item["product_id"] == prod_low.id for item in content)
    assert not any(item["product_id"] == prod_ok.id for item in content)


def test_get_product_stock_movement_history_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email("_usr_gethist"))
    user_headers = get_auth_headers(user.id, user.role)
    product = create_random_product(db, name_suffix="_hist_prod")

    ensure_inventory_item_exists(db, product.id, initial_quantity=20)
    services.inventory_service.update_stock(db, product.id, -5, StockMovementType.SALE)

    response = client.get(f"{API_V1_INV_STOCK_URL}/products/{product.id}/history", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2 # INITIAL_STOCK (from ensure) and SALE

    # Check for the SALE movement (usually most recent if not considering exact timestamps)
    # Ordering is movement_date DESC, id DESC
    sale_movement = next((m for m in content if m["movement_type"] == StockMovementType.SALE.value), None)
    assert sale_movement is not None
    assert sale_movement["quantity_changed"] == -5

    # Test filtering by movement_type
    response_filtered = client.get(f"{API_V1_INV_STOCK_URL}/products/{product.id}/history?movement_type={StockMovementType.INITIAL_STOCK.value}", headers=user_headers)
    assert response_filtered.status_code == 200, response_filtered.text
    content_filtered = response_filtered.json()
    assert len(content_filtered) == 1
    assert content_filtered[0]["movement_type"] == StockMovementType.INITIAL_STOCK.value
    assert content_filtered[0]["quantity_changed"] == 20
