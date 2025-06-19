from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Dict
from datetime import date

from app import models
from app import schemas
from app.models.inventory import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, StockMovementType
from app.services import inventory_service # For updating stock upon receiving items
from app.services import supplier_service # To validate supplier
from app.services import product_service # To validate products
from fastapi import HTTPException, status

def create_purchase_order(db: Session, po_in: schemas.PurchaseOrderCreate) -> models.inventory.PurchaseOrder:
    '''Create a new purchase order with its items.'''
    supplier = supplier_service.get_supplier(db, po_in.supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with ID {po_in.supplier_id} not found.")

    if not po_in.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase order must contain at least one item.")

    db_po_items = []
    for item_in in po_in.items:
        product = product_service.get_product(db, item_in.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {item_in.product_id} not found for purchase order.")

        price_paid = item_in.unit_price_paid if item_in.unit_price_paid is not None else product.price

        db_item = models.inventory.PurchaseOrderItem(
            product_id=item_in.product_id,
            quantity_ordered=item_in.quantity_ordered,
            unit_price_paid=price_paid,
            quantity_received=0
        )
        db_po_items.append(db_item)

    po_data = po_in.model_dump(exclude={"items"})
    db_po = models.inventory.PurchaseOrder(**po_data)
    db_po.items = db_po_items

    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    # Eager load for response consistency
    # db_po = get_purchase_order(db, db_po.id) # Simplest way to get fully loaded object, but might cause recursive call if get_purchase_order is complex
    # For now, let's return the refreshed object. The API layer can decide if it needs more details.
    # Or, if we need to ensure relationships are loaded for the immediate return:
    db.refresh(db_po.supplier) # if supplier was lazy loaded before commit
    for item in db_po.items:
        db.refresh(item.product) # if product was lazy loaded
    return db_po


def get_purchase_order(db: Session, po_id: int) -> Optional[models.inventory.PurchaseOrder]:
    '''Retrieve a purchase order by ID, including supplier and items with their products.'''
    return db.query(models.inventory.PurchaseOrder).options(
        joinedload(models.inventory.PurchaseOrder.supplier),
        selectinload(models.inventory.PurchaseOrder.items).joinedload(models.inventory.PurchaseOrderItem.product).selectinload(models.product.Product.category)
    ).filter(models.inventory.PurchaseOrder.id == po_id).first()

def get_all_purchase_orders(
    db: Session, skip: int = 0, limit: int = 100,
    supplier_id: Optional[int] = None,
    status: Optional[PurchaseOrderStatus] = None,
    order_date_from: Optional[date] = None,
    order_date_to: Optional[date] = None
) -> List[models.inventory.PurchaseOrder]:
    '''Retrieve all purchase orders with pagination and optional filters.'''
    query = db.query(models.inventory.PurchaseOrder).options(
        joinedload(models.inventory.PurchaseOrder.supplier),
        # selectinload(models.inventory.PurchaseOrder.items) # Maybe too much data for a list view
    )
    if supplier_id:
        query = query.filter(models.inventory.PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(models.inventory.PurchaseOrder.status == status)
    if order_date_from:
        query = query.filter(models.inventory.PurchaseOrder.order_date >= order_date_from)
    if order_date_to:
        query = query.filter(models.inventory.PurchaseOrder.order_date <= order_date_to)

    return query.order_by(models.inventory.PurchaseOrder.order_date.desc(), models.inventory.PurchaseOrder.id.desc()).offset(skip).limit(limit).all()


def update_purchase_order_status(db: Session, po_id: int, new_status: PurchaseOrderStatus) -> Optional[models.inventory.PurchaseOrder]:
    '''Update the status of a purchase order.'''
    # Use a simpler query here, as get_purchase_order does many joins not needed for just status update
    db_po = db.query(models.inventory.PurchaseOrder).filter(models.inventory.PurchaseOrder.id == po_id).first()
    if not db_po:
        return None

    if db_po.status == PurchaseOrderStatus.RECEIVED and new_status != PurchaseOrderStatus.RECEIVED :
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change status of a fully received order, except for archival or similar administrative actions not covered by simple status update.")
    if db_po.status == PurchaseOrderStatus.CANCELLED and new_status != PurchaseOrderStatus.CANCELLED:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change status of a cancelled order.")

    if new_status == PurchaseOrderStatus.RECEIVED:
        # To set to RECEIVED, all items must be fully received.
        # This check should be done by the receive_purchase_order_item logic automatically.
        # Manually setting to RECEIVED should only be allowed if this condition is met.
        all_items_fully_received = all(item.quantity_received >= item.quantity_ordered for item in db_po.items)
        if not all_items_fully_received:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot manually set PO status to RECEIVED. Not all items are fully received. Use the item receiving process or ensure all items are marked as received.")

    db_po.status = new_status
    db.commit()
    db.refresh(db_po)
    # Return the fully loaded PO for consistency if desired by API
    return get_purchase_order(db, po_id)


def receive_purchase_order_item(
    db: Session, po_item_id: int, quantity_received_now: int
) -> models.inventory.PurchaseOrderItem:
    '''
    Record received quantity for a specific purchase order item.
    Updates stock and the PO item's received quantity.
    Updates the PO's overall status (PARTIALLY_RECEIVED or RECEIVED).
    '''
    if quantity_received_now <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity received must be positive.")

    po_item = db.query(models.inventory.PurchaseOrderItem).options(
        joinedload(models.inventory.PurchaseOrderItem.purchase_order).selectinload(models.inventory.PurchaseOrder.items).joinedload(models.inventory.PurchaseOrderItem.product).selectinload(models.product.Product.category)
    ).filter(models.inventory.PurchaseOrderItem.id == po_item_id).first()

    if not po_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase order item with ID {po_item_id} not found.")

    purchase_order = po_item.purchase_order

    if purchase_order.status not in [PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.PARTIALLY_RECEIVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive items for a purchase order with status '{purchase_order.status.value}'. Order must be 'ORDERED' or 'PARTIALLY_RECEIVED'."
        )

    if po_item.quantity_received + quantity_received_now > po_item.quantity_ordered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total quantity received ({po_item.quantity_received + quantity_received_now}) cannot exceed quantity ordered ({po_item.quantity_ordered})."
        )

    # This will commit the stock movement and inventory item update
    inventory_service.update_stock(
        db=db,
        product_id=po_item.product_id,
        quantity_changed=quantity_received_now,
        movement_type=StockMovementType.PURCHASE_RECEIPT,
        reason=f"Received against PO Item ID {po_item.id} (PO ID {purchase_order.id})",
        related_purchase_order_item_id=po_item.id
    )

    po_item.quantity_received += quantity_received_now
    db.add(po_item) # Add updated po_item to session

    # Update PO status based on all its items
    all_items_fully_received = True
    current_total_received_for_po = 0
    current_total_ordered_for_po = 0

    for item in purchase_order.items: # Iterate through all items of the PO
        if item.quantity_received < item.quantity_ordered:
            all_items_fully_received = False
        current_total_received_for_po += item.quantity_received
        current_total_ordered_for_po += item.quantity_ordered

    if all_items_fully_received:
        purchase_order.status = PurchaseOrderStatus.RECEIVED
    elif current_total_received_for_po > 0 : # If anything has been received but not all
        purchase_order.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
    else: # Nothing received yet across all items
        purchase_order.status = PurchaseOrderStatus.ORDERED


    db.add(purchase_order) # Add updated purchase_order to session
    db.commit()
    db.refresh(po_item)
    db.refresh(purchase_order)

    # Re-fetch po_item with its product for the response, as refresh might not populate it
    # The joinedload in the initial query for po_item should have loaded product, but it's safer.
    # If product was already loaded, this is efficient.
    if not po_item.product or not po_item.product.category: # Check if already loaded
         po_item = db.query(models.inventory.PurchaseOrderItem).options(
            joinedload(models.inventory.PurchaseOrderItem.product).selectinload(models.product.Product.category)
        ).filter(models.inventory.PurchaseOrderItem.id == po_item.id).first()

    return po_item
