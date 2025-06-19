from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from datetime import date, timedelta, datetime, timezone
import random
import uuid

from app import models, schemas, services
from app.models.billing import FolioStatus, FolioTransactionType
from app.models.user import UserRole
from tests.utils.user import create_user_in_db
from tests.utils.guest import create_random_guest
# from tests.utils.reservations import create_random_reservation # Only if needed for linked reservation
from tests.utils.common import random_lower_string

def create_random_folio_transaction_data(
    db: Session, # db session might not be needed if not creating related entities here
    transaction_type: FolioTransactionType,
    amount: Optional[Decimal] = None,
    description_suffix: str = "",
    related_pos_sale_id: Optional[int] = None,
    related_reservation_id: Optional[int] = None
) -> schemas.billing.FolioTransactionCreate:
    '''
    Generates a FolioTransactionCreate schema.
    Manages charge_amount vs payment_amount based on transaction_type and schema constraints (ge=0).
    '''
    charge_amt = Decimal("0.00")
    payment_amt = Decimal("0.00")

    rand_amount = amount if amount is not None else Decimal(str(random.uniform(10.0, 100.0))).quantize(Decimal("0.01"))

    if transaction_type in [
        FolioTransactionType.ROOM_CHARGE,
        FolioTransactionType.POS_CHARGE,
        FolioTransactionType.SERVICE_CHARGE,
        FolioTransactionType.TAX_CHARGE
    ]:
        charge_amt = rand_amount
    elif transaction_type == FolioTransactionType.PAYMENT:
        payment_amt = rand_amount
    elif transaction_type == FolioTransactionType.REFUND:
        # Per schema (payment_amount >= 0), a refund is a positive value in payment_amount.
        # The service/accounting logic must interpret this as money out from hotel.
        payment_amt = rand_amount
    elif transaction_type == FolioTransactionType.DISCOUNT_ADJUSTMENT:
        # Per schema (charge_amount >= 0), a discount is a positive value in charge_amount.
        # The service/accounting logic must interpret this as a reduction of what guest owes.
        charge_amt = rand_amount

        # If a discount could be zero value (e.g. just a note), this is fine.
        # Otherwise, ensure rand_amount > 0 if amount is None for these types.
        if charge_amt == Decimal("0.00") and payment_amt == Decimal("0.00"): # Ensure adjustments have value
             charge_amt = Decimal(str(random.uniform(5.0, 50.0))).quantize(Decimal("0.01"))


    desc = f"{transaction_type.value.replace('_', ' ')} {description_suffix} {random_lower_string(3)}"

    return schemas.billing.FolioTransactionCreate(
        description=desc,
        charge_amount=charge_amt,
        payment_amount=payment_amt,
        transaction_type=transaction_type,
        related_pos_sale_id=related_pos_sale_id,
        related_reservation_id=related_reservation_id,
        transaction_date=datetime.now(timezone.utc) # Set explicitly for predictability in tests
    )


def create_random_guest_folio(
    db: Session,
    guest_id: Optional[uuid.UUID] = None,
    reservation_id: Optional[int] = None
    # creator_user_id is not taken by the service get_or_create_folio_for_guest
) -> models.billing.GuestFolio:
    '''
    Creates or retrieves an open GuestFolio using the get_or_create_folio_for_guest service function.
    '''
    if guest_id is None:
        guest_obj = create_random_guest(db, suffix=f"_folio_util{random_lower_string(2)}")
        guest_id = guest_obj.id

    # The service function get_or_create_folio_for_guest handles creation if no open folio exists.
    # It does not require creator_user_id.
    return services.billing_service.get_or_create_folio_for_guest(
        db, guest_id=guest_id, reservation_id=reservation_id
    )

def add_sample_transactions_to_folio(
    db: Session,
    folio_id: int,
    created_by_user_id: uuid.UUID,
    num_charges: int = 2,
    num_payments: int = 1
) -> models.billing.GuestFolio:
    '''Adds a number of sample charge and payment transactions to a folio.'''
    for _ in range(num_charges):
        charge_type = random.choice([
            FolioTransactionType.POS_CHARGE,
            FolioTransactionType.SERVICE_CHARGE,
            FolioTransactionType.ROOM_CHARGE
        ])
        transaction_charge_in = create_random_folio_transaction_data(db, transaction_type=charge_type)
        services.billing_service.add_transaction_to_folio(db, folio_id, transaction_charge_in, created_by_user_id)

    for _ in range(num_payments):
        transaction_payment_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.PAYMENT)
        services.billing_service.add_transaction_to_folio(db, folio_id, transaction_payment_in, created_by_user_id)

    return services.billing_service.get_folio_details(db, folio_id)
