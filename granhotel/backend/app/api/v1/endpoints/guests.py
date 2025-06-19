from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app import schemas
from app import services # Will use app.services.guest_service
from app.db import session as db_session # Corrected import for get_db
from app.models.guest import DocumentType as GuestDocumentTypeModel # For query param enum

router = APIRouter()

@router.post("/", response_model=schemas.Guest, status_code=status.HTTP_201_CREATED)
def create_new_guest( # Renamed to avoid conflict if importing *
    *,
    db: Session = Depends(db_session.get_db),
    guest_in: schemas.GuestCreate,
) -> Any: # Return type is Any due to FastAPI handling response_model
    '''
    Create a new guest.
    - Validates uniqueness of email and document number.
    - Handles Peruvian document types.
    '''
    # The service layer (create_guest) already handles HTTPException for duplicates
    guest = services.guest_service.create_guest(db=db, guest_in=guest_in)
    return guest

@router.get("/", response_model=List[schemas.Guest])
def read_all_guests( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    first_name: Optional[str] = Query(None, description="Filter by first name (case-insensitive partial match)"),
    last_name: Optional[str] = Query(None, description="Filter by last name (case-insensitive partial match)"),
    document_number: Optional[str] = Query(None, description="Filter by exact document number"),
    email: Optional[str] = Query(None, description="Filter by email (case-insensitive partial match)"),
    is_blacklisted: Optional[bool] = Query(None, description="Filter by blacklist status")
) -> Any:
    '''
    Retrieve a list of guests with optional filters.
    Supports pagination.
    '''
    guests = services.guest_service.get_guests(
        db, skip=skip, limit=limit,
        first_name=first_name, last_name=last_name,
        document_number=document_number, email=email,
        is_blacklisted=is_blacklisted
    )
    return guests

@router.get("/{guest_id}", response_model=schemas.Guest)
def read_single_guest( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    guest_id: int,
) -> Any:
    '''
    Retrieve a specific guest by their ID.
    '''
    guest = services.guest_service.get_guest(db, guest_id=guest_id)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found")
    return guest

@router.put("/{guest_id}", response_model=schemas.Guest)
def update_existing_guest( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    guest_id: int,
    guest_in: schemas.GuestUpdate,
) -> Any:
    '''
    Update an existing guest's information.
    - Checks for uniqueness if email or document number are changed.
    '''
    guest_db_obj = services.guest_service.get_guest(db, guest_id=guest_id)
    if not guest_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found to update")

    # The service layer (update_guest) handles HTTPException for duplicates on changed fields
    updated_guest = services.guest_service.update_guest(db=db, guest_db_obj=guest_db_obj, guest_in=guest_in)
    return updated_guest

@router.delete("/{guest_id}", response_model=schemas.Guest) # Or return a 204 No Content with a simple message
def delete_existing_guest( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    guest_id: int,
) -> Any:
    '''
    Delete a guest by their ID.
    (Currently hard delete)
    '''
    deleted_guest = services.guest_service.delete_guest(db=db, guest_id=guest_id)
    if not deleted_guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found for deletion")
    return deleted_guest # Returns the deleted guest object

@router.patch("/{guest_id}/blacklist", response_model=schemas.Guest)
def toggle_guest_blacklist_status( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    guest_id: int,
    blacklist_status: bool = Query(..., description="Set to true to blacklist, false to unblacklist"),
) -> Any:
    '''
    Set or unset the blacklist status for a guest.
    '''
    # guest_db_obj = services.guest_service.get_guest(db, guest_id=guest_id) # Service handles check
    # if not guest_db_obj:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found to update blacklist status")

    blacklisted_guest = services.guest_service.blacklist_guest(db=db, guest_id=guest_id, blacklist_status=blacklist_status)
    if not blacklisted_guest:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found to update blacklist status")
    return blacklisted_guest
