from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func as sql_func
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app import models
from app import schemas
from app.models.billing import GuestFolio, FolioTransaction, FolioStatus, FolioTransactionType
from app.models.guest import Guest
from app.models.reservations import Reservation
from app.models.pos import POSSale
from app.models.user import User
from app.services import guest_service, reservation_service, pos_service # Removed user_service, not directly used
from fastapi import HTTPException, status

def _recalculate_and_save_folio_totals(db: Session, folio_id: int) -> models.billing.GuestFolio:
    # Use a subquery to get the folio to avoid issues with already loaded relationships if any
    folio = db.query(models.billing.GuestFolio).filter(models.billing.GuestFolio.id == folio_id).first()
    if not folio:
        # This is an internal function, so a ValueError might be more appropriate if folio_id is expected to be valid
        raise ValueError(f"Folio with ID {folio_id} not found for recalculation.")

    sum_charges = db.query(sql_func.sum(models.billing.FolioTransaction.charge_amount)).filter(
        models.billing.FolioTransaction.guest_folio_id == folio_id
    ).scalar() or Decimal("0.00")

    sum_payments = db.query(sql_func.sum(models.billing.FolioTransaction.payment_amount)).filter(
        models.billing.FolioTransaction.guest_folio_id == folio_id
    ).scalar() or Decimal("0.00")

    folio.total_charges = sum_charges
    folio.total_payments = sum_payments

    db.add(folio) # Add to session to mark as dirty
    # The commit should happen in the calling function to ensure atomicity with transaction add/update
    # For now, let's commit here as this function is called after a transaction is already committed.
    # This could be refactored for better transaction control.
    db.commit()
    db.refresh(folio)
    return folio


def get_folio_details(db: Session, folio_id: int) -> Optional[models.billing.GuestFolio]:
    # This function is used by others, so it needs to be defined before them or forward declared.
    # Python handles this fine if not type hinting return of this in the functions above it.
    # For explicit typing, it should be defined first.
    return db.query(models.billing.GuestFolio).options(
        joinedload(models.billing.GuestFolio.guest),
        joinedload(models.billing.GuestFolio.reservation).options(
            selectinload(models.reservations.Reservation.room)
        ),
        selectinload(models.billing.GuestFolio.transactions).options(
            joinedload(models.billing.FolioTransaction.created_by),
            joinedload(models.billing.FolioTransaction.pos_sale),
            joinedload(models.billing.FolioTransaction.reservation_ref)
        )
    ).filter(models.billing.GuestFolio.id == folio_id).first()


