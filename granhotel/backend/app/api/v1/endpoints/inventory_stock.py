from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date

from app import schemas, models, services
from app.api import deps
from app.db import session as db_session
from app.models.inventory import StockMovementType

router = APIRouter()

@router.get("/products/{product_id}", response_model=schemas.inventory.InventoryItem)
def read_inventory_item_for_product_api(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Get current inventory details (stock on hand, threshold) for a specific product.
    '''
    inventory_item = services.inventory_service.get_inventory_item_by_product_id(db, product_id=product_id)
    if not inventory_item:
        # Check if product exists to give a more specific error
        product = services.product_service.get_product(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")
        # Product exists, but no inventory item. This could mean it needs initialization.
        # Depending on business logic, could auto-create here, or return 404.
        # For now, return 404, as services.inventory_service.update_stock expects item to exist or creates it carefully.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory record for product ID {product_id} not found. Consider initializing stock or ensure product setup is complete.")
    return inventory_item

@router.post("/products/{product_id}/adjust-stock", response_model=schemas.inventory.InventoryItem)
def adjust_product_stock_api(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    adjustment_in: schemas.inventory.InventoryAdjustment,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Manually adjust stock for a product (e.g., due to stock count, damage).
    Requires Manager or Admin role.
    `quantity_changed` is positive for increase, negative for decrease.
    `movement_type` in payload must be an adjustment type.
    '''
    # Validate movement_type from payload
    if adjustment_in.movement_type not in [StockMovementType.ADJUSTMENT_INCREASE, StockMovementType.ADJUSTMENT_DECREASE]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid movement type for stock adjustment. Use ADJUSTMENT_INCREASE or ADJUSTMENT_DECREASE.")

    # Validate quantity_changed against the movement_type
    if adjustment_in.movement_type == StockMovementType.ADJUSTMENT_INCREASE and adjustment_in.quantity_changed <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be positive for ADJUSTMENT_INCREASE.")
    if adjustment_in.movement_type == StockMovementType.ADJUSTMENT_DECREASE and adjustment_in.quantity_changed >= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be negative for ADJUSTMENT_DECREASE.")
    # Schema already validates quantity_changed != 0 via validator

    # Ensure product exists before attempting stock update
    product = services.product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")

    updated_inventory_item = services.inventory_service.update_stock(
        db=db,
        product_id=product_id,
        quantity_changed=adjustment_in.quantity_changed,
        movement_type=adjustment_in.movement_type, # Pass the validated type
        reason=adjustment_in.reason
    )
    return updated_inventory_item

@router.put("/products/{product_id}/low-stock-threshold", response_model=schemas.inventory.InventoryItem)
def set_product_low_stock_threshold_api(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    threshold_in: schemas.inventory.InventoryItemLowStockThresholdUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Set or update the low stock threshold for a product.
    Requires Manager or Admin role.
    '''
    # Ensure product exists
    product = services.product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")

    updated_inventory_item = services.inventory_service.set_low_stock_threshold(
        db, product_id=product_id, threshold=threshold_in.low_stock_threshold
    )
    return updated_inventory_item


@router.get("/low-stock", response_model=List[schemas.inventory.InventoryItem])
def get_low_stock_items_api(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Get a list of all inventory items that are currently at or below their low stock threshold.
    '''
    low_stock_items = services.inventory_service.get_low_stock_items(db, skip=skip, limit=limit)
    return low_stock_items

@router.get("/products/{product_id}/history", response_model=List[schemas.inventory.StockMovement])
def get_product_stock_movement_history_api(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = Query(None, description="Filter history from this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter history up to this date (YYYY-MM-DD)"),
    movement_type: Optional[StockMovementType] = Query(None, description="Filter by a specific movement type"),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Get the stock movement history for a specific product.
    '''
    product = services.product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")

    history = services.inventory_service.get_stock_movement_history(
        db, product_id=product_id, skip=skip, limit=limit, date_from=date_from, date_to=date_to, movement_type=movement_type
    )
    return history
