from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # Added length
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), index=True, nullable=False) # Added length
    description = Column(Text, nullable=True)
    # Using Numeric for price to handle currency precisely
    price = Column(Numeric(10, 2), nullable=False) # Example: 10 total digits, 2 after decimal

    sku = Column(String(50), unique=True, index=True, nullable=True) # Stock Keeping Unit, added length
    image_url = Column(String(2048), nullable=True) # Added length for URLs
    is_active = Column(Boolean, default=True, nullable=False)
    taxable = Column(Boolean, default=True, nullable=False) # True if IGV applies

    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category = relationship("ProductCategory", back_populates="products")
    # Add relationships to InventoryItem or OrderItem later if needed
