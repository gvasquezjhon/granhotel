from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.schemas.guest import GuestCreate, GuestUpdate # Ensure DocumentType is available for test data
from app.models.guest import DocumentType # Direct import for test data clarity
from app.services import guest_service # To help setup for filter test
from app import schemas as app_schemas # For guest_service.create_guest

from tests.utils.guest import create_random_guest, random_email, random_document_number
import random

API_V1_GUESTS_URL = f"{settings.API_V1_STR}/guests"

def test_create_guest_api(client: TestClient, db: Session) -> None:
    email = random_email()
    doc_num = random_document_number(DocumentType.DNI)
    data = {
        "first_name": "APITest", "last_name": "User", "email": email,
        "document_type": DocumentType.DNI.value, "document_number": doc_num,
        "phone_number": "987654321"
    }
    response = client.post(f"{API_V1_GUESTS_URL}/", json=data)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["email"] == email
    assert content["document_number"] == doc_num
    assert "id" in content

def test_create_guest_api_duplicate_email(client: TestClient, db: Session) -> None:
    existing_guest = create_random_guest(db, suffix="_apidupemail")
    data = {
        "first_name": "APIDup", "last_name": "Email", "email": existing_guest.email, # Duplicate email
        "document_type": DocumentType.PASSPORT.value, "document_number": random_document_number(DocumentType.PASSPORT)
    }
    response = client.post(f"{API_V1_GUESTS_URL}/", json=data)
    assert response.status_code == 400, response.text
    assert "email" in response.json()["detail"].lower()

def test_read_guests_api(client: TestClient, db: Session) -> None:
    guest1 = create_random_guest(db, suffix="_apilist1")
    guest2 = create_random_guest(db, suffix="_apilist2")
    response = client.get(f"{API_V1_GUESTS_URL}/")
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    guest_ids = [g["id"] for g in content]
    assert guest1.id in guest_ids
    assert guest2.id in guest_ids

def test_read_guests_api_with_filters(client: TestClient, db: Session) -> None:
    # Create a guest with a specific first name for filtering
    target_first_name = "FilterTargetName"
    target_doc_num = random_document_number(DocumentType.DNI) + "_filt" # make it somewhat unique

    target_guest_schema = app_schemas.GuestCreate(
        first_name=target_first_name,
        last_name="FilterTest",
        email=random_email(),
        document_type=DocumentType.DNI,
        document_number=target_doc_num
    )
    target_guest = guest_service.create_guest(db, guest_in=target_guest_schema)

    # Create another guest that shouldn't match the filter
    create_random_guest(db, suffix="_filter_other")

    response = client.get(f"{API_V1_GUESTS_URL}/?first_name={target_first_name}")
    assert response.status_code == 200, response.text
    content = response.json()
    assert len(content) >= 1

    found_target = False
    for guest_data in content:
        if guest_data["id"] == target_guest.id:
            assert guest_data["first_name"] == target_first_name
            found_target = True
            break
    assert found_target, f"Guest with first name {target_first_name} not found in filtered list"

def test_read_single_guest_api(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_apiget")
    response = client.get(f"{API_V1_GUESTS_URL}/{guest.id}")
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == guest.id
    assert content["email"] == guest.email

def test_read_single_guest_api_not_found(client: TestClient) -> None:
    response = client.get(f"{API_V1_GUESTS_URL}/999999")
    assert response.status_code == 404

def test_update_guest_api(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_apiupd")
    update_data = {"first_name": "UpdatedAPIUser", "is_blacklisted": True}
    response = client.put(f"{API_V1_GUESTS_URL}/{guest.id}", json=update_data)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["first_name"] == "UpdatedAPIUser"
    assert content["is_blacklisted"] is True
    assert content["id"] == guest.id

def test_update_guest_api_not_found(client: TestClient) -> None:
    update_data = {"first_name": "GhostUser"}
    response = client.put(f"{API_V1_GUESTS_URL}/999999", json=update_data)
    assert response.status_code == 404

def test_delete_guest_api(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_apidel")
    response = client.delete(f"{API_V1_GUESTS_URL}/{guest.id}")
    assert response.status_code == 200, response.text # Assuming service returns deleted obj

    # Verify it's gone
    get_response = client.get(f"{API_V1_GUESTS_URL}/{guest.id}")
    assert get_response.status_code == 404

def test_delete_guest_api_not_found(client: TestClient) -> None:
    response = client.delete(f"{API_V1_GUESTS_URL}/999999")
    assert response.status_code == 404

def test_blacklist_guest_api(client: TestClient, db: Session) -> None:
    guest = create_random_guest(db, suffix="_apiblist")
    assert not guest.is_blacklisted # Created as not blacklisted by default

    # Blacklist
    response_blist = client.patch(f"{API_V1_GUESTS_URL}/{guest.id}/blacklist?blacklist_status=true")
    assert response_blist.status_code == 200, response_blist.text
    content_blist = response_blist.json()
    assert content_blist["is_blacklisted"] is True

    # Un-blacklist
    response_unblist = client.patch(f"{API_V1_GUESTS_URL}/{guest.id}/blacklist?blacklist_status=false")
    assert response_unblist.status_code == 200, response_unblist.text
    content_unblist = response_unblist.json()
    assert content_unblist["is_blacklisted"] is False

def test_blacklist_guest_api_not_found(client: TestClient) -> None:
    response = client.patch(f"{API_V1_GUESTS_URL}/999999/blacklist?blacklist_status=true")
    assert response.status_code == 404
