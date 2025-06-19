from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app import schemas, models, services
from app.api import deps # For authentication/authorization
from app.db import session as db_session

router = APIRouter()

@router.post("/", response_model=schemas.inventory.Supplier, status_code=status.HTTP_201_CREATED)
def create_new_supplier_api(
    *,
    db: Session = Depends(db_session.get_db),
    supplier_in: schemas.inventory.SupplierCreate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Create a new supplier. Requires Manager or Admin role.
    '''
    # Service handles unique name/email checks and raises HTTPException if needed
    supplier = services.supplier_service.create_supplier(db=db, supplier_in=supplier_in)
    return supplier

@router.get("/", response_model=List[schemas.inventory.Supplier])
def read_all_suppliers_api(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user) # Any active user can view suppliers
) -> Any:
    '''
    Retrieve all suppliers.
    '''
    suppliers = services.supplier_service.get_all_suppliers(db=db, skip=skip, limit=limit)
    return suppliers

@router.get("/{supplier_id}", response_model=schemas.inventory.Supplier)
def read_single_supplier_api(
    *,
    db: Session = Depends(db_session.get_db),
    supplier_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Retrieve a specific supplier by ID.
    '''
    supplier = services.supplier_service.get_supplier(db, supplier_id=supplier_id)
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return supplier

@router.put("/{supplier_id}", response_model=schemas.inventory.Supplier)
def update_existing_supplier_api(
    *,
    db: Session = Depends(db_session.get_db),
    supplier_id: int,
    supplier_in: schemas.inventory.SupplierUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Update an existing supplier. Requires Manager or Admin role.
    '''
    supplier_db_obj = services.supplier_service.get_supplier(db, supplier_id=supplier_id)
    if not supplier_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found for update")

    updated_supplier = services.supplier_service.update_supplier(
        db=db, supplier_db_obj=supplier_db_obj, supplier_in=supplier_in
    )
    return updated_supplier

@router.delete("/{supplier_id}", response_model=schemas.inventory.Supplier)
def delete_existing_supplier_api(
    *,
    db: Session = Depends(db_session.get_db),
    supplier_id: int,
    current_user: models.User = Depends(deps.require_admin_user) # Admin only for deletion
) -> Any:
    '''
    Delete a supplier. Requires Admin role.
    Supplier must not have associated purchase orders.
    '''
    # Service handles check for associated POs and raises HTTPException if not empty
    deleted_supplier = services.supplier_service.delete_supplier(db=db, supplier_id=supplier_id)
    if not deleted_supplier: # If supplier itself was not found (service returns None)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found for deletion")
    return deleted_supplier
