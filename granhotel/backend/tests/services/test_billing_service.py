import pytest
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import uuid

from app import schemas, services, models
from app.models.billing import FolioStatus, FolioTransactionType
from app.models.user import UserRole
from tests.utils.user import create_user_in_db
from tests.utils.guest import create_random_guest
# from tests.utils.reservations import create_random_reservation # Import if creating folios linked to reservations
# from tests.utils.pos import create_random_pos_sale # Import if linking transactions to POS sales
from tests.utils.billing import create_random_guest_folio, create_random_folio_transaction_data, add_sample_transactions_to_folio
from tests.utils.common import random_lower_string, random_email


def test_recalculate_and_save_folio_totals(db: Session):
    creator = create_user_in_db(db, email=random_email("_recalc_creator"))
    # create_random_guest_folio calls the service which creates a folio
    folio = create_random_guest_folio(db, guest_id=create_random_guest(db, suffix="_recalc").id)

    t1 = models.billing.FolioTransaction(guest_folio_id=folio.id, description="Charge 1", charge_amount=Decimal("100.00"), transaction_type=FolioTransactionType.ROOM_CHARGE, created_by_user_id=creator.id)
    t2 = models.billing.FolioTransaction(guest_folio_id=folio.id, description="Payment 1", payment_amount=Decimal("50.00"), transaction_type=FolioTransactionType.PAYMENT, created_by_user_id=creator.id)
    t3 = models.billing.FolioTransaction(guest_folio_id=folio.id, description="Charge 2", charge_amount=Decimal("25.50"), transaction_type=FolioTransactionType.POS_CHARGE, created_by_user_id=creator.id)
    db.add_all([t1, t2, t3])
    db.commit() # Commit transactions before recalculating

    recalculated_folio = services.billing_service._recalculate_and_save_folio_totals(db, folio.id)
    assert recalculated_folio.total_charges == Decimal("125.50")
    assert recalculated_folio.total_payments == Decimal("50.00")
    assert recalculated_folio.balance == Decimal("75.50")

def test_get_or_create_folio_for_guest_new_folio(db: Session):
    guest = create_random_guest(db, suffix="_goc_new")
    # creator_user_id is not part of get_or_create_folio_for_guest service signature
    folio = services.billing_service.get_or_create_folio_for_guest(db, guest_id=guest.id)
    assert folio is not None
    assert folio.guest_id == guest.id
    assert folio.status == FolioStatus.OPEN
    assert folio.total_charges == Decimal("0.00")
    assert folio.total_payments == Decimal("0.00")

def test_get_or_create_folio_for_guest_existing_open_folio(db: Session):
    # creator_user_id is not needed for create_random_guest_folio as per its definition
    existing_folio = create_random_guest_folio(db)

    fetched_folio = services.billing_service.get_or_create_folio_for_guest(
        db, guest_id=existing_folio.guest_id, reservation_id=existing_folio.reservation_id
    )
    assert fetched_folio is not None
    assert fetched_folio.id == existing_folio.id
    assert fetched_folio.status == FolioStatus.OPEN

def test_add_transaction_to_folio_charge(db: Session):
    creator = create_user_in_db(db, email=random_email("_addtrans_charge_creator"))
    folio = create_random_guest_folio(db)
    initial_charges = folio.total_charges

    transaction_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.SERVICE_CHARGE, amount=Decimal("75.00"))
    updated_folio = services.billing_service.add_transaction_to_folio(db, folio.id, transaction_in, creator.id)

    assert len(updated_folio.transactions) >= 1 # Can be more if folio existed and had transactions
    # Check the last added transaction
    last_transaction = next(t for t in updated_folio.transactions if t.description == transaction_in.description)
    assert last_transaction.charge_amount == Decimal("75.00")
    assert updated_folio.total_charges == initial_charges + Decimal("75.00")
    assert updated_folio.balance == updated_folio.total_charges - updated_folio.total_payments

