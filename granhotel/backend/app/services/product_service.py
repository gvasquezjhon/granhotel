from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any # Added Any for return type
from decimal import Decimal, ROUND_HALF_UP # For precise tax calculation

from app import models
from app import schemas
from app.models.product import Product, ProductCategory
from fastapi import HTTPException, status

# --- ProductCategory Services ---

def create_product_category(db: Session, category_in: schemas.ProductCategoryCreate) -> models.ProductCategory:
    '''Create a new product category.'''
    existing_category = db.query(models.ProductCategory).filter(models.ProductCategory.name == category_in.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product category with name '{category_in.name}' already exists."
        )
    db_category = models.ProductCategory(**category_in.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_product_category(db: Session, category_id: int) -> Optional[models.ProductCategory]:
    '''Retrieve a product category by ID.'''
    return db.query(models.ProductCategory).filter(models.ProductCategory.id == category_id).first()

def get_all_product_categories(db: Session, skip: int = 0, limit: int = 100) -> List[models.ProductCategory]:
    '''Retrieve all product categories with pagination.'''
    return db.query(models.ProductCategory).order_by(models.ProductCategory.name).offset(skip).limit(limit).all()

def update_product_category(
    db: Session, category_db_obj: models.ProductCategory, category_in: schemas.ProductCategoryUpdate
) -> models.ProductCategory:
    '''Update an existing product category.'''
    update_data = category_in.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != category_db_obj.name:
        existing_category = db.query(models.ProductCategory).filter(models.ProductCategory.name == update_data["name"]).first()
        if existing_category and existing_category.id != category_db_obj.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another product category with name '{update_data['name']}' already exists."
            )

    for field, value in update_data.items():
        setattr(category_db_obj, field, value)

    db.add(category_db_obj)
    db.commit()
    db.refresh(category_db_obj)
    return category_db_obj

def delete_product_category(db: Session, category_id: int) -> Optional[models.ProductCategory]:
    '''Delete a product category. Ensures category is empty before deletion.'''
    category_to_delete = get_product_category(db, category_id)
    if not category_to_delete:
        return None # Or raise 404 in API layer

    if category_to_delete.products: # Check if there are any products in this category
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{category_to_delete.name}' as it contains products. Please reassign or delete products first."
        )

    db.delete(category_to_delete)
    db.commit()
    return category_to_delete


# --- Product Services ---

def create_product(db: Session, product_in: schemas.ProductCreate) -> models.Product:
    '''Create a new product.'''
    category = get_product_category(db, product_in.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with ID {product_in.category_id} not found."
        )

    if product_in.sku: # Check SKU only if provided
        existing_product_sku = db.query(models.Product).filter(models.Product.sku == product_in.sku).first()
        if existing_product_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{product_in.sku}' already exists."
            )

    db_product_data = product_in.model_dump()
    # Price is already Decimal from Pydantic schema
    db_product = models.Product(**db_product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    '''Retrieve a product by ID, including its category (if accessed).'''
    return db.query(models.Product).options(
        joinedload(models.Product.category) # Eager load category for Product schema
    ).filter(models.Product.id == product_id).first()

def get_products(
    db: Session, skip: int = 0, limit: int = 100,
    category_id: Optional[int] = None,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    taxable: Optional[bool] = None
) -> List[models.Product]:
    '''Retrieve products with filtering and pagination.'''
    query = db.query(models.Product).options(joinedload(models.Product.category))

    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if name:
        query = query.filter(models.Product.name.ilike(f"%{name}%"))
    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)
    if taxable is not None:
        query = query.filter(models.Product.taxable == taxable)

    return query.order_by(models.Product.name).offset(skip).limit(limit).all()

def update_product(
    db: Session, product_db_obj: models.Product, product_in: schemas.ProductUpdate
) -> models.Product:
    '''Update an existing product.'''
    update_data = product_in.model_dump(exclude_unset=True)

    if "category_id" in update_data and update_data["category_id"] != product_db_obj.category_id:
        category = get_product_category(db, update_data["category_id"])
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product category with ID {update_data['category_id']} not found."
            )

    if "sku" in update_data and update_data["sku"] and update_data["sku"] != product_db_obj.sku:
        existing_product_sku = db.query(models.Product).filter(models.Product.sku == update_data["sku"]).first()
        if existing_product_sku and existing_product_sku.id != product_db_obj.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another product with SKU '{update_data['sku']}' already exists."
            )

    for field, value in update_data.items():
        setattr(product_db_obj, field, value)

    db.add(product_db_obj)
    db.commit()
    db.refresh(product_db_obj)
    return product_db_obj

def delete_product(db: Session, product_id: int) -> Optional[models.Product]:
    '''
    Delete a product.
    (Currently hard delete. Consider soft delete: product.is_active = False)
    '''
    product_to_delete = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product_to_delete:
        return None

    db.delete(product_to_delete)
    db.commit()
    return product_to_delete

# Peruvian IGV is 18%
IGV_RATE = Decimal("0.18")

def calculate_product_price_with_tax(product: models.Product, quantity: int = 1) -> Dict[str, Any]: # Changed return type for product_id
    '''
    Calculate the price for a given quantity of a product, including IGV if applicable.
    Returns a dictionary with subtotal, tax_amount, and total_with_tax.
    '''
    if not isinstance(quantity, int) or quantity < 1:
        raise ValueError("Quantity must be a positive integer.")

    subtotal = product.price * Decimal(quantity)
    tax_amount = Decimal("0.00")

    if product.taxable:
        tax_amount = (subtotal * IGV_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    total_with_tax = subtotal + tax_amount

    return {
        "product_id": product.id, # product.id is int, no need for Decimal()
        "product_name": product.name,
        "quantity": Decimal(quantity), # Keep quantity as Decimal for consistency in financial dict
        "unit_price": product.price,
        "subtotal": subtotal,
        "tax_rate": IGV_RATE if product.taxable else Decimal("0.00"),
        "tax_amount": tax_amount,
        "total_with_tax": total_with_tax
    }

def get_product_price_details(db: Session, product_id: int, quantity: int = 1) -> Optional[Dict[str, Any]]:
    '''Helper to get a product and then calculate its price details.'''
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found.")

    if not isinstance(quantity, int) or quantity < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be a positive integer.")

    return calculate_product_price_with_tax(product, quantity)
