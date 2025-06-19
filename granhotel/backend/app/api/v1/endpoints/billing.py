from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date
import uuid

from app import schemas, models, services
from app.api import deps
from app.db import session as db_session
from app.models.billing import FolioStatus, FolioTransactionType
from app.models.user import UserRole

router = APIRouter()

FOLIO_NOT_FOUND = "Guest folio not found."
GUEST_NOT_FOUND = "Guest not found." # Added for consistency

@router.get("/folios/guest/{guest_id}", response_model=List[schemas.billing.GuestFolio])
def read_folios_for_guest_api(
    *,
    db: Session = Depends(db_session.get_db),
    guest_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Retrieve all folios for a specific guest.
    Accessible by Receptionist, Manager, Admin.
    '''
    if current_user.role not in [UserRole.RECEPTIONIST, UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view guest folios.")

    # Validate guest existence before fetching folios
    guest = services.guest_service.get_guest(db, guest_id=guest_id)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=GUEST_NOT_FOUND)

    folios = services.billing_service.get_folios_for_guest(db, guest_id=guest_id, skip=skip, limit=limit)
    return folios

@router.post("/folios/guest/{guest_id}/get-or-create", response_model=schemas.billing.GuestFolio)
def get_or_create_folio_for_guest_api(
    *,
    db: Session = Depends(db_session.get_db),
    guest_id: uuid.UUID,
    reservation_id: Optional[int] = Body(None, embed=True),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Get an open folio for a guest (and optionally reservation), or create one if none exists.
    Accessible by Receptionist, Manager, Admin.
    '''
    if current_user.role not in [UserRole.RECEPTIONIST, UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions.")

    # Service function get_or_create_folio_for_guest handles guest/reservation validation
    # and creator_user_id is not strictly needed by service if not auditing folio creation directly.
    # If auditing who initiated this get-or-create action, it could be passed.
    # The service's create_folio part doesn't use creator_user_id.
    folio = services.billing_service.get_or_create_folio_for_guest(
        db, guest_id=guest_id, reservation_id=reservation_id
    )
    return folio


@router.get("/folios/{folio_id}", response_model=schemas.billing.GuestFolio)
def read_folio_details_api(
    *,
    db: Session = Depends(db_session.get_db),
    folio_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Retrieve detailed information for a specific guest folio, including all transactions.
    Accessible by Receptionist (if related to their scope, e.g. guest they are serving), Manager, Admin.
    '''
    # Basic permission check, more granular might be needed if receptionists have limited folio access
    if current_user.role not in [UserRole.RECEPTIONIST, UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view folio details.")

    folio = services.billing_service.get_folio_details(db, folio_id=folio_id)
    if not folio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=FOLIO_NOT_FOUND)

    # Example of more granular access for Receptionist:
    # if current_user.role == UserRole.RECEPTIONIST:
    #     # Check if the folio's guest is somehow linked to the receptionist's current context
    #     # This logic would be complex and depends on operational workflows not yet defined.
    #     # For now, allowing access.
    #     pass
    return folio


@router.post("/folios/{folio_id}/transactions", response_model=schemas.billing.GuestFolio, status_code=status.HTTP_201_CREATED)
def add_transaction_to_folio_api(
    *,
    db: Session = Depends(db_session.get_db),
    folio_id: int,
    transaction_in: schemas.billing.FolioTransactionCreate,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Add a financial transaction (charge or payment) to a guest folio.
    Accessible by Receptionist, Manager, Admin.
    '''
    if current_user.role not in [UserRole.RECEPTIONIST, UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to post transactions.")

    # Service layer handles all validations (folio open, amounts, related entities)
    updated_folio = services.billing_service.add_transaction_to_folio(
        db, folio_id=folio_id, transaction_in=transaction_in, created_by_user_id=current_user.id
    )
    return updated_folio


@router.patch("/folios/{folio_id}/status", response_model=schemas.billing.GuestFolio)
def update_folio_status_api(
    *,
    db: Session = Depends(db_session.get_db),
    folio_id: int,
    status_update_in: schemas.billing.FolioStatusUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user) # Only Manager/Admin can change overall folio status
) -> Any:
    '''
    Update the status of a guest folio (e.g., OPEN, CLOSED, SETTLED, VOIDED).
    Requires Manager or Admin role.
    '''
    # The service update_folio_status does not take updater_user_id currently.
    # If auditing of who changed the status is needed, the service and model need to support it.
    # For now, passing current_user.id for consistency, though service might not use it.
    updated_folio = services.billing_service.update_folio_status(
        db, folio_id=folio_id, new_status=status_update_in.status # Removed updater_user_id as service doesn't take it
    )
    if not updated_folio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=FOLIO_NOT_FOUND)
    return updated_folio
