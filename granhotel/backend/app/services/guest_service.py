from sqlalchemy.orm import Session
from typing import List, Optional, Any
from fastapi import HTTPException, status

from app import models
from app import schemas
from app.models.guest import Guest # Explicit import for clarity
from app.schemas.guest import GuestCreate, GuestUpdate # Explicit import

def get_guest(db: Session, guest_id: int) -> Optional[models.Guest]:
    '''
    Retrieve a guest by their ID.
    '''
    return db.query(models.Guest).filter(models.Guest.id == guest_id).first()

def get_guest_by_email(db: Session, email: str) -> Optional[models.Guest]:
    '''
    Retrieve a guest by their email address.
    '''
    return db.query(models.Guest).filter(models.Guest.email == email).first()

def get_guest_by_document_number(db: Session, document_number: str) -> Optional[models.Guest]:
    '''
    Retrieve a guest by their document number.
    '''
    return db.query(models.Guest).filter(models.Guest.document_number == document_number).first()

def get_guests(
    db: Session, skip: int = 0, limit: int = 100,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    document_number: Optional[str] = None,
    email: Optional[str] = None,
    is_blacklisted: Optional[bool] = None
) -> List[models.Guest]:
    '''
    Retrieve a list of guests with optional filtering.
    '''
    query = db.query(models.Guest)

    if first_name:
        query = query.filter(models.Guest.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(models.Guest.last_name.ilike(f"%{last_name}%"))
    if document_number:
        query = query.filter(models.Guest.document_number == document_number)
    if email:
        query = query.filter(models.Guest.email.ilike(f"%{email}%")) # ilike for partial email search
    if is_blacklisted is not None:
        query = query.filter(models.Guest.is_blacklisted == is_blacklisted)

    return query.order_by(models.Guest.last_name, models.Guest.first_name).offset(skip).limit(limit).all()

def create_guest(db: Session, guest_in: schemas.GuestCreate) -> models.Guest:
    '''
    Create a new guest.
    Checks for uniqueness of email and document_number if provided.
    '''
    if guest_in.email:
        existing_guest_email = get_guest_by_email(db, email=guest_in.email)
        if existing_guest_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Guest with email '{guest_in.email}' already exists."
            )

    if guest_in.document_number:
        existing_guest_doc = get_guest_by_document_number(db, document_number=guest_in.document_number)
        if existing_guest_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Guest with document number '{guest_in.document_number}' already exists."
            )

    db_guest = models.Guest(**guest_in.model_dump())
    # created_at and updated_at are handled by server_default and onupdate
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest

def update_guest(db: Session, guest_db_obj: models.Guest, guest_in: schemas.GuestUpdate) -> models.Guest:
    '''
    Update an existing guest.
    Checks for uniqueness if email or document_number are being changed.
    '''
    update_data = guest_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != guest_db_obj.email:
        if update_data["email"] is not None: # Ensure we don't check None against existing emails
            existing_guest_email = get_guest_by_email(db, email=update_data["email"])
            if existing_guest_email and existing_guest_email.id != guest_db_obj.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another guest with email '{update_data['email']}' already exists."
                )

    if "document_number" in update_data and update_data["document_number"] != guest_db_obj.document_number:
        if update_data["document_number"] is not None: # Ensure we don't check None
            existing_guest_doc = get_guest_by_document_number(db, document_number=update_data["document_number"])
            if existing_guest_doc and existing_guest_doc.id != guest_db_obj.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another guest with document number '{update_data['document_number']}' already exists."
                )

    for field, value in update_data.items():
        if hasattr(guest_db_obj, field):
            setattr(guest_db_obj, field, value)

    # updated_at is handled by onupdate=func.now() in the model
    db.add(guest_db_obj)
    db.commit()
    db.refresh(guest_db_obj)
    return guest_db_obj

def delete_guest(db: Session, guest_id: int) -> Optional[models.Guest]:
    '''
    Delete a guest (hard delete for now, consider soft delete later).
    If implementing soft delete, this would set an `is_deleted` flag.
    '''
    guest_to_delete = get_guest(db, guest_id=guest_id)
    if guest_to_delete:
        # For soft delete:
        # guest_to_delete.is_deleted = True
        # guest_to_delete.deleted_at = func.now()
        # db.commit()
        # db.refresh(guest_to_delete)
        db.delete(guest_to_delete)
        db.commit()
    return guest_to_delete


def blacklist_guest(db: Session, guest_id: int, blacklist_status: bool = True) -> Optional[models.Guest]:
    '''
    Set or unset the blacklist status for a guest.
    '''
    guest_to_update = get_guest(db, guest_id=guest_id)
    if not guest_to_update:
        # Return None, the API layer can decide to raise HTTPException
        return None

    guest_to_update.is_blacklisted = blacklist_status
    # updated_at should be triggered by the model's onupdate
    db.add(guest_to_update)
    db.commit()
    db.refresh(guest_to_update)
    return guest_to_update
