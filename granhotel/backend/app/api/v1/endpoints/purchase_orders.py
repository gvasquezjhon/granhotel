from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date

from app import schemas, models, services
from app.api import deps
from app.db import session as db_session
from app.models.inventory import PurchaseOrderStatus

router = APIRouter()

@router.post("/", response_model=schemas.inventory.PurchaseOrder, status_code=status.HTTP_201_CREATED)
def create_new_purchase_order_api(
    *,
    db: Session = Depends(db_session.get_db),
    po_in: schemas.inventory.PurchaseOrderCreate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Create a new purchase order. Requires Manager or Admin role.
    The request body should include a list of items to be ordered.
    '''
    # Service layer handles validation of supplier, products, etc.
    purchase_order = services.purchase_order_service.create_purchase_order(db=db, po_in=po_in)
    return purchase_order

@router.get("/", response_model=List[schemas.inventory.PurchaseOrder])
def read_all_purchase_orders_api(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    supplier_id: Optional[int] = Query(None, description="Filter by Supplier ID"),
    status: Optional[PurchaseOrderStatus] = Query(None, description="Filter by PO status"),
    order_date_from: Optional[date] = Query(None, description="Filter POs on or after this order date"),
    order_date_to: Optional[date] = Query(None, description="Filter POs on or before this order date"),
    current_user: models.User = Depends(deps.get_current_active_user) # Active users can view POs
) -> Any:
    '''
    Retrieve all purchase orders with optional filters and pagination.
    '''
    purchase_orders = services.purchase_order_service.get_all_purchase_orders(
        db, skip=skip, limit=limit, supplier_id=supplier_id, status=status,
        order_date_from=order_date_from, order_date_to=order_date_to
    )
    return purchase_orders

@router.get("/{po_id}", response_model=schemas.inventory.PurchaseOrder)
def read_single_purchase_order_api(
    *,
    db: Session = Depends(db_session.get_db),
    po_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Retrieve a specific purchase order by ID. Includes items and supplier details.
    '''
    purchase_order = services.purchase_order_service.get_purchase_order(db, po_id=po_id)
    if not purchase_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return purchase_order

@router.patch("/{po_id}/status", response_model=schemas.inventory.PurchaseOrder)
def update_purchase_order_status_api(
    *,
    db: Session = Depends(db_session.get_db),
    po_id: int,
    status_update: schemas.inventory.PurchaseOrderStatusUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Update the status of a purchase order (e.g., to CANCELLED).
    Requires Manager or Admin role.
    Note: Status changes to PARTIALLY_RECEIVED or RECEIVED are typically driven by item receiving.
    '''
    # Service layer handles validation of status transition and if PO exists
    updated_po = services.purchase_order_service.update_purchase_order_status(
        db, po_id=po_id, new_status=status_update.status
    )
    if not updated_po: # If PO not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found for status update")
    return updated_po

@router.post("/{po_id}/items/{po_item_id}/receive", response_model=schemas.inventory.PurchaseOrderItem)
def receive_purchase_order_item_api(
    *,
    db: Session = Depends(db_session.get_db),
    po_id: int, # Path parameter to ensure item belongs to PO
    po_item_id: int,
    receive_in: schemas.inventory.PurchaseOrderItemReceive,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Record received quantity for a specific purchase order item.
    Updates stock, PO item's received quantity, and overall PO status.
    Requires Manager or Admin role.
    '''
    # Check if po_item_id belongs to po_id for path consistency before calling service.
    # The service might also do this check, but it's good practice for RESTful path design.
    po_item_check = db.query(models.inventory.PurchaseOrderItem).filter(
        models.inventory.PurchaseOrderItem.id == po_item_id,
        models.inventory.PurchaseOrderItem.purchase_order_id == po_id
    ).first()

    if not po_item_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order item ID {po_item_id} not found or does not belong to Purchase Order ID {po_id}."
        )

    # Service layer handles main logic, including stock update and PO status changes
    updated_po_item = services.purchase_order_service.receive_purchase_order_item(
        db, po_item_id=po_item_id, quantity_received_now=receive_in.quantity_received
    )
    # The returned po_item from service should have its product loaded.
    return updated_po_item
