from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
from datetime import datetime, date, timezone, timedelta # Ensure all are imported

from app import models
from app import schemas
from app.models.inventory import InventoryItem, StockMovement, StockMovementType
from app.models.product import Product # To link inventory to product
from fastapi import HTTPException, status

def get_inventory_item_by_product_id(db: Session, product_id: int) -> Optional[models.inventory.InventoryItem]:
    '''Retrieve an inventory item by product_id, including the product details.'''
    return db.query(models.inventory.InventoryItem).options(
        joinedload(models.inventory.InventoryItem.product)
    ).filter(models.inventory.InventoryItem.product_id == product_id).first()

def _create_stock_movement_internal( # Renamed to indicate internal use and avoid export by default
    db: Session,
    product_id: int,
    quantity_changed: int,
    movement_type: StockMovementType,
    reason: Optional[str] = None,
    related_purchase_order_item_id: Optional[int] = None,
    commit: bool = True # Allow caller to control commit for transactions
) -> models.inventory.StockMovement:
    '''
    Internal helper to record a stock movement.
    Actual quantity_on_hand updates should be handled by a dedicated function like `update_stock`.
    '''
    product = db.query(models.product.Product).filter(models.product.Product.id == product_id).first()
    if not product:
        # This should ideally not happen if called from trusted service functions
        # that have already validated product_id.
        raise ValueError(f"Product with ID {product_id} not found for stock movement.")

    db_stock_movement = models.inventory.StockMovement(
        product_id=product_id,
        quantity_changed=quantity_changed,
        movement_type=movement_type,
        reason=reason,
        purchase_order_item_id=related_purchase_order_item_id,
        # movement_date is server_default
    )
    db.add(db_stock_movement)
    if commit:
        db.commit()
        db.refresh(db_stock_movement)
    # If not commit, the calling function is responsible for commit & refresh if needed.
    return db_stock_movement


def create_inventory_item_if_not_exists(db: Session, product_id: int, initial_quantity: int = 0, low_stock_threshold: Optional[int] = 0) -> models.inventory.InventoryItem:
    '''
    Creates an inventory item for a product if it doesn't already exist.
    If it exists, it just returns the existing item.
    If created with initial_quantity != 0, an INITIAL_STOCK movement is recorded.
    '''
    inventory_item = get_inventory_item_by_product_id(db, product_id)
    if inventory_item:
        return inventory_item

    product = db.query(models.product.Product).filter(models.product.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found, cannot create inventory item.")

    new_inventory_item = models.inventory.InventoryItem(
        product_id=product_id,
        quantity_on_hand=initial_quantity, # Set initial quantity directly
        low_stock_threshold=low_stock_threshold if low_stock_threshold is not None else 0
        # last_restocked_at will be set if initial_quantity > 0
    )
    if initial_quantity > 0 : # Only set last_restocked if actual stock is added
        new_inventory_item.last_restocked_at = datetime.now(timezone.utc)

    db.add(new_inventory_item)

    if initial_quantity != 0:
        _create_stock_movement_internal(
            db=db,
            product_id=product_id,
            quantity_changed=initial_quantity,
            movement_type=StockMovementType.INITIAL_STOCK,
            reason="Initial stock for new product inventory record",
            commit=False # Commit will be done after adding inventory_item
        )

    db.commit()
    db.refresh(new_inventory_item)
    return new_inventory_item


def update_stock(
    db: Session,
    product_id: int,
    quantity_changed: int,
    movement_type: StockMovementType,
    reason: Optional[str] = None,
    related_purchase_order_item_id: Optional[int] = None,
) -> models.inventory.InventoryItem:
    '''
    Updates the stock quantity for a product and records the movement.
    This is the primary function to change stock levels.
    '''
    if quantity_changed == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity changed cannot be zero.")

    inventory_item = get_inventory_item_by_product_id(db, product_id)
    if not inventory_item:
        # If product exists, create inventory item with the first stock movement quantity.
        # If quantity_changed is negative, this means starting with negative stock, which is an issue.
        if quantity_changed < 0 and movement_type != StockMovementType.INITIAL_STOCK: # Cannot start with negative stock unless it's an initial (potentially erroneous) setup
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot decrease stock for product ID {product_id} as it has no inventory record. Create with initial stock first.")

        # For positive changes or initial stock, create the item.
        # The initial_quantity in create_inventory_item_if_not_exists will be this first quantity_changed.
        inventory_item = create_inventory_item_if_not_exists(db, product_id=product_id, initial_quantity=quantity_changed)
        # The INITIAL_STOCK movement is already created by create_inventory_item_if_not_exists.
        # If the movement_type for this update_stock call was *also* INITIAL_STOCK, it's fine, it just means the first recorded value is this one.
        # If it was a different type (e.g. first movement is a SALE, which is odd), it means initial stock was 0, then this movement.
        # We need to ensure that create_inventory_item_if_not_exists uses the *correct* movement_type if it's the first movement.
        # This is getting complex. Simpler: update_stock assumes inventory_item exists.
        # Let's revert: create_inventory_item_if_not_exists is separate. update_stock requires item to exist.

        # Reverted logic: update_stock requires inventory_item to exist.
        # Caller should ensure inventory_item is created first, e.g. when product is created.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory item for product ID {product_id} not found. Cannot update stock.")


    new_quantity = inventory_item.quantity_on_hand + quantity_changed
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock for product ID {product_id} cannot go below zero. Current: {inventory_item.quantity_on_hand}, Change: {quantity_changed}"
        )

    inventory_item.quantity_on_hand = new_quantity
    if quantity_changed > 0 and movement_type in [StockMovementType.PURCHASE_RECEIPT, StockMovementType.INITIAL_STOCK, StockMovementType.ADJUSTMENT_INCREASE, StockMovementType.CUSTOMER_RETURN]:
        inventory_item.last_restocked_at = datetime.now(timezone.utc)

    db.add(inventory_item)

    _create_stock_movement_internal(
        db=db,
        product_id=product_id,
        quantity_changed=quantity_changed,
        movement_type=movement_type,
        reason=reason,
        related_purchase_order_item_id=related_purchase_order_item_id,
        commit=False # Commit together with inventory_item update
    )

    db.commit()
    db.refresh(inventory_item)
    return inventory_item

