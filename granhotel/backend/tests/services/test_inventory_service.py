import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date, timedelta, datetime, timezone # Ensure timezone is imported

from app import schemas, services, models
from app.models.inventory import StockMovementType, InventoryItem
from tests.utils.product import create_random_product
from tests.utils.inventory import ensure_inventory_item_exists # Using the new util

def test_create_inventory_item_if_not_exists_new(db: Session):
    product = create_random_product(db, name_suffix="_inv_new")
    inv_item = services.inventory_service.create_inventory_item_if_not_exists(
        db, product_id=product.id, initial_quantity=10, low_stock_threshold=5
    )
    assert inv_item is not None
    assert inv_item.product_id == product.id
    assert inv_item.quantity_on_hand == 10
    assert inv_item.low_stock_threshold == 5
    assert inv_item.last_restocked_at is not None # Should be set if initial_quantity > 0

    history = services.inventory_service.get_stock_movement_history(db, product_id=product.id)
    assert len(history) == 1
    assert history[0].movement_type == StockMovementType.INITIAL_STOCK
    assert history[0].quantity_changed == 10

def test_create_inventory_item_if_not_exists_new_zero_quantity(db: Session):
    product = create_random_product(db, name_suffix="_inv_new_zero")
    inv_item = services.inventory_service.create_inventory_item_if_not_exists(
        db, product_id=product.id, initial_quantity=0, low_stock_threshold=3
    )
    assert inv_item is not None
    assert inv_item.product_id == product.id
    assert inv_item.quantity_on_hand == 0
    assert inv_item.low_stock_threshold == 3
    assert inv_item.last_restocked_at is None # Should not be set if initial_quantity is 0

    history = services.inventory_service.get_stock_movement_history(db, product_id=product.id)
    assert len(history) == 0 # No INITIAL_STOCK movement for zero quantity

def test_create_inventory_item_if_not_exists_existing(db: Session):
    product = create_random_product(db, name_suffix="_inv_exist")
    inv_item_orig = services.inventory_service.create_inventory_item_if_not_exists(
        db, product_id=product.id, initial_quantity=5, low_stock_threshold=2
    )
    inv_item_fetched = services.inventory_service.create_inventory_item_if_not_exists(
        db, product_id=product.id, initial_quantity=100, low_stock_threshold=50
    )
    assert inv_item_fetched.id == inv_item_orig.id
    assert inv_item_fetched.quantity_on_hand == 5
    assert inv_item_fetched.low_stock_threshold == 2

    history = services.inventory_service.get_stock_movement_history(db, product_id=product.id)
    assert len(history) == 1

def test_update_stock_increase(db: Session):
    product = create_random_product(db, name_suffix="_upd_inc")
    ensure_inventory_item_exists(db, product.id, initial_quantity=10)

    updated_inv_item = services.inventory_service.update_stock(
        db, product_id=product.id, quantity_changed=5, movement_type=StockMovementType.ADJUSTMENT_INCREASE, reason="Cycle count adjustment"
    )
    assert updated_inv_item.quantity_on_hand == 15
    assert updated_inv_item.last_restocked_at is not None

    history = services.inventory_service.get_stock_movement_history(db, product_id=product.id)
    assert len(history) == 2
    assert any(h.movement_type == StockMovementType.ADJUSTMENT_INCREASE and h.quantity_changed == 5 for h in history)

def test_update_stock_decrease(db: Session):
    product = create_random_product(db, name_suffix="_upd_dec")
    ensure_inventory_item_exists(db, product.id, initial_quantity=20)

    updated_inv_item = services.inventory_service.update_stock(
        db, product_id=product.id, quantity_changed=-5, movement_type=StockMovementType.SALE, reason="Customer sale"
    )
    assert updated_inv_item.quantity_on_hand == 15

    history = services.inventory_service.get_stock_movement_history(db, product_id=product.id)
    assert len(history) == 2
    assert any(h.movement_type == StockMovementType.SALE and h.quantity_changed == -5 for h in history)

def test_update_stock_to_zero(db: Session):
    product = create_random_product(db, name_suffix="_upd_zero")
    ensure_inventory_item_exists(db, product.id, initial_quantity=5)
    updated_inv_item = services.inventory_service.update_stock(
        db, product_id=product.id, quantity_changed=-5, movement_type=StockMovementType.SALE
    )
    assert updated_inv_item.quantity_on_hand == 0

def test_update_stock_below_zero_fail(db: Session):
    product = create_random_product(db, name_suffix="_upd_neg")
    ensure_inventory_item_exists(db, product.id, initial_quantity=3)
    with pytest.raises(HTTPException) as exc_info:
        services.inventory_service.update_stock(
            db, product_id=product.id, quantity_changed=-5, movement_type=StockMovementType.SALE
        )
    assert exc_info.value.status_code == 400
    assert "cannot go below zero" in exc_info.value.detail.lower()

def test_update_stock_item_not_exists_fail(db: Session):
    product = create_random_product(db, name_suffix="_upd_no_inv")
    # Inventory item does not exist for product_id
    with pytest.raises(HTTPException) as exc_info:
        services.inventory_service.update_stock(
            db, product_id=product.id, quantity_changed=5, movement_type=StockMovementType.ADJUSTMENT_INCREASE
        )
    assert exc_info.value.status_code == 404 # Based on current service logic
    assert "inventory item for product id" in exc_info.value.detail.lower()
    assert "not found" in exc_info.value.detail.lower()


