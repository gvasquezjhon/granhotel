import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from app import schemas, services, models
from app.models.user import UserRole
from tests.utils.user import create_user_in_db, random_email

def test_create_user_service(db: Session):
    email = random_email()
    user_in = schemas.UserCreate(email=email, password="testpassword", first_name="Test", last_name="UserSvc", role=UserRole.MANAGER, is_active=True)
    user = services.user_service.create_user(db, user_in)
    assert user is not None
    assert user.email == email
    assert user.first_name == "Test"
    assert user.role == UserRole.MANAGER
    assert user.is_active is True
    assert hasattr(user, "hashed_password") and user.hashed_password is not None

def test_create_user_duplicate_email_service(db: Session):
    email = random_email()
    create_user_in_db(db, email=email, password="pw1") # suffix_for_email not used here, relying on random_email being unique enough for setup
    user_in_dup = schemas.UserCreate(email=email, password="pw2") # UserCreate schema has defaults for role, is_active
    with pytest.raises(HTTPException) as exc_info:
        services.user_service.create_user(db, user_in_dup)
    assert exc_info.value.status_code == 400
    assert "email already exists" in exc_info.value.detail # Check specific error message

def test_authenticate_user_service(db: Session):
    email = random_email()
    password = "authTestPassword"
    create_user_in_db(db, email=email, password=password, is_active=True)

    authed_user = services.user_service.authenticate_user(db, email, password)
    assert authed_user is not None
    assert authed_user.email == email

    assert services.user_service.authenticate_user(db, email, "wrongpass") is None
    assert services.user_service.authenticate_user(db, "wrong@email.com", password) is None

def test_authenticate_inactive_user(db: Session):
    email = random_email()
    password = "inactivePassword"
    create_user_in_db(db, email=email, password=password, is_active=False)
    assert services.user_service.authenticate_user(db, email, password) is None

def test_get_user_service(db: Session):
    user_created = create_user_in_db(db)
    user_fetched = services.user_service.get_user(db, user_id=user_created.id)
    assert user_fetched is not None
    assert user_fetched.id == user_created.id

def test_update_user_service(db: Session):
    user = create_user_in_db(db, role=UserRole.RECEPTIONIST)
    new_first_name = "UpdatedFirstName"
    new_password = "newSecurePassword123"
    user_update_schema = schemas.UserUpdate(first_name=new_first_name, password=new_password, role=UserRole.ADMIN)

    updated_user = services.user_service.update_user(db, user_db_obj=user, user_in=user_update_schema)
    assert updated_user.first_name == new_first_name
    assert updated_user.role == UserRole.ADMIN
    # Verify new password works
    assert services.user_service.authenticate_user(db, user.email, new_password) is not None

def test_activate_deactivate_user_service(db: Session):
    user_active = create_user_in_db(db, is_active=True, suffix_for_email="_actdeact1")
    user_inactive = create_user_in_db(db, is_active=False, suffix_for_email="_actdeact2")

    # Deactivate active user
    deactivated_user = services.user_service.deactivate_user(db, user_id=user_active.id)
    assert deactivated_user is not None and deactivated_user.is_active is False

    # Activate inactive user
    activated_user = services.user_service.activate_user(db, user_id=user_inactive.id)
    assert activated_user is not None and activated_user.is_active is True

    # Test activating already active user (should return user, no change)
    assert services.user_service.activate_user(db, user_id=activated_user.id).is_active is True
    # Test deactivating already inactive user
    assert services.user_service.deactivate_user(db, user_id=deactivated_user.id).is_active is False


def test_update_user_role_service(db: Session):
    user = create_user_in_db(db, role=UserRole.RECEPTIONIST)
    updated_user = services.user_service.update_user_role(db, user_id=user.id, new_role=UserRole.MANAGER)
    assert updated_user is not None
    assert updated_user.role == UserRole.MANAGER

def test_get_users_service_with_filters(db: Session):
    create_user_in_db(db, role=UserRole.ADMIN, is_active=True, suffix_for_email="_getusers1")
    create_user_in_db(db, role=UserRole.MANAGER, is_active=True, suffix_for_email="_getusers2")
    create_user_in_db(db, role=UserRole.RECEPTIONIST, is_active=False, suffix_for_email="_getusers3")

    all_users = services.user_service.get_users(db)
    assert len(all_users) >= 3

    active_users = services.user_service.get_users(db, is_active=True)
    assert len(active_users) >= 2
    assert all(u.is_active for u in active_users)

    admin_users = services.user_service.get_users(db, role=UserRole.ADMIN)
    assert len(admin_users) >= 1
    assert all(u.role == UserRole.ADMIN for u in admin_users)

    inactive_receptionists = services.user_service.get_users(db, is_active=False, role=UserRole.RECEPTIONIST)
    assert len(inactive_receptionists) >= 1
    assert all(not u.is_active and u.role == UserRole.RECEPTIONIST for u in inactive_receptionists)
