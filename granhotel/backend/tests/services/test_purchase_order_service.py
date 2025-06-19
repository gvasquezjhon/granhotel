import pytest
from sqlalchemy.orm import Session, joinedload # joinedload for potential test-side verification
from fastapi import HTTPException
from datetime import date, timedelta
from decimal import Decimal

from app import schemas, services, models
from app.models.inventory import PurchaseOrderStatus, StockMovementType
from tests.utils.inventory import create_random_supplier, create_random_po_items_data, create_random_purchase_order, ensure_inventory_item_exists
from tests.utils.product import create_random_product # Needed by create_random_po_items_data
from tests.utils.common import random_lower_string


def test_create_purchase_order_service(db: Session):
    supplier = create_random_supplier(db, suffix="_po_create")
    # create_random_po_items_data creates products internally
    items_data = create_random_po_items_data(db, num_items=2, product_name_suffix_base="crt_po_srv")

    po_in = schemas.inventory.PurchaseOrderCreate(
        supplier_id=supplier.id,
        items=items_data,
        order_date=date.today(),
        expected_delivery_date=date.today() + timedelta(days=7),
        notes="Test PO creation"
    )
    po = services.purchase_order_service.create_purchase_order(db, po_in)

    assert po is not None
    assert po.supplier_id == supplier.id
    assert len(po.items) == 2
    assert po.status == PurchaseOrderStatus.PENDING # Default from schema
    assert po.items[0].product_id == items_data[0].product_id
    assert po.items[0].quantity_ordered == items_data[0].quantity_ordered
    assert po.items[0].unit_price_paid is not None

def test_create_purchase_order_no_items_fail(db: Session):
    supplier = create_random_supplier(db, suffix="_po_noitem")
    po_in_no_items = schemas.inventory.PurchaseOrderCreate(supplier_id=supplier.id, items=[])
    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.create_purchase_order(db, po_in_no_items)
    assert exc_info.value.status_code == 400
    assert "must contain at least one item" in exc_info.value.detail

def test_create_purchase_order_invalid_supplier_fail(db: Session):
    items_data = create_random_po_items_data(db, num_items=1, product_name_suffix_base="bad_sup_po")
    po_in_bad_supplier = schemas.inventory.PurchaseOrderCreate(supplier_id=99999, items=items_data)
    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.create_purchase_order(db, po_in_bad_supplier)
    assert exc_info.value.status_code == 404

def test_create_purchase_order_invalid_product_fail(db: Session):
    supplier = create_random_supplier(db, suffix="_po_badprod")
    bad_item_data = [schemas.inventory.PurchaseOrderItemCreate(product_id=99999, quantity_ordered=10)]
    po_in_bad_product = schemas.inventory.PurchaseOrderCreate(supplier_id=supplier.id, items=bad_item_data)
    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.create_purchase_order(db, po_in_bad_product)
    assert exc_info.value.status_code == 404

def test_get_purchase_order_service(db: Session):
    po_created = create_random_purchase_order(db, num_items=1, po_notes_suffix="_get_po_srv")
    po_fetched = services.purchase_order_service.get_purchase_order(db, po_id=po_created.id)

    assert po_fetched is not None
    assert po_fetched.id == po_created.id
    assert po_fetched.supplier is not None
    assert len(po_fetched.items) == 1
    assert po_fetched.items[0].product is not None
    assert po_fetched.items[0].product.category is not None

def test_get_all_purchase_orders_service(db: Session):
    sup1 = create_random_supplier(db, "_po_list_s1")
    sup2 = create_random_supplier(db, "_po_list_s2")
    create_random_purchase_order(db, supplier_id=sup1.id, status=PurchaseOrderStatus.ORDERED)
    create_random_purchase_order(db, supplier_id=sup2.id, status=PurchaseOrderStatus.RECEIVED)
    create_random_purchase_order(db, supplier_id=sup1.id, status=PurchaseOrderStatus.ORDERED)

    all_pos = services.purchase_order_service.get_all_purchase_orders(db, limit=10)
    assert len(all_pos) >= 3

    sup1_pos = services.purchase_order_service.get_all_purchase_orders(db, supplier_id=sup1.id)
    assert len(sup1_pos) >= 2
    assert all(po.supplier_id == sup1.id for po in sup1_pos)

    ordered_pos = services.purchase_order_service.get_all_purchase_orders(db, status=PurchaseOrderStatus.ORDERED)
    assert len(ordered_pos) >= 2
    assert all(po.status == PurchaseOrderStatus.ORDERED for po in ordered_pos)


def test_update_purchase_order_status_service(db: Session):
    po = create_random_purchase_order(db, status=PurchaseOrderStatus.ORDERED)
    updated_po = services.purchase_order_service.update_purchase_order_status(db, po.id, PurchaseOrderStatus.CANCELLED)
    assert updated_po is not None
    assert updated_po.status == PurchaseOrderStatus.CANCELLED

def test_update_po_status_invalid_transition(db: Session):
    po_received = create_random_purchase_order(db, status=PurchaseOrderStatus.RECEIVED)
    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.update_purchase_order_status(db, po_received.id, PurchaseOrderStatus.PENDING)
    assert exc_info.value.status_code == 400

    po_cancelled = create_random_purchase_order(db, status=PurchaseOrderStatus.CANCELLED)
    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.update_purchase_order_status(db, po_cancelled.id, PurchaseOrderStatus.ORDERED)
    assert exc_info.value.status_code == 400