def get_or_create_folio_for_guest(
    db: Session, guest_id: uuid.UUID, reservation_id: Optional[int] = None
    # creator_user_id is not used in this function's current logic
) -> models.billing.GuestFolio:
    guest = guest_service.get_guest(db, guest_id) # Uses schemas.UUID for guest_id, model uses uuid.UUID
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Guest with ID {guest_id} not found.")

    query = db.query(models.billing.GuestFolio).filter(
        models.billing.GuestFolio.guest_id == guest_id, # guest_id is UUID in model
        models.billing.GuestFolio.status == FolioStatus.OPEN
    )
    if reservation_id:
        reservation = reservation_service.get_reservation(db, reservation_id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation with ID {reservation_id} not found.")
        if str(reservation.guest_id) != str(guest_id): # Compare as string to be safe with UUID types
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Reservation ID {reservation_id} does not belong to Guest ID {guest_id}.")
        query = query.filter(models.billing.GuestFolio.reservation_id == reservation_id)

    existing_open_folio = query.order_by(models.billing.GuestFolio.opened_at.desc()).first() # Get most recent open
    if existing_open_folio:
        return get_folio_details(db, existing_open_folio.id) # Return full details

    new_folio = models.billing.GuestFolio(
        guest_id=guest_id,
        reservation_id=reservation_id,
        status=FolioStatus.OPEN,
        # total_charges and total_payments default to 0.00 in model
        # opened_at defaults to now() in model
    )
    db.add(new_folio)
    db.commit()
    db.refresh(new_folio)
    return get_folio_details(db, new_folio.id) # Return full details


def add_transaction_to_folio(
    db: Session,
    folio_id: int,
    transaction_in: schemas.billing.FolioTransactionCreate,
    created_by_user_id: uuid.UUID
) -> models.billing.GuestFolio:
    # Fetch folio without all transactions first to check status
    folio = db.query(models.billing.GuestFolio).filter(models.billing.GuestFolio.id == folio_id).first()
    if not folio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Folio with ID {folio_id} not found.")

    if folio.status != FolioStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Folio ID {folio_id} is not OPEN. Cannot add new transactions.")

    if transaction_in.charge_amount < Decimal("0.00") or transaction_in.payment_amount < Decimal("0.00"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Charge and payment amounts cannot be negative.")
    if transaction_in.charge_amount > Decimal("0.00") and transaction_in.payment_amount > Decimal("0.00"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction cannot be both a charge and a payment simultaneously.")

    # Allow zero amount for specific types like DISCOUNT_ADJUSTMENT if needed, or for pure informational entries
    # This check is based on Pydantic model_validator which was simplified; service must enforce.
    is_adjustment_or_note = transaction_in.transaction_type in [FolioTransactionType.DISCOUNT_ADJUSTMENT] # Add other types if they can be zero
    if transaction_in.charge_amount == Decimal("0.00") and transaction_in.payment_amount == Decimal("0.00") and not is_adjustment_or_note:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction amount (charge or payment) must be specified and non-zero for most types.")


    if transaction_in.related_pos_sale_id:
        pos_sale = pos_service.get_pos_sale(db, transaction_in.related_pos_sale_id)
        if not pos_sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Related POS Sale ID {transaction_in.related_pos_sale_id} not found.")

    if transaction_in.related_reservation_id:
        reservation = reservation_service.get_reservation(db, transaction_in.related_reservation_id)
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Related Reservation ID {transaction_in.related_reservation_id} not found.")

    transaction_data = transaction_in.model_dump()
    if transaction_data.get("transaction_date") is None:
        transaction_data["transaction_date"] = datetime.now(timezone.utc)

    new_transaction = models.billing.FolioTransaction(
        **transaction_data,
        guest_folio_id=folio_id,
        created_by_user_id=created_by_user_id
    )
    db.add(new_transaction)
    # Important: Commit the new transaction before recalculating totals.
    # _recalculate_and_save_folio_totals itself commits.
    db.commit()
    # db.refresh(new_transaction) # Not strictly needed if not immediately using it before recalculate

    updated_folio = _recalculate_and_save_folio_totals(db, folio_id)
    return get_folio_details(db, updated_folio.id) # Return with all joins


def get_folios_for_guest(db: Session, guest_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.billing.GuestFolio]:
    # Guest ID is UUID in model, ensure comparison is correct
    return db.query(models.billing.GuestFolio).filter(
        models.billing.GuestFolio.guest_id == guest_id
    ).order_by(models.billing.GuestFolio.opened_at.desc()).offset(skip).limit(limit).all()


def update_folio_status(
    db: Session, folio_id: int, new_status: FolioStatus # updater_user_id not used in this func
) -> Optional[models.billing.GuestFolio]:
    folio = get_folio_details(db, folio_id)
    if not folio:
        return None

    if new_status == FolioStatus.SETTLED and folio.balance != Decimal("0.00"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Folio balance is {folio.balance:.2f}. Cannot set to SETTLED until balance is zero.")

    if new_status in [FolioStatus.CLOSED, FolioStatus.SETTLED, FolioStatus.VOIDED] and not folio.closed_at:
        folio.closed_at = datetime.now(timezone.utc)
    elif new_status == FolioStatus.OPEN: # Re-opening a folio
        folio.closed_at = None

    folio.status = new_status
    # folio.updated_by_user_id = updater_user_id # Model for GuestFolio doesn't have updated_by_user_id
    db.add(folio)
    db.commit()
    db.refresh(folio)
    return get_folio_details(db, folio.id)
