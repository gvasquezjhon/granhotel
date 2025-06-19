from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
import random # Added import
import string # Added import

from app import models, schemas, services
# from app.models.user import UserRole # Not directly used in this util file
# from tests.utils.user import create_user_in_db # Not directly used in this util file

# Helper function for random strings (can be shared if needed)
def random_lower_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def create_random_product_category(db: Session, name_suffix: str = "") -> models.ProductCategory:
    name = f"Test Category {name_suffix}{random_lower_string(4)}"
    # Ensure name is unique enough for tests, or handle potential conflicts
    existing_category = db.query(models.ProductCategory).filter(models.ProductCategory.name == name).first()
    if existing_category:
        name = f"{name}_{random_lower_string(2)}" # Append more random chars if collision

    category_in = schemas.ProductCategoryCreate(name=name, description=f"Desc for {name}")
    return services.product_service.create_product_category(db=db, category_in=category_in)

def create_random_product(
    db: Session,
    category_id: Optional[int] = None,
    name_suffix: str = "",
    price: Optional[Decimal] = None,
    sku: Optional[str] = None,
    is_active: bool = True,
    taxable: bool = True
) -> models.Product:
    if category_id is None:
        category = create_random_product_category(db, name_suffix=f"_prod_cat_util{name_suffix}")
        category_id = category.id

    name = f"Test Product {name_suffix}{random_lower_string(4)}"
    # Ensure SKU is unique enough for tests
    product_sku = sku or f"SKU{name_suffix}{random_lower_string(6).upper()}"
    existing_product_sku = db.query(models.Product).filter(models.Product.sku == product_sku).first()
    if existing_product_sku:
        product_sku = f"{product_sku}_{random_lower_string(2)}"


    product_price = price if price is not None else Decimal(str(random.randint(10, 100))) + Decimal("0.99")

    product_in = schemas.ProductCreate(
        name=name,
        description=f"Description for {name}",
        price=product_price,
        sku=product_sku,
        is_active=is_active,
        taxable=taxable,
        category_id=category_id,
        image_url=f"http://example.com/{name.replace(' ', '_')}.jpg" # Add example image_url
    )
    return services.product_service.create_product(db=db, product_in=product_in)
