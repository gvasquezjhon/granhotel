from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict # Added Dict
from decimal import Decimal # Added Decimal

from app import schemas, models, services
from app.api import deps
from app.db import session as db_session

router = APIRouter()

@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_new_product(
    *,
    db: Session = Depends(db_session.get_db),
    product_in: schemas.ProductCreate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Create a new product. Requires Manager or Admin role.'''
    # Service handles category existence and unique SKU checks
    product = services.product_service.create_product(db=db, product_in=product_in)
    return product

@router.get("/", response_model=List[schemas.Product])
def read_all_products(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    name: Optional[str] = Query(None, description="Filter by product name (case-insensitive partial match)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    taxable: Optional[bool] = Query(None, description="Filter by taxable status"),
    current_user: models.User = Depends(deps.get_current_active_user) # Open to any active user
) -> Any:
    '''Retrieve all products with optional filters.'''
    products = services.product_service.get_products(
        db, skip=skip, limit=limit, category_id=category_id, name=name, is_active=is_active, taxable=taxable
    )
    return products

@router.get("/{product_id}", response_model=schemas.Product)
def read_single_product(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''Retrieve a specific product by ID.'''
    product = services.product_service.get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.Product)
def update_existing_product(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    product_in: schemas.ProductUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Update an existing product. Requires Manager or Admin role.'''
    product_db_obj = services.product_service.get_product(db, product_id=product_id)
    if not product_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found for update")
    # Service handles validation for category_id, SKU uniqueness etc.
    updated_product = services.product_service.update_product(
        db=db, product_db_obj=product_db_obj, product_in=product_in
    )
    return updated_product

@router.delete("/{product_id}", response_model=schemas.Product)
def delete_existing_product(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    current_user: models.User = Depends(deps.require_admin_user) # Stricter: Admin only for deletion
) -> Any:
    '''Delete a product. Requires Admin role.'''
    deleted_product = services.product_service.delete_product(db=db, product_id=product_id)
    if not deleted_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found for deletion")
    return deleted_product

@router.get("/{product_id}/price-details", response_model=Dict[str, Any])
def get_product_price_with_tax_api(
    *,
    db: Session = Depends(db_session.get_db),
    product_id: int,
    quantity: int = Query(1, gt=0, description="Quantity of the product"),
    current_user: models.User = Depends(deps.get_current_active_user) # Open for price checks
) -> Any:
    '''
    Get calculated price details for a product, including tax.
    '''
    # service.get_product_price_details raises HTTPException if product not found or quantity invalid
    price_details = services.product_service.get_product_price_details(db, product_id=product_id, quantity=quantity)
    # The service now returns a dict that should be directly convertible by FastAPI
    return price_details
