from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app import schemas, models, services
from app.api import deps # For authentication/authorization
from app.db import session as db_session

router = APIRouter()

@router.post("/", response_model=schemas.ProductCategory, status_code=status.HTTP_201_CREATED)
def create_new_product_category(
    *,
    db: Session = Depends(db_session.get_db),
    category_in: schemas.ProductCategoryCreate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user) # Example protection
) -> Any:
    '''Create a new product category. Requires Manager or Admin role.'''
    # Service handles unique name check and raises HTTPException if needed
    category = services.product_service.create_product_category(db=db, category_in=category_in)
    return category

@router.get("/", response_model=List[schemas.ProductCategory])
def read_all_product_categories(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user) # Open to any active user
) -> Any:
    '''Retrieve all product categories.'''
    categories = services.product_service.get_all_product_categories(db=db, skip=skip, limit=limit)
    return categories

@router.get("/{category_id}", response_model=schemas.ProductCategory)
def read_single_product_category(
    *,
    db: Session = Depends(db_session.get_db),
    category_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''Retrieve a specific product category by ID.'''
    category = services.product_service.get_product_category(db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found")
    return category

@router.put("/{category_id}", response_model=schemas.ProductCategory)
def update_existing_product_category(
    *,
    db: Session = Depends(db_session.get_db),
    category_id: int,
    category_in: schemas.ProductCategoryUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Update an existing product category. Requires Manager or Admin role.'''
    category_db_obj = services.product_service.get_product_category(db, category_id=category_id)
    if not category_db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found for update")
    # Service handles unique name check on update
    updated_category = services.product_service.update_product_category(
        db=db, category_db_obj=category_db_obj, category_in=category_in
    )
    return updated_category

@router.delete("/{category_id}", response_model=schemas.ProductCategory)
def delete_existing_product_category(
    *,
    db: Session = Depends(db_session.get_db),
    category_id: int,
    current_user: models.User = Depends(deps.require_admin_user) # Stricter: Admin only for deletion
) -> Any:
    '''Delete a product category. Requires Admin role. Category must be empty.'''
    # Service handles check for empty category and raises HTTPException if not empty
    deleted_category = services.product_service.delete_product_category(db=db, category_id=category_id)
    if not deleted_category: # If category itself was not found by the service (though service might raise 404 too)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product category not found for deletion")
    return deleted_category
