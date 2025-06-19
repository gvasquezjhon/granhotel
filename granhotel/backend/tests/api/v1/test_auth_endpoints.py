from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from tests.utils.user import create_user_in_db, random_email # Ensure random_email is available if needed, or use specific emails

API_V1_AUTH_URL = f"{settings.API_V1_STR}/auth"

def test_login_for_access_token(client: TestClient, db: Session):
    email = random_email() # Using random_email from utils
    password = "loginTestPass"
    create_user_in_db(db, email=email, password=password, is_active=True)

    login_data = {"username": email, "password": password}
    response = client.post(f"{API_V1_AUTH_URL}/login", data=login_data) # Form data
    assert response.status_code == 200, response.text
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_inactive_user(client: TestClient, db: Session):
    email = random_email()
    password = "loginInactivePass"
    create_user_in_db(db, email=email, password=password, is_active=False)
    login_data = {"username": email, "password": password}
    response = client.post(f"{API_V1_AUTH_URL}/login", data=login_data)
    # Service's authenticate_user returns None for inactive user,
    # API layer translates this to 401 for "Incorrect email or password"
    # or could be specific 400 as in auth.py. Current auth.py raises 400 for inactive user *after* successful auth.
    # Let's check against the code in auth.py:
    # if not user.is_active: -> raises 400
    assert response.status_code == 400, response.text
    assert "inactive user" in response.json()["detail"].lower()


def test_login_wrong_credentials(client: TestClient, db: Session):
    email = random_email()
    password = "correctPassword"
    create_user_in_db(db, email=email, password=password, is_active=True)

    # Wrong password
    login_data_wrong_pass = {"username": email, "password": "wrongPassword"}
    response_wrong_pass = client.post(f"{API_V1_AUTH_URL}/login", data=login_data_wrong_pass)
    assert response_wrong_pass.status_code == 401, response_wrong_pass.text
    assert "incorrect email or password" in response_wrong_pass.json()["detail"].lower()

    # Wrong email
    login_data_wrong_email = {"username": "nonexistent@example.com", "password": password}
    response_wrong_email = client.post(f"{API_V1_AUTH_URL}/login", data=login_data_wrong_email)
    assert response_wrong_email.status_code == 401, response_wrong_email.text
    assert "incorrect email or password" in response_wrong_email.json()["detail"].lower()


def test_refresh_token(client: TestClient, db: Session):
    email = random_email()
    password = "refreshTestPass"
    create_user_in_db(db, email=email, password=password, is_active=True)
    login_data = {"username": email, "password": password}
    login_response = client.post(f"{API_V1_AUTH_URL}/login", data=login_data)
    assert login_response.status_code == 200, "Login failed during refresh token test setup"
    refresh_token = login_response.json()["refresh_token"]

    refresh_payload = {"refresh_token": refresh_token}
    refresh_response = client.post(f"{API_V1_AUTH_URL}/refresh", json=refresh_payload)
    assert refresh_response.status_code == 200, refresh_response.text
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["refresh_token"] == refresh_token # Assuming refresh token is reused for now
    assert new_tokens["access_token"] != login_response.json()["access_token"] # New access token should be different

def test_refresh_with_invalid_token(client: TestClient):
    refresh_payload = {"refresh_token": "this.is.an.invalid.token"}
    response = client.post(f"{API_V1_AUTH_URL}/refresh", json=refresh_payload)
    assert response.status_code == 401, response.text
    assert "invalid or expired refresh token" in response.json()["detail"].lower()

def test_refresh_token_for_inactive_user(client: TestClient, db: Session):
    email = random_email()
    password = "refreshInactivePass"
    user = create_user_in_db(db, email=email, password=password, is_active=True)

    login_data = {"username": email, "password": password}
    login_response = client.post(f"{API_V1_AUTH_URL}/login", data=login_data)
    assert login_response.status_code == 200, "Login failed during setup"
    refresh_token = login_response.json()["refresh_token"]

    # Deactivate user after obtaining token
    services.user_service.deactivate_user(db, user_id=user.id)

    refresh_payload = {"refresh_token": refresh_token}
    response = client.post(f"{API_V1_AUTH_URL}/refresh", json=refresh_payload)
    assert response.status_code == 400, response.text # As per auth.py logic
    assert "inactive user" in response.json()["detail"].lower()
