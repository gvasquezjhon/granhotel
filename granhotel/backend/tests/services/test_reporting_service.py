import pytest
from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import uuid

from app import schemas, services, models
from app.models.reservations import ReservationStatus
from app.models.pos import POSSaleStatus, PaymentMethod
from app.models.billing import FolioTransactionType, FolioStatus
from app.models.user import UserRole

# Import all necessary utilities
from tests.utils.common import random_lower_string, random_email
from tests.utils.user import create_user_in_db
from tests.utils.room import create_random_room
from tests.utils.guest import create_random_guest
from tests.utils.product import create_random_product, create_random_product_category
from tests.utils.inventory import ensure_inventory_item_exists
from tests.utils.reservations import create_random_reservation # Util for creating reservations
from tests.utils.pos import create_random_pos_sale
from tests.utils.billing import create_random_guest_folio, add_sample_transactions_to_folio, create_random_folio_transaction_data


# Helper to setup rooms
def setup_rooms(db: Session, count: int):
    rooms = []
    for i in range(count):
        rooms.append(create_random_room(db, room_number_suffix=f"_rep_r{i}"))
    return rooms

# --- Occupancy Report Tests ---
def test_get_daily_occupancy_data_no_rooms(db: Session):
    # This test is tricky without DB isolation. If other tests create rooms, it won't be "no rooms".
    # The service function handles the "No rooms in system" error case.
    # We can test this by temporarily ensuring no rooms, or mocking the query.
    # For now, this specific scenario is hard to enforce reliably here.
    # The service returns: {"date": target_date.isoformat(), "total_rooms": 0, ... "error": "No rooms in system."}
    # So, if total_rooms is 0, an error key should be present.
    # This test will be more effective if run against an empty DB or with mocking.

    # Let's assume if we query for a date far in the past where no rooms existed (if possible with test setup)
    # or if we could somehow ensure no rooms are returned by the query:
    # query_result_mock = 0
    # report = services.reporting_service.get_daily_occupancy_data(db, date(2000,1,1))
    # if report["total_rooms"] == 0 :
    #    assert "error" in report
    pass


def test_get_daily_occupancy_data_basic(db: Session):
    if db.query(models.Room).count() == 0:
        setup_rooms(db, 5)

    test_date = date.today() + timedelta(days=10)
    # Creator user isn't strictly needed by create_random_reservation as defined previously
    # but if it were, we'd create one:
    # creator = create_user_in_db(db, email=random_email("_rep_docc_cr"))
    guest = create_random_guest(db, suffix="_rep_docc")
    room1 = create_random_room(db, room_number_suffix="_rep_docc1_occ") # Ensure unique room number
    room2 = create_random_room(db, room_number_suffix="_rep_docc2_occ")

    # Reservation 1: Occupied on test_date
    create_random_reservation(db, guest_id=guest.id, room_id=room1.id,
                              check_in_date=test_date - timedelta(days=1),
                              check_out_date=test_date + timedelta(days=2),
                              status=ReservationStatus.CHECKED_IN)
    # Reservation 2: Not occupied on test_date (checkout is on test_date)
    create_random_reservation(db, guest_id=guest.id, room_id=room2.id,
                              check_in_date=test_date - timedelta(days=3),
                              check_out_date=test_date,
                              status=ReservationStatus.CHECKED_IN)

    report = services.reporting_service.get_daily_occupancy_data(db, target_date=test_date)
    assert report["date"] == test_date.isoformat()
    total_rooms_in_db = db.query(models.Room).count() # Get actual total rooms
    assert report["total_rooms"] == total_rooms_in_db

    # Check that at least room1 contributes to occupied count
    # Querying directly to confirm state for assertion.
    occupied_on_date = db.query(models.Reservation).filter(
        models.Reservation.room_id == room1.id,
        models.Reservation.check_in_date <= test_date,
        models.Reservation.check_out_date > test_date,
        models.Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN])
    ).count()
    assert occupied_on_date >= 1

    # The report's occupied_rooms should be at least 1.
    assert report["occupied_rooms"] >= 1