def set_low_stock_threshold(db: Session, product_id: int, threshold: int) -> models.inventory.InventoryItem:
    '''Set the low stock threshold for a product's inventory item.'''
    if threshold < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Low stock threshold cannot be negative.")

    inventory_item = get_inventory_item_by_product_id(db, product_id)
    if not inventory_item:
        # If product exists, create inventory item.
        inventory_item = create_inventory_item_if_not_exists(db, product_id=product_id, initial_quantity=0, low_stock_threshold=threshold)
        # The create_inventory_item_if_not_exists will commit.
    else:
        inventory_item.low_stock_threshold = threshold
        db.add(inventory_item)
        db.commit()
        db.refresh(inventory_item)
    return inventory_item

def get_low_stock_items(db: Session, skip: int = 0, limit: int = 100) -> List[models.inventory.InventoryItem]:
    '''Retrieve inventory items that are at or below their low stock threshold and are active products.'''
    return db.query(models.inventory.InventoryItem).join(models.inventory.InventoryItem.product).filter(
        models.product.Product.is_active == True,
        models.inventory.InventoryItem.quantity_on_hand <= models.inventory.InventoryItem.low_stock_threshold,
        models.inventory.InventoryItem.low_stock_threshold > 0 # Only if a threshold is set and > 0
    ).options(
        joinedload(models.inventory.InventoryItem.product)
    ).order_by(models.inventory.InventoryItem.product_id).offset(skip).limit(limit).all()

def get_stock_movement_history(
    db: Session, product_id: int, skip: int = 0, limit: int = 100,
    date_from: Optional[date] = None, date_to: Optional[date] = None,
    movement_type: Optional[StockMovementType] = None
) -> List[models.inventory.StockMovement]:
    '''Retrieve stock movement history for a product, with optional date and type filtering.'''
    query = db.query(models.inventory.StockMovement).filter(models.inventory.StockMovement.product_id == product_id)
    if date_from:
        query = query.filter(models.inventory.StockMovement.movement_date >= datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc))
    if date_to:
        query = query.filter(models.inventory.StockMovement.movement_date < datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    if movement_type:
        query = query.filter(models.inventory.StockMovement.movement_type == movement_type)

    return query.order_by(models.inventory.StockMovement.movement_date.desc(), models.inventory.StockMovement.id.desc()).offset(skip).limit(limit).all()
