from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid # For get_auth_headers if user_id is UUID

from app.core.config import settings
from app.models.user import UserRole # For creating users with specific roles
from app.schemas.inventory import SupplierCreate, SupplierUpdate
from tests.utils.user import create_user_in_db
from tests.utils.inventory import create_random_supplier
from tests.utils.common import random_lower_string, random_email
# Assuming get_auth_headers is in test_users_endpoints.py and works with UUIDs
# If not, it might need to be moved to a common test util or adapted.
# For now, let's assume it's accessible and works.
# from tests.api.v1.test_users_endpoints import get_auth_headers
# For simplicity, re-define a local get_auth_headers or ensure it's in a common spot.
from app.core.security import create_access_token # Use this directly for test tokens

API_V1_SUPPLIERS_URL = f"{settings.API_V1_STR}/suppliers"

def get_auth_headers_for_test(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}


def test_create_supplier_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, email=random_email(prefix="admin_csup"))
    admin_headers = get_auth_headers_for_test(admin_user.id, admin_user.role)

    supplier_name = f"API Supplier Test {random_lower_string(4)}"
    supplier_data = {"name": supplier_name, "email": random_email(prefix=supplier_name[:10].replace(" ", ""))}

    response = client.post(f"{API_V1_SUPPLIERS_URL}/", json=supplier_data, headers=admin_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["name"] == supplier_name
    assert "id" in content

def test_create_supplier_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email(prefix="mgr_csup"))
    manager_headers = get_auth_headers_for_test(manager_user.id, manager_user.role)

    supplier_name = f"Manager API Supplier {random_lower_string(4)}"
    supplier_data = {"name": supplier_name, "email": random_email(prefix=supplier_name[:10].replace(" ", ""))}

    response = client.post(f"{API_V1_SUPPLIERS_URL}/", json=supplier_data, headers=manager_headers)
    assert response.status_code == 201, response.text

def test_create_supplier_api_as_receptionist_fail(client: TestClient, db: Session):
    receptionist_user = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email(prefix="rec_csup"))
    receptionist_headers = get_auth_headers_for_test(receptionist_user.id, receptionist_user.role)

    supplier_name = f"Recept API Supplier {random_lower_string(4)}"
    supplier_data = {"name": supplier_name, "email": random_email(prefix=supplier_name[:10].replace(" ", ""))}

    response = client.post(f"{API_V1_SUPPLIERS_URL}/", json=supplier_data, headers=receptionist_headers)
    assert response.status_code == 403, response.text # Forbidden

def test_read_all_suppliers_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email(prefix="usr_rsup")) # Any active user
    user_headers = get_auth_headers_for_test(user.id, user.role)

    create_random_supplier(db, suffix="_api_s1")
    create_random_supplier(db, suffix="_api_s2")

    response = client.get(f"{API_V1_SUPPLIERS_URL}/", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2

def test_read_single_supplier_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email(prefix="usr_rsingle_sup"))
    user_headers = get_auth_headers_for_test(user.id, user.role)
    supplier = create_random_supplier(db, suffix="_api_single")

    response = client.get(f"{API_V1_SUPPLIERS_URL}/{supplier.id}", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == supplier.id
    assert content["name"] == supplier.name

def test_read_single_supplier_not_found_api(client: TestClient, db: Session):
    user = create_user_in_db(db, email=random_email(prefix="usr_rsnf_sup"))
    user_headers = get_auth_headers_for_test(user.id, user.role)
    response = client.get(f"{API_V1_SUPPLIERS_URL}/999999", headers=user_headers)
    assert response.status_code == 404, response.text

def test_update_supplier_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email(prefix="mgr_usup"))
    manager_headers = get_auth_headers_for_test(manager_user.id, manager_user.role)
    supplier = create_random_supplier(db, suffix="_api_upd")

    update_data = {"contact_person": "Jane ManagerUpdate"}
    response = client.put(f"{API_V1_SUPPLIERS_URL}/{supplier.id}", json=update_data, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["contact_person"] == "Jane ManagerUpdate"
    assert content["name"] == supplier.name

def test_delete_supplier_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, email=random_email(prefix="admin_dsup"))
    admin_headers = get_auth_headers_for_test(admin_user.id, admin_user.role)
    supplier = create_random_supplier(db, suffix="_api_del")

    response = client.delete(f"{API_V1_SUPPLIERS_URL}/{supplier.id}", headers=admin_headers)
    assert response.status_code == 200, response.text

    get_response = client.get(f"{API_V1_SUPPLIERS_URL}/{supplier.id}", headers=admin_headers)
    assert get_response.status_code == 404, get_response.text

def test_delete_supplier_api_with_po_fail(client: TestClient, db: Session):
    from tests.utils.inventory import create_random_purchase_order
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, email=random_email(prefix="admin_delsup_po"))
    admin_headers = get_auth_headers_for_test(admin_user.id, admin_user.role)

    supplier_with_po = create_random_supplier(db, suffix="_api_del_w_po")
    create_random_purchase_order(db, supplier_id=supplier_with_po.id)
    db.refresh(supplier_with_po)

    response = client.delete(f"{API_V1_SUPPLIERS_URL}/{supplier_with_po.id}", headers=admin_headers)
    assert response.status_code == 400, response.text
    assert "associated purchase orders" in response.json()["detail"].lower()

def test_create_supplier_api_duplicate_name_fail(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, email=random_email("_admin_csup_dupname"))
    admin_headers = get_auth_headers_for_test(admin_user.id, admin_user.role)

    supplier_name = f"API Supplier DupName {random_lower_string(4)}"
    create_random_supplier(db, name=supplier_name) # Create one with this name

    supplier_data = {"name": supplier_name, "email": random_email(supplier_name[:5])}
    response = client.post(f"{API_V1_SUPPLIERS_URL}/", json=supplier_data, headers=admin_headers)
    assert response.status_code == 400, response.text # Service raises 400 for duplicate name
    assert "name" in response.json()["detail"].lower()
    assert "already exists" in response.json()["detail"].lower()