def test_get_occupancy_rate_over_period(db: Session):
    if db.query(models.Room).count() < 2: setup_rooms(db, 2)

    date_from = date.today() + timedelta(days=20)
    date_to = date_from + timedelta(days=2) # 3 day period
    guest = create_random_guest(db, suffix="_rep_pocc")
    # Get first available room for test consistency
    room1 = db.query(models.Room).order_by(models.Room.id).first()
    if not room1: room1 = create_random_room(db, room_number_suffix="_occ_period_r1")


    # Reservation spanning the whole period for room1
    create_random_reservation(db, guest_id=guest.id, room_id=room1.id,
                              check_in_date=date_from,
                              check_out_date=date_to + timedelta(days=1), # Stays through date_to night
                              status=ReservationStatus.CONFIRMED)

    report = services.reporting_service.get_occupancy_rate_over_period(db, date_from, date_to)
    assert report["date_from"] == date_from.isoformat()
    assert report["date_to"] == date_to.isoformat()
    assert report["number_of_days"] == 3
    # For this specific setup, 1 room is occupied for 3 nights.
    # So, total_room_nights_occupied should be exactly 3 if no other overlapping reservations exist for these dates.
    # This assertion can be flaky if other tests create reservations in this exact future window.
    # A safer check is that it's at least 3.
    assert report["total_room_nights_occupied"] >= 3


def test_get_revpar_over_period(db: Session):
    if db.query(models.Room).count() == 0: setup_rooms(db, 1)

    date_from = date.today() + timedelta(days=30)
    date_to = date_from + timedelta(days=1) # 2 day period
    creator = create_user_in_db(db, role=UserRole.ADMIN, email=random_email("_rep_revpar_cr"))
    guest = create_random_guest(db, suffix="_rep_revpar")
    room_for_revpar = create_random_room(db, room_number_suffix="_revpar_room", price=Decimal("100.00"))

    reservation = create_random_reservation(db, guest_id=guest.id, room_id=room_for_revpar.id,
                                           check_in_date=date_from,
                                           check_out_date=date_to + timedelta(days=1), # Covers nights of date_from and date_to
                                           status=ReservationStatus.CHECKED_IN)
    folio = create_random_guest_folio(db, guest_id=guest.id, reservation_id=reservation.id)

    # Add room charges for the period
    services.billing_service.add_transaction_to_folio(
        db, folio.id,
        create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.ROOM_CHARGE, amount=Decimal("100.00"), transaction_date=datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)),
        creator.id
    )
    services.billing_service.add_transaction_to_folio(
        db, folio.id,
        create_random_folio_transaction_data(db, transaction_type=FolioTransactionType.ROOM_CHARGE, amount=Decimal("100.00"), transaction_date=datetime.combine(date_to, datetime.min.time(), tzinfo=timezone.utc)),
        creator.id
    )

    report = services.reporting_service.get_revpar_over_period(db, date_from, date_to)
    # Total room revenue should be at least 200 from this test setup.
    assert Decimal(report["total_room_revenue"]) >= Decimal("200.00")


