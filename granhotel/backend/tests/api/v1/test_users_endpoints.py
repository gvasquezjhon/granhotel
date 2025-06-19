from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid # For user_id path param

from app.core.config import settings
from app.schemas.user import UserCreate # Ensure UserRole is available if needed directly
from app.models.user import UserRole # For creating users with specific roles and for query params
from tests.utils.user import create_user_in_db, random_email
from app.core.security import create_access_token

API_V1_USERS_URL = f"{settings.API_V1_STR}/users"

def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict: # Use uuid.UUID and UserRole
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}

def test_create_user_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="admin_cu")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)

    new_user_email = random_email()
    user_data = {"email": new_user_email, "password": "newPassword123", "first_name": "API", "last_name": "Created", "role": UserRole.RECEPTIONIST.value, "is_active": True}

    response = client.post(f"{API_V1_USERS_URL}/", json=user_data, headers=admin_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["email"] == new_user_email
    assert content["role"] == UserRole.RECEPTIONIST.value

def test_create_user_api_as_non_admin(client: TestClient, db: Session):
    non_admin_user = create_user_in_db(db, role=UserRole.RECEPTIONIST, suffix_for_email="nonadmin_cu")
    non_admin_headers = get_auth_headers(non_admin_user.id, non_admin_user.role)

    user_data = {"email": random_email(), "password": "pw", "role": UserRole.RECEPTIONIST.value}
    response = client.post(f"{API_V1_USERS_URL}/", json=user_data, headers=non_admin_headers)
    assert response.status_code == 403, response.text # Forbidden

def test_read_me_api(client: TestClient, db: Session):
    user = create_user_in_db(db, suffix_for_email="readme")
    user_headers = get_auth_headers(user.id, user.role)

    response = client.get(f"{API_V1_USERS_URL}/me", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["email"] == user.email
    assert content["id"] == str(user.id)

def test_list_all_users_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="admin_list")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    create_user_in_db(db, suffix_for_email="user1_list") # Create some users to list
    create_user_in_db(db, suffix_for_email="user2_list")

    response = client.get(f"{API_V1_USERS_URL}/", headers=admin_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 3 # Admin + 2 users

def test_list_all_users_api_as_non_admin(client: TestClient, db: Session):
    non_admin_user = create_user_in_db(db, role=UserRole.RECEPTIONIST, suffix_for_email="nonadmin_list")
    non_admin_headers = get_auth_headers(non_admin_user.id, non_admin_user.role)
    response = client.get(f"{API_V1_USERS_URL}/", headers=non_admin_headers)
    assert response.status_code == 403, response.text

def test_read_user_by_id_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="admin_getid")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    user_to_get = create_user_in_db(db, suffix_for_email="target_getid")

    response = client.get(f"{API_V1_USERS_URL}/{user_to_get.id}", headers=admin_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == str(user_to_get.id)

def test_update_current_user_me_api(client: TestClient, db: Session):
    user = create_user_in_db(db, suffix_for_email="updateme")
    user_headers = get_auth_headers(user.id, user.role)
    update_data = {"first_name": "UpdatedViaMe"}
    response = client.put(f"{API_V1_USERS_URL}/me", json=update_data, headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["first_name"] == "UpdatedViaMe"

def test_update_user_by_id_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="admin_upd_id")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    user_to_update = create_user_in_db(db, role=UserRole.RECEPTIONIST, suffix_for_email="target_upd_id")

    update_data = {"last_name": "AdminUpdated", "role": UserRole.MANAGER.value}
    response = client.put(f"{API_V1_USERS_URL}/{user_to_update.id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["last_name"] == "AdminUpdated"
    assert content["role"] == UserRole.MANAGER.value

def test_activate_deactivate_user_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="admin_actdeact")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    user_to_mod = create_user_in_db(db, is_active=True, suffix_for_email="target_actdeact")

    # Deactivate
    response_deact = client.patch(f"{API_V1_USERS_URL}/{user_to_mod.id}/deactivate", headers=admin_headers)
    assert response_deact.status_code == 200, response_deact.text
    assert response_deact.json()["is_active"] is False

    # Activate
    response_act = client.patch(f"{API_V1_USERS_URL}/{user_to_mod.id}/activate", headers=admin_headers)
    assert response_act.status_code == 200, response_act.text
    assert response_act.json()["is_active"] is True

def test_update_user_role_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="admin_rolechg")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    user_to_chg_role = create_user_in_db(db, role=UserRole.RECEPTIONIST, suffix_for_email="target_rolechg")

    response = client.patch(f"{API_V1_USERS_URL}/{user_to_chg_role.id}/role?new_role={UserRole.MANAGER.value}", headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["role"] == UserRole.MANAGER.value
