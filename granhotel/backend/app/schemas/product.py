from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from decimal import Decimal # For price

# ProductCategory Schemas
class ProductCategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class ProductCategoryCreate(ProductCategoryBase):
    pass

class ProductCategoryUpdate(BaseModel): # Allow partial updates for all fields
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None

class ProductCategoryInDBBase(ProductCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductCategory(ProductCategoryInDBBase):
    pass # For now, same as InDBBase for responses

# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2) # Price must be positive
    sku: Optional[str] = Field(None, max_length=50)
    image_url: Optional[HttpUrl] = None # Validate as URL
    is_active: bool = True
    taxable: bool = True
    category_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel): # Allow partial updates
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    sku: Optional[str] = Field(None, max_length=50) # Allow clearing SKU by passing None
    image_url: Optional[HttpUrl] = None # Allow clearing image_url
    is_active: Optional[bool] = None
    taxable: Optional[bool] = None
    category_id: Optional[int] = None

class ProductInDBBase(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategory] = None # Nest category details in product response

    class Config:
        from_attributes = True

class Product(ProductInDBBase):
    pass # For now, same as InDBBase for responses

# Schema for Product with its category for richer listings if needed without full nesting
# This is an example, could be achieved by modifying Product schema or via a separate endpoint/service logic
# For now, Product already nests the ProductCategory object.
# If only category_name was needed, a different approach might be used.
# class ProductWithCategoryName(Product):
#     category_name: Optional[str] = None
#
# This can be removed for now as Product nests the full category object.
# If specific derived fields are needed, they can be added to the main `Product` schema using @computed_field or similar.
