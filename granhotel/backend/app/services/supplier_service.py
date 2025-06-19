from sqlalchemy.orm import Session
from typing import List, Optional

from app import models
from app import schemas
from fastapi import HTTPException, status

def create_supplier(db: Session, supplier_in: schemas.SupplierCreate) -> models.inventory.Supplier:
    '''Create a new supplier.'''
    existing_supplier_by_name = db.query(models.inventory.Supplier).filter(models.inventory.Supplier.name == supplier_in.name).first()
    if existing_supplier_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with name '{supplier_in.name}' already exists."
        )
    if supplier_in.email: # Ensure email is provided before checking
        existing_supplier_by_email = db.query(models.inventory.Supplier).filter(models.inventory.Supplier.email == supplier_in.email).first()
        if existing_supplier_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with email '{supplier_in.email}' already exists."
            )

    db_supplier = models.inventory.Supplier(**supplier_in.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def get_supplier(db: Session, supplier_id: int) -> Optional[models.inventory.Supplier]:
    '''Retrieve a supplier by ID.'''
    return db.query(models.inventory.Supplier).filter(models.inventory.Supplier.id == supplier_id).first()

def get_all_suppliers(db: Session, skip: int = 0, limit: int = 100) -> List[models.inventory.Supplier]:
    '''Retrieve all suppliers with pagination.'''
    return db.query(models.inventory.Supplier).order_by(models.inventory.Supplier.name).offset(skip).limit(limit).all()

def update_supplier(
    db: Session, supplier_db_obj: models.inventory.Supplier, supplier_in: schemas.SupplierUpdate
) -> models.inventory.Supplier:
    '''Update an existing supplier.'''
    update_data = supplier_in.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != supplier_db_obj.name:
        existing_supplier_name = db.query(models.inventory.Supplier).filter(models.inventory.Supplier.name == update_data["name"]).first()
        if existing_supplier_name and existing_supplier_name.id != supplier_db_obj.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another supplier with name '{update_data['name']}' already exists."
            )

    if "email" in update_data and update_data["email"] and update_data["email"] != supplier_db_obj.email:
        # Ensure email is not None before querying
        if update_data["email"] is not None: # Check if email is not None
            existing_supplier_email = db.query(models.inventory.Supplier).filter(models.inventory.Supplier.email == update_data["email"]).first()
            if existing_supplier_email and existing_supplier_email.id != supplier_db_obj.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Another supplier with email '{update_data['email']}' already exists."
                )
        # If email in update_data is explicitly set to None (to clear it), allow it if model supports nullable email.
        # The current model has email as unique=True, index=True, nullable=True.
        # So, setting to None should be fine, and the unique constraint won't apply to multiple Nulls (in most DBs).

    for field, value in update_data.items():
        setattr(supplier_db_obj, field, value)

    db.add(supplier_db_obj)
    db.commit()
    db.refresh(supplier_db_obj)
    return supplier_db_obj

def delete_supplier(db: Session, supplier_id: int) -> Optional[models.inventory.Supplier]:
    '''Delete a supplier. Ensures supplier has no associated purchase orders.'''
    supplier_to_delete = get_supplier(db, supplier_id)
    if not supplier_to_delete:
        return None

    if supplier_to_delete.purchase_orders: # Check the relationship
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete supplier '{supplier_to_delete.name}' as they have associated purchase orders. Please reassign or delete these orders first."
        )

    db.delete(supplier_to_delete)
    db.commit()
    return supplier_to_delete
