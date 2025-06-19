import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import schemas
from app.services import guest_service
from app.models.guest import Guest as GuestModel, DocumentType
from tests.utils.guest import create_random_guest, random_email, random_document_number, create_guest_with_data

def test_create_guest_service(db: Session) -> None:
    email = random_email()
    doc_num = random_document_number(DocumentType.DNI)
    guest_in = schemas.GuestCreate(
        first_name="ServiceTest",
        last_name="User",
        email=email,
        document_type=DocumentType.DNI,
        document_number=doc_num
    )
    guest = guest_service.create_guest(db=db, guest_in=guest_in)
    assert guest is not None
    assert guest.email == email
    assert guest.document_number == doc_num
    assert guest.first_name == "ServiceTest"

def test_create_guest_duplicate_email(db: Session) -> None:
    email = random_email()
    # Create one guest with this email
    guest_in_orig = schemas.GuestCreate(first_name="OrigF", last_name="OrigL", email=email, document_type=DocumentType.DNI, document_number=random_document_number(DocumentType.DNI))
    guest_service.create_guest(db=db, guest_in=guest_in_orig)

    # Try to create another guest with the same email
    guest_in_dup = schemas.GuestCreate(first_name="DupF", last_name="DupL", email=email, document_type=DocumentType.PASSPORT, document_number=random_document_number(DocumentType.PASSPORT))
    with pytest.raises(HTTPException) as excinfo:
        guest_service.create_guest(db=db, guest_in=guest_in_dup)
    assert excinfo.value.status_code == 400
    assert "email" in excinfo.value.detail.lower()

def test_create_guest_duplicate_document_number(db: Session) -> None:
    doc_num = random_document_number(DocumentType.RUC)
    guest_in_orig = schemas.GuestCreate(first_name="OrigF", last_name="OrigL", email=random_email(), document_type=DocumentType.RUC, document_number=doc_num)
    guest_service.create_guest(db=db, guest_in=guest_in_orig)

    guest_in_dup = schemas.GuestCreate(first_name="DupF", last_name="DupL", email=random_email(), document_type=DocumentType.RUC, document_number=doc_num)
    with pytest.raises(HTTPException) as excinfo:
        guest_service.create_guest(db=db, guest_in=guest_in_dup)
    assert excinfo.value.status_code == 400
    assert "document number" in excinfo.value.detail.lower()


def test_get_guest_service(db: Session) -> None:
    guest_created = create_random_guest(db, suffix="_getsvc")
    guest_fetched = guest_service.get_guest(db, guest_id=guest_created.id)
    assert guest_fetched is not None
    assert guest_fetched.id == guest_created.id
    assert guest_fetched.email == guest_created.email

def test_get_guest_by_email_service(db: Session) -> None:
    guest_created = create_random_guest(db, suffix="_getemailsvc")
    guest_fetched = guest_service.get_guest_by_email(db, email=guest_created.email)
    assert guest_fetched is not None
    assert guest_fetched.id == guest_created.id

def test_get_guest_by_document_number_service(db: Session) -> None:
    guest_created = create_random_guest(db, suffix="_getdocsvc")
    guest_fetched = guest_service.get_guest_by_document_number(db, document_number=guest_created.document_number)
    assert guest_fetched is not None
    assert guest_fetched.id == guest_created.id

def test_get_guests_service_filtering(db: Session) -> None:
    # Create a few guests with specific characteristics for filtering
    guest1_data = schemas.GuestCreate(first_name="FilTestFirst", last_name="UserA", email=random_email(), document_type=DocumentType.DNI, document_number=random_document_number(DocumentType.DNI)+"F1", is_blacklisted=False)
    guest_service.create_guest(db, guest1_data)

    guest2_data = schemas.GuestCreate(first_name="Another", last_name="FilTestLast", email=random_email(), document_type=DocumentType.PASSPORT, document_number=random_document_number(DocumentType.PASSPORT)+"F2", is_blacklisted=True)
    guest_service.create_guest(db, guest2_data)

    guest3_data = schemas.GuestCreate(first_name="FilTestFirst", last_name="UserC", email="filterme@example.com", document_type=DocumentType.RUC, document_number="12345678901F3", is_blacklisted=False) # Explicit doc num
    guest_service.create_guest(db, guest3_data)

    # Test filtering
    assert len(guest_service.get_guests(db, first_name="FilTestFirst")) >= 2
    assert len(guest_service.get_guests(db, last_name="FilTestLast")) >= 1
    assert len(guest_service.get_guests(db, email="filterme@example.com")) >= 1
    assert len(guest_service.get_guests(db, document_number="12345678901F3")) >= 1
    assert len(guest_service.get_guests(db, is_blacklisted=True)) >= 1
    assert len(guest_service.get_guests(db, is_blacklisted=False)) >= 2


def test_update_guest_service(db: Session) -> None:
    guest_to_update = create_random_guest(db, suffix="_updsvc")
    new_email = random_email()
    update_data = schemas.GuestUpdate(email=new_email, first_name="UpdatedName")

    updated_guest = guest_service.update_guest(db=db, guest_db_obj=guest_to_update, guest_in=update_data)
    assert updated_guest is not None
    assert updated_guest.email == new_email
    assert updated_guest.first_name == "UpdatedName"
    assert updated_guest.id == guest_to_update.id

def test_update_guest_service_conflict_email(db: Session) -> None:
    guest1 = create_random_guest(db, suffix="_updconf1")
    guest2 = create_random_guest(db, suffix="_updconf2")

    update_data_conflict = schemas.GuestUpdate(email=guest1.email) # Try to update guest2 with guest1's email
    with pytest.raises(HTTPException) as excinfo:
        guest_service.update_guest(db=db, guest_db_obj=guest2, guest_in=update_data_conflict)
    assert excinfo.value.status_code == 400
    assert "email" in excinfo.value.detail.lower()


def test_delete_guest_service(db: Session) -> None:
    guest_to_delete = create_random_guest(db, suffix="_delsvc")
    guest_id = guest_to_delete.id

    deleted_guest = guest_service.delete_guest(db=db, guest_id=guest_id)
    assert deleted_guest is not None
    assert deleted_guest.id == guest_id
    assert guest_service.get_guest(db, guest_id=guest_id) is None

def test_blacklist_guest_service(db: Session) -> None:
    guest = create_random_guest(db, suffix="_blistsvc")
    assert not guest.is_blacklisted

    # Blacklist
    blacklisted_guest = guest_service.blacklist_guest(db=db, guest_id=guest.id, blacklist_status=True)
    assert blacklisted_guest is not None
    assert blacklisted_guest.is_blacklisted

    # Un-blacklist
    unblacklisted_guest = guest_service.blacklist_guest(db=db, guest_id=guest.id, blacklist_status=False)
    assert unblacklisted_guest is not None
    assert not unblacklisted_guest.is_blacklisted

def test_blacklist_nonexistent_guest(db: Session) -> None:
    result = guest_service.blacklist_guest(db=db, guest_id=99999, blacklist_status=True)
    assert result is None