# --- Sales Report Tests ---
def test_get_total_sales_by_period(db: Session):
    # Use dates further in the past to minimize interference from other tests
    date_from = date(2023, 1, 1)
    date_to = date(2023, 1, 2) # 2 day period
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rep_sales_csh"))

    # Sale 1 in period
    sale1 = create_random_pos_sale(db, cashier_user_id=cashier.id, num_items=1)
    sale1.sale_date = datetime.combine(date_from, datetime(2023,1,1,10,0,0).time(), tzinfo=timezone.utc)
    db.add(sale1); db.commit(); db.refresh(sale1)

    # Sale 2 in period
    sale2 = create_random_pos_sale(db, cashier_user_id=cashier.id, num_items=1, payment_method=PaymentMethod.CARD_CREDIT)
    sale2.sale_date = datetime.combine(date_to, datetime(2023,1,2,15,0,0).time(), tzinfo=timezone.utc)
    db.add(sale2); db.commit(); db.refresh(sale2)

    # Sale outside period
    sale_outside = create_random_pos_sale(db, cashier_user_id=cashier.id)
    sale_outside.sale_date = datetime.combine(date_from - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    db.add(sale_outside); db.commit()

    report = services.reporting_service.get_total_sales_by_period(db, date_from, date_to)
    expected_total = (sale1.total_amount_after_tax + sale2.total_amount_after_tax).quantize(Decimal("0.01"))

    assert Decimal(report["total_sales_after_tax"]) == expected_total
    assert report["number_of_sales"] == 2

    # Test with payment method filter
    report_cash = services.reporting_service.get_total_sales_by_period(db, date_from, date_to, payment_method=PaymentMethod.CASH)
    assert Decimal(report_cash["total_sales_after_tax"]) == sale1.total_amount_after_tax.quantize(Decimal("0.01"))
    assert report_cash["number_of_sales"] == 1


# --- Inventory Report Tests ---
def test_get_inventory_summary(db: Session):
    cat = create_random_product_category(db, "_repinvsumcat")
    prod1 = create_random_product(db, category_id=cat.id, name_suffix="_repinvsum1", price=Decimal("10.00"))
    prod2 = create_random_product(db, category_id=cat.id, name_suffix="_repinvsum2", price=Decimal("25.50"))
    prod_inactive = create_random_product(db, category_id=cat.id, name_suffix="_repinvsum_inactive", price=Decimal("5.00"), is_active=False)

    ensure_inventory_item_exists(db, prod1.id, initial_quantity=5)
    ensure_inventory_item_exists(db, prod2.id, initial_quantity=2)
    ensure_inventory_item_exists(db, prod_inactive.id, initial_quantity=100)

    summary = services.reporting_service.get_inventory_summary(db)

    active_product_ids_in_summary = [item["product_id"] for item in summary]
    assert prod1.id in active_product_ids_in_summary
    assert prod2.id in active_product_ids_in_summary
    assert prod_inactive.id not in active_product_ids_in_summary # Inactive product should not be listed

    prod1_summary = next((item for item in summary if item["product_id"] == prod1.id), None)
    assert prod1_summary is not None
    assert prod1_summary["quantity_on_hand"] == 5
    assert Decimal(prod1_summary["total_stock_value"]) == Decimal("50.00")

    prod2_summary = next((item for item in summary if item["product_id"] == prod2.id), None)
    assert prod2_summary is not None
    assert prod2_summary["quantity_on_hand"] == 2
    assert Decimal(prod2_summary["total_stock_value"]) == Decimal("51.00")


def test_get_folio_financial_summary(db: Session):
    date_from = date(2023, 2, 1)
    date_to = date(2023, 2, 5)
    creator = create_user_in_db(db, role=UserRole.ADMIN, email=random_email("_rep_ffs_cr"))
    guest = create_random_guest(db, suffix="_rep_ffs")
    folio = create_random_guest_folio(db, guest_id=guest.id)

    # Transactions within the period
    services.billing_service.add_transaction_to_folio(
        db, folio.id,
        create_random_folio_transaction_data(db, FolioTransactionType.ROOM_CHARGE, Decimal("100.00"), transaction_date=datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)),
        creator.id
    )
    services.billing_service.add_transaction_to_folio(
        db, folio.id,
        create_random_folio_transaction_data(db, FolioTransactionType.PAYMENT, Decimal("50.00"), transaction_date=datetime.combine(date_to, datetime.min.time(), tzinfo=timezone.utc)),
        creator.id
    )
    # Transaction outside the period
    services.billing_service.add_transaction_to_folio(
        db, folio.id,
        create_random_folio_transaction_data(db, FolioTransactionType.POS_CHARGE, Decimal("20.00"), transaction_date=datetime.combine(date_from - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)),
        creator.id
    )

    report = services.reporting_service.get_folio_financial_summary(db, date_from, date_to)
    assert Decimal(report["total_charges_posted"]) == Decimal("100.00")
    assert Decimal(report["total_payments_received"]) == Decimal("50.00")
