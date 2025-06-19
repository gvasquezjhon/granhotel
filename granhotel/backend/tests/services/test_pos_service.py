import pytest
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from datetime import date, timedelta, datetime
from decimal import Decimal
import uuid

from app import schemas, services, models
from app.models.pos import POSSaleStatus, PaymentMethod
from app.models.inventory import StockMovementType
from app.models.user import UserRole
from tests.utils.user import create_user_in_db
from tests.utils.product import create_random_product
from tests.utils.guest import create_random_guest
from tests.utils.inventory import ensure_inventory_item_exists
from tests.utils.pos import create_random_pos_sale # Utility to create a full sale via service
from tests.utils.common import random_lower_string, random_email


def test_create_pos_sale_service_success(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_cps"))
    guest = create_random_guest(db, suffix="_cps_guest")
    product1 = create_random_product(db, name_suffix="_cps_p1", price=Decimal("10.00"), taxable=True)
    product2 = create_random_product(db, name_suffix="_cps_p2", price=Decimal("5.50"), taxable=False)

    ensure_inventory_item_exists(db, product1.id, initial_quantity=20)
    ensure_inventory_item_exists(db, product2.id, initial_quantity=10)

    sale_items_in = [
        schemas.pos.POSSaleItemCreate(product_id=product1.id, quantity=2),
        schemas.pos.POSSaleItemCreate(product_id=product2.id, quantity=3)
    ]
    sale_in_schema = schemas.pos.POSSaleCreate(
        guest_id=guest.id,
        payment_method=PaymentMethod.CARD_CREDIT,
        items=sale_items_in,
        notes="Test successful sale"
    )

    pos_sale = services.pos_service.create_pos_sale(db, sale_in=sale_in_schema, cashier_user_id=cashier.id)

    assert pos_sale is not None
    assert pos_sale.cashier_user_id == cashier.id
    assert pos_sale.guest_id == guest.id
    assert len(pos_sale.items) == 2
    assert pos_sale.status == POSSaleStatus.COMPLETED

    # Item1: price_before_tax = 10.00 * 2 = 20.00. tax = 20.00 * 0.18 = 3.60. total = 23.60
    # Item2: price_before_tax =  5.50 * 3 = 16.50. tax = 0.00. total = 16.50
    expected_total_before_tax = Decimal("20.00") + Decimal("16.50")
    expected_tax_amount = Decimal("3.60")
    expected_total_after_tax = expected_total_before_tax + expected_tax_amount

    assert pos_sale.total_amount_before_tax == expected_total_before_tax
    assert pos_sale.tax_amount == expected_tax_amount
    assert pos_sale.total_amount_after_tax == expected_total_after_tax

    inv_item1 = services.inventory_service.get_inventory_item_by_product_id(db, product1.id)
    assert inv_item1.quantity_on_hand == 20 - 2
    hist1 = services.inventory_service.get_stock_movement_history(db, product1.id, movement_type=StockMovementType.SALE)
    assert len(hist1) >= 1 # Can be more if product used in other tests, check for specific one
    assert any(h.quantity_changed == -2 and h.reason and str(pos_sale.id) in h.reason for h in hist1)

    inv_item2 = services.inventory_service.get_inventory_item_by_product_id(db, product2.id)
    assert inv_item2.quantity_on_hand == 10 - 3
    hist2 = services.inventory_service.get_stock_movement_history(db, product2.id, movement_type=StockMovementType.SALE)
    assert len(hist2) >= 1
    assert any(h.quantity_changed == -3 and h.reason and str(pos_sale.id) in h.reason for h in hist2)


def test_create_pos_sale_insufficient_stock_fail(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_cps_is"))
    product_low_stock = create_random_product(db, name_suffix="_cps_p_low_stock")
    ensure_inventory_item_exists(db, product_low_stock.id, initial_quantity=1)

    sale_items_in = [schemas.pos.POSSaleItemCreate(product_id=product_low_stock.id, quantity=2)]
    sale_in_schema = schemas.pos.POSSaleCreate(payment_method=PaymentMethod.CASH, items=sale_items_in)

    with pytest.raises(HTTPException) as exc_info:
        services.pos_service.create_pos_sale(db, sale_in=sale_in_schema, cashier_user_id=cashier.id)
    assert exc_info.value.status_code == 400
    assert "insufficient stock" in exc_info.value.detail.lower()


def test_create_pos_sale_room_charge_no_guest_fail(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_cps_rcng"))
    product = create_random_product(db, name_suffix="_cps_p_rcng")
    ensure_inventory_item_exists(db, product.id, initial_quantity=5)

    sale_items_in = [schemas.pos.POSSaleItemCreate(product_id=product.id, quantity=1)]
    sale_in_schema = schemas.pos.POSSaleCreate(
        payment_method=PaymentMethod.ROOM_CHARGE,
        guest_id=None,
        items=sale_items_in
    )
    with pytest.raises(HTTPException) as exc_info:
        services.pos_service.create_pos_sale(db, sale_in=sale_in_schema, cashier_user_id=cashier.id)
    assert exc_info.value.status_code == 400
    assert "guest id is required for room charge" in exc_info.value.detail.lower()

def test_get_pos_sale_service(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_gps"))
    sale_created = create_random_pos_sale(db, cashier_user_id=cashier.id, num_items=1)

    sale_fetched = services.pos_service.get_pos_sale(db, sale_id=sale_created.id)
    assert sale_fetched is not None
    assert sale_fetched.id == sale_created.id
    assert sale_fetched.cashier is not None
    assert len(sale_fetched.items) == 1
    assert sale_fetched.items[0].product is not None
    assert sale_fetched.items[0].product.category is not None

def test_get_pos_sales_filtering(db: Session):
    cashier1 = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier1_gpsf"))
    cashier2 = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier2_gpsf"))
    guest1 = create_random_guest(db, suffix="_gpsf_g1")

    create_random_pos_sale(db, cashier_user_id=cashier1.id, guest_id=guest1.id, payment_method=PaymentMethod.CASH, status=POSSaleStatus.COMPLETED)
    create_random_pos_sale(db, cashier_user_id=cashier2.id, payment_method=PaymentMethod.CARD_CREDIT, status=POSSaleStatus.COMPLETED)
    # The create_random_pos_sale utility calls the service which defaults status to COMPLETED.
    # To test voided status, we need to void a sale first.
    sale_to_void = create_random_pos_sale(db, cashier_user_id=cashier1.id)
    services.pos_service.void_pos_sale(db, sale_to_void.id, "Test void for filter", cashier1.id)


    all_sales = services.pos_service.get_pos_sales(db, limit=10)
    assert len(all_sales) >= 3

    sales_c1 = services.pos_service.get_pos_sales(db, cashier_user_id=cashier1.id)
    assert len(sales_c1) >= 2 # Two completed, one voided by cashier1
    assert all(s.cashier_user_id == cashier1.id for s in sales_c1)

    sales_completed = services.pos_service.get_pos_sales(db, status=POSSaleStatus.COMPLETED)
    assert len(sales_completed) >= 2 # Original two completed sales
    assert all(s.status == POSSaleStatus.COMPLETED for s in sales_completed)

    sales_g1 = services.pos_service.get_pos_sales(db, guest_id=guest1.id)
    assert len(sales_g1) >= 1
    assert all(s.guest_id == guest1.id for s in sales_g1)

    sales_voided = services.pos_service.get_pos_sales(db, status=POSSaleStatus.VOIDED)
    assert len(sales_voided) >= 1
    assert all(s.status == POSSaleStatus.VOIDED for s in sales_voided)


def test_void_pos_sale_service(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_vps_c"))
    manager_voider = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_vps_v"))

    sale_to_void = create_random_pos_sale(db, cashier_user_id=cashier.id) # Status is COMPLETED by default

    void_reason = "Customer changed mind."
    voided_sale = services.pos_service.void_pos_sale(db, sale_id=sale_to_void.id, reason=void_reason, voiding_user_id=manager_voider.id)

    assert voided_sale is not None
    assert voided_sale.status == POSSaleStatus.VOIDED
    assert voided_sale.void_reason == void_reason
    assert voided_sale.voided_by_user_id == manager_voider.id
    assert voided_sale.voided_at is not None

def test_void_already_voided_sale_fail(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_vps_av_c"))
    manager_voider = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_vps_av_v"))
    # Create a sale and immediately void it for the test setup
    sale_to_void_twice = create_random_pos_sale(db, cashier_user_id=cashier.id)
    services.pos_service.void_pos_sale(db, sale_to_void_twice.id, "Initial void", manager_voider.id)

    db.refresh(sale_to_void_twice) # Ensure status is VOIDED from DB
    assert sale_to_void_twice.status == POSSaleStatus.VOIDED

    with pytest.raises(HTTPException) as exc_info:
        services.pos_service.void_pos_sale(db, sale_id=sale_to_void_twice.id, reason="Test second void", voiding_user_id=manager_voider.id)
    assert exc_info.value.status_code == 400
    assert "already voided" in exc_info.value.detail.lower()

def test_void_pending_payment_sale(db: Session):
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cashier_vps_pp_c"))
    manager_voider = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_vps_pp_v"))

    # Manually create a PENDING_PAYMENT sale for this test, as util defaults to COMPLETED
    product = create_random_product(db, name_suffix="_vps_pp_p1", price=Decimal("10.00"))
    ensure_inventory_item_exists(db, product.id, initial_quantity=10)
    sale_items_in = [schemas.pos.POSSaleItemCreate(product_id=product.id, quantity=1)]
    sale_in_schema = schemas.pos.POSSaleCreate(payment_method=PaymentMethod.OTHER, items=sale_items_in)

    # Temporarily modify service or create manually to set PENDING_PAYMENT
    # For now, assume we can create it and then update its status for test setup
    temp_sale = services.pos_service.create_pos_sale(db, sale_in=sale_in_schema, cashier_user_id=cashier.id)
    temp_sale.status = POSSaleStatus.PENDING_PAYMENT # Manually set for test after creation
    db.add(temp_sale)
    db.commit()
    db.refresh(temp_sale)

    void_reason = "Payment not received, voiding."
    voided_sale = services.pos_service.void_pos_sale(db, sale_id=temp_sale.id, reason=void_reason, voiding_user_id=manager_voider.id)
    assert voided_sale is not None
    assert voided_sale.status == POSSaleStatus.VOIDED
    assert voided_sale.void_reason == void_reason