def test_set_low_stock_threshold(db: Session):
    product = create_random_product(db, name_suffix="_low_thresh")
    inv_item = ensure_inventory_item_exists(db, product.id, low_stock_threshold=5) # Default initial_quantity=0

    updated_inv_item = services.inventory_service.set_low_stock_threshold(db, product.id, threshold=10)
    assert updated_inv_item.low_stock_threshold == 10

    product2 = create_random_product(db, name_suffix="_low_thresh_new")
    updated_inv_item2 = services.inventory_service.set_low_stock_threshold(db, product2.id, threshold=3)
    assert updated_inv_item2 is not None
    assert updated_inv_item2.product_id == product2.id
    assert updated_inv_item2.low_stock_threshold == 3
    assert updated_inv_item2.quantity_on_hand == 0

def test_set_low_stock_threshold_negative_fail(db: Session):
    product = create_random_product(db, name_suffix="_low_thresh_neg")
    # ensure_inventory_item_exists will create the item if product exists
    with pytest.raises(HTTPException) as exc_info:
        services.inventory_service.set_low_stock_threshold(db, product.id, threshold=-5)
    assert exc_info.value.status_code == 400

def test_get_low_stock_items(db: Session):
    prod1 = create_random_product(db, name_suffix="_ls_1", is_active=True)
    ensure_inventory_item_exists(db, prod1.id, initial_quantity=5, low_stock_threshold=10)

    prod2 = create_random_product(db, name_suffix="_ls_2", is_active=True)
    ensure_inventory_item_exists(db, prod2.id, initial_quantity=15, low_stock_threshold=10)

    prod3 = create_random_product(db, name_suffix="_ls_3", is_active=False) # Inactive product
    ensure_inventory_item_exists(db, prod3.id, initial_quantity=2, low_stock_threshold=5)

    prod4 = create_random_product(db, name_suffix="_ls_4", is_active=True)
    ensure_inventory_item_exists(db, prod4.id, initial_quantity=0, low_stock_threshold=0) # Threshold is 0

    prod5 = create_random_product(db, name_suffix="_ls_5", is_active=True)
    ensure_inventory_item_exists(db, prod5.id, initial_quantity=1, low_stock_threshold=1) # quantity == threshold, threshold > 0

    low_stock_list = services.inventory_service.get_low_stock_items(db)
    low_stock_product_ids = [item.product_id for item in low_stock_list]

    assert prod1.id in low_stock_product_ids  # 5 <= 10, threshold > 0
    assert prod2.id not in low_stock_product_ids # 15 > 10
    assert prod3.id not in low_stock_product_ids # Product inactive
    assert prod4.id not in low_stock_product_ids # Threshold is 0
    assert prod5.id in low_stock_product_ids # 1 <= 1, threshold > 0


def test_get_stock_movement_history(db: Session):
    product = create_random_product(db, name_suffix="_hist")
    # ensure_inventory_item_exists calls create_inventory_item_if_not_exists which logs INITIAL_STOCK
    inv_item = ensure_inventory_item_exists(db, product.id, initial_quantity=50)

    services.inventory_service.update_stock(db, product.id, -10, StockMovementType.SALE)
    services.inventory_service.update_stock(db, product.id, -5, StockMovementType.ADJUSTMENT_DECREASE, "Damaged")
    services.inventory_service.update_stock(db, product.id, 20, StockMovementType.PURCHASE_RECEIPT)

    history = services.inventory_service.get_stock_movement_history(db, product.id)
    assert len(history) == 4
    assert history[0].quantity_changed == 20
    assert history[0].movement_type == StockMovementType.PURCHASE_RECEIPT

    sale_history = services.inventory_service.get_stock_movement_history(db, product.id, movement_type=StockMovementType.SALE)
    assert len(sale_history) == 1
    assert sale_history[0].movement_type == StockMovementType.SALE
    assert sale_history[0].quantity_changed == -10

    # Test date filtering
    # Create a movement on a known past date for filtering
    past_date = date.today() - timedelta(days=5)
    # Manually create a stock movement for testing date filter
    # Need to ensure product and inventory item exist first
    prod_for_date_filter = create_random_product(db, name_suffix="_hist_date")
    ensure_inventory_item_exists(db, prod_for_date_filter.id, initial_quantity=10)

    past_movement = models.inventory.StockMovement(
        product_id=prod_for_date_filter.id,
        quantity_changed=-2,
        movement_type=StockMovementType.SALE,
        movement_date=datetime.combine(past_date, datetime.min.time(), tzinfo=timezone.utc), # Set specific past date
        reason="Past sale for date filter test"
    )
    db.add(past_movement)
    db.commit()

    history_date_from = services.inventory_service.get_stock_movement_history(db, prod_for_date_filter.id, date_from=past_date)
    assert any(h.id == past_movement.id for h in history_date_from)

    history_date_to = services.inventory_service.get_stock_movement_history(db, prod_for_date_filter.id, date_to=past_date)
    assert any(h.id == past_movement.id for h in history_date_to)

    history_specific_date = services.inventory_service.get_stock_movement_history(db, prod_for_date_filter.id, date_from=past_date, date_to=past_date)
    assert any(h.id == past_movement.id for h in history_specific_date)

    history_after_specific_date = services.inventory_service.get_stock_movement_history(db, prod_for_date_filter.id, date_from=past_date + timedelta(days=1))
    assert not any(h.id == past_movement.id for h in history_after_specific_date)
