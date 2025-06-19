from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date
import uuid

from app import schemas, models, services
from app.api import deps
from app.db import session as db_session
from app.models.pos import POSSaleStatus, PaymentMethod
from app.models.user import UserRole

router = APIRouter()

@router.post("/sales/", response_model=schemas.pos.POSSale, status_code=status.HTTP_201_CREATED)
def create_new_pos_sale_api(
    *,
    db: Session = Depends(db_session.get_db),
    sale_in: schemas.pos.POSSaleCreate,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Create a new Point of Sale transaction.
    Accessible by users with roles: RECEPTIONIST, MANAGER, ADMIN.
    Deducts stock from inventory. Calculates prices and taxes.
    '''
    if current_user.role not in [UserRole.RECEPTIONIST, UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to create POS sales."
        )

    new_sale = services.pos_service.create_pos_sale(
        db=db, sale_in=sale_in, cashier_user_id=current_user.id
    )
    return new_sale

@router.get("/sales/", response_model=List[schemas.pos.POSSale])
def read_all_pos_sales_api(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    cashier_user_id: Optional[uuid.UUID] = Query(None, description="Filter by Cashier (User ID)"),
    guest_id: Optional[uuid.UUID] = Query(None, description="Filter by Guest ID"),
    status: Optional[POSSaleStatus] = Query(None, description="Filter by sale status"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    date_from: Optional[date] = Query(None, description="Filter sales on or after this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter sales on or before this date (YYYY-MM-DD)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Retrieve all Point of Sale transactions with optional filters.
    Requires Manager or Admin role.
    '''
    sales = services.pos_service.get_pos_sales(
        db, skip=skip, limit=limit, cashier_user_id=cashier_user_id, guest_id=guest_id,
        status=status, payment_method=payment_method, date_from=date_from, date_to=date_to
    )
    return sales

@router.get("/sales/{sale_id}", response_model=schemas.pos.POSSale)
def read_single_pos_sale_api(
    *,
    db: Session = Depends(db_session.get_db),
    sale_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Retrieve a specific Point of Sale transaction by its ID.
    Includes items, products, cashier, and guest details.
    Receptionist can only view their own sales unless they are also Manager/Admin.
    '''
    sale = services.pos_service.get_pos_sale(db, sale_id=sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="POS Sale not found")

    is_manager_or_admin = current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    # If user is RECEPTIONIST and not cashier of this sale, and not manager/admin, deny access.
    if current_user.role == UserRole.RECEPTIONIST and sale.cashier_user_id != current_user.id and not is_manager_or_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this POS sale")
    return sale

@router.post("/sales/{sale_id}/void", response_model=schemas.pos.POSSale)
def void_pos_sale_api(
    *,
    db: Session = Depends(db_session.get_db),
    sale_id: int,
    void_in: schemas.pos.POSSaleVoid,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Void a Point of Sale transaction. Requires Manager or Admin role.
    Sets the sale status to VOIDED and records the reason.
    Note: This does NOT automatically re-adjust stock.
    '''
    # Service layer handles if sale exists and if it can be voided.
    voided_sale = services.pos_service.void_pos_sale(
        db, sale_id=sale_id, reason=void_in.void_reason, voiding_user_id=current_user.id
    )
    if not voided_sale: # Should be caught by service, but as a safeguard if service returns None for not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="POS Sale not found for voiding")
    return voided_sale