def test_update_po_status_to_received_fail_if_items_not_received(db: Session):
    po = create_random_purchase_order(db, num_items=1, status=PurchaseOrderStatus.ORDERED)
    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.update_purchase_order_status(db, po.id, PurchaseOrderStatus.RECEIVED)
    assert exc_info.value.status_code == 400
    assert "not all items are fully received" in exc_info.value.detail.lower()


def test_receive_purchase_order_item_fully(db: Session):
    po = create_random_purchase_order(db, num_items=1, status=PurchaseOrderStatus.ORDERED)
    po_item_to_receive = po.items[0]
    product_id_of_item = po_item_to_receive.product_id
    quantity_ordered = po_item_to_receive.quantity_ordered

    ensure_inventory_item_exists(db, product_id=product_id_of_item, initial_quantity=0)
    initial_stock_obj = services.inventory_service.get_inventory_item_by_product_id(db, product_id_of_item)
    initial_stock_on_hand = initial_stock_obj.quantity_on_hand if initial_stock_obj else 0

    updated_po_item = services.purchase_order_service.receive_purchase_order_item(
        db, po_item_id=po_item_to_receive.id, quantity_received_now=quantity_ordered
    )

    assert updated_po_item is not None
    assert updated_po_item.quantity_received == quantity_ordered

    final_stock_obj = services.inventory_service.get_inventory_item_by_product_id(db, product_id_of_item)
    assert final_stock_obj is not None
    assert final_stock_obj.quantity_on_hand == initial_stock_on_hand + quantity_ordered

    history = services.inventory_service.get_stock_movement_history(db, product_id_of_item)
    # ensure_inventory_item_exists with initial_quantity=0 does not create INITIAL_STOCK
    # So only one PURCHASE_RECEIPT movement is expected.
    assert len(history) == 1
    assert any(
        h.movement_type == StockMovementType.PURCHASE_RECEIPT and \
        h.quantity_changed == quantity_ordered and \
        h.purchase_order_item_id == po_item_to_receive.id
        for h in history
    )

    db.refresh(po)
    assert po.status == PurchaseOrderStatus.RECEIVED

def test_receive_purchase_order_item_partially(db: Session):
    po = create_random_purchase_order(db, num_items=2, status=PurchaseOrderStatus.ORDERED)
    item1_to_receive = po.items[0]
    item1_product_id = item1_to_receive.product_id
    item1_qty_ordered = item1_to_receive.quantity_ordered

    ensure_inventory_item_exists(db, product_id=item1_product_id, initial_quantity=0)

    qty_received_partial = item1_qty_ordered - 1 if item1_qty_ordered > 1 else 1 # Ensure positive partial receive
    if item1_qty_ordered == 1 : qty_received_partial = 1 # if only 1 ordered, receive 1

    updated_item1 = services.purchase_order_service.receive_purchase_order_item(
        db, po_item_id=item1_to_receive.id, quantity_received_now=qty_received_partial
    )
    assert updated_item1.quantity_received == qty_received_partial

    db.refresh(po)
    assert po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED

    if item1_qty_ordered > qty_received_partial : # If there's remaining quantity
        services.purchase_order_service.receive_purchase_order_item(
            db, po_item_id=item1_to_receive.id, quantity_received_now=item1_qty_ordered - qty_received_partial
        )
    db.refresh(po)
    assert po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED

    item2_to_receive = po.items[1]
    ensure_inventory_item_exists(db, product_id=item2_to_receive.product_id, initial_quantity=0)
    services.purchase_order_service.receive_purchase_order_item(
        db, po_item_id=item2_to_receive.id, quantity_received_now=item2_to_receive.quantity_ordered
    )
    db.refresh(po)
    assert po.status == PurchaseOrderStatus.RECEIVED


def test_receive_po_item_over_receive_fail(db: Session):
    po = create_random_purchase_order(db, num_items=1, status=PurchaseOrderStatus.ORDERED)
    po_item = po.items[0]
    ensure_inventory_item_exists(db, product_id=po_item.product_id)

    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.receive_purchase_order_item(
            db, po_item_id=po_item.id, quantity_received_now=po_item.quantity_ordered + 1
        )
    assert exc_info.value.status_code == 400
    assert "cannot exceed quantity ordered" in exc_info.value.detail.lower()

def test_receive_po_item_invalid_status_fail(db: Session):
    po_cancelled = create_random_purchase_order(db, num_items=1, status=PurchaseOrderStatus.CANCELLED)
    po_item_cancelled = po_cancelled.items[0]
    ensure_inventory_item_exists(db, product_id=po_item_cancelled.product_id)

    with pytest.raises(HTTPException) as exc_info:
        services.purchase_order_service.receive_purchase_order_item(
            db, po_item_id=po_item_cancelled.id, quantity_received_now=1
        )
    assert exc_info.value.status_code == 400
    assert "cannot receive items for a purchase order with status 'CANCELLED'" in exc_info.value.detail.lower()