def test_add_transaction_to_folio_payment(db: Session):
    creator = create_user_in_db(db, email=random_email("_addtrans_pay_creator"))
    folio = create_random_guest_folio(db)

    charge_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.ROOM_CHARGE, amount=Decimal("200.00"))
    services.billing_service.add_transaction_to_folio(db, folio.id, charge_in, creator.id)

    # Re-fetch folio to ensure totals are based on committed state before adding next transaction
    folio_after_charge = services.billing_service.get_folio_details(db, folio.id)
    initial_payments = folio_after_charge.total_payments

    payment_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.PAYMENT, amount=Decimal("100.00"))
    updated_folio_after_payment = services.billing_service.add_transaction_to_folio(db, folio.id, payment_in, creator.id)

    assert len(updated_folio_after_payment.transactions) >= 2
    last_transaction = next(t for t in updated_folio_after_payment.transactions if t.description == payment_in.description)
    assert last_transaction.payment_amount == Decimal("100.00")
    assert updated_folio_after_payment.total_payments == initial_payments + Decimal("100.00")
    assert updated_folio_after_payment.balance == updated_folio_after_payment.total_charges - updated_folio_after_payment.total_payments

def test_add_transaction_to_closed_folio_fail(db: Session):
    creator = create_user_in_db(db, email=random_email("_addtrans_closed_creator"))
    folio = create_random_guest_folio(db)
    # Close the folio using the service
    services.billing_service.update_folio_status(db, folio.id, FolioStatus.CLOSED)
    folio_closed = services.billing_service.get_folio_details(db, folio.id) # Re-fetch
    assert folio_closed.status == FolioStatus.CLOSED

    transaction_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.POS_CHARGE)
    with pytest.raises(HTTPException) as exc_info:
        services.billing_service.add_transaction_to_folio(db, folio.id, transaction_in, creator.id)
    assert exc_info.value.status_code == 400
    assert "not open" in exc_info.value.detail.lower()

def test_get_folio_details_service(db: Session):
    creator = create_user_in_db(db, email=random_email("_getfolio_creator"))
    folio_created = create_random_guest_folio(db)
    add_sample_transactions_to_folio(db, folio_id=folio_created.id, created_by_user_id=creator.id, num_charges=1, num_payments=1)

    folio_details = services.billing_service.get_folio_details(db, folio_id=folio_created.id)
    assert folio_details is not None
    assert folio_details.id == folio_created.id
    assert folio_details.guest is not None
    assert len(folio_details.transactions) == 2
    assert folio_details.transactions[0].created_by is not None

def test_update_folio_status_to_settled_with_balance_fail(db: Session):
    creator = create_user_in_db(db, email=random_email("_updstat_bal_creator"))
    folio = create_random_guest_folio(db)
    add_sample_transactions_to_folio(db, folio.id, creator.id, num_charges=1, num_payments=0)

    folio_with_charge = services.billing_service.get_folio_details(db, folio.id)
    assert folio_with_charge.balance > Decimal("0.00")

    with pytest.raises(HTTPException) as exc_info:
        services.billing_service.update_folio_status(db, folio.id, FolioStatus.SETTLED) # Removed updater_user_id
    assert exc_info.value.status_code == 400
    assert "cannot set to settled until balance is zero" in exc_info.value.detail.lower()

def test_update_folio_status_to_settled_success(db: Session):
    creator = create_user_in_db(db, email=random_email("_updstat_ok_creator"))
    folio = create_random_guest_folio(db)

    # Add a charge
    charge_amount = Decimal("50.00")
    charge_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.ROOM_CHARGE, amount=charge_amount)
    services.billing_service.add_transaction_to_folio(db, folio.id, charge_in, creator.id)

    # Add an equal payment
    payment_in = create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.PAYMENT, amount=charge_amount)
    services.billing_service.add_transaction_to_folio(db, folio.id, payment_in, creator.id)

    folio_balanced = services.billing_service.get_folio_details(db, folio.id)
    assert folio_balanced.balance == Decimal("0.00")

    settled_folio = services.billing_service.update_folio_status(db, folio.id, FolioStatus.SETTLED) # Removed updater_user_id
    assert settled_folio.status == FolioStatus.SETTLED
    assert settled_folio.closed_at is not None

def test_get_folios_for_guest_service(db: Session):
    guest = create_random_guest(db, suffix="_getfolios_g")
    creator = create_user_in_db(db, email=random_email("_getfolios_c"))

    folio1 = create_random_guest_folio(db, guest_id=guest.id)
    services.billing_service.update_folio_status(db, folio1.id, FolioStatus.SETTLED)

    folio2 = create_random_guest_folio(db, guest_id=guest.id) # New open folio

    folios = services.billing_service.get_folios_for_guest(db, guest_id=guest.id)
    assert len(folios) >= 2
    assert any(f.id == folio1.id and f.status == FolioStatus.SETTLED for f in folios)
    assert any(f.id == folio2.id and f.status == FolioStatus.OPEN for f in folios)
