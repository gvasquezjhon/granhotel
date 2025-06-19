import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Numeric, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PGEnum # For PostgreSQL specific ENUM type if SAEnum is not sufficient
from ..db.base_class import Base
from sqlalchemy.sql.expression import text # For server_default with text

# --- Enums ---
class PurchaseOrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"

class StockMovementType(str, enum.Enum):
    INITIAL_STOCK = "INITIAL_STOCK"
    SALE = "SALE"
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    ADJUSTMENT_INCREASE = "ADJUSTMENT_INCREASE"
    ADJUSTMENT_DECREASE = "ADJUSTMENT_DECREASE"
    RETURN_TO_SUPPLIER = "RETURN_TO_SUPPLIER"
    CUSTOMER_RETURN = "CUSTOMER_RETURN"
    INTERNAL_USE = "INTERNAL_USE"


# --- Models ---
class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, index=True, nullable=False)
    contact_person = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False, index=True)
    quantity_on_hand = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, nullable=True, default=0)
    last_restocked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", backref="inventory_item_assoc")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    order_date = Column(Date, server_default=func.current_date(), nullable=False) # Changed default to server_default
    expected_delivery_date = Column(Date, nullable=True)
    # Using SAEnum for direct mapping to Python enum and native DB enum if supported
    status = Column(PGEnum(PurchaseOrderStatus, name="po_status_enum", create_type=True),
                    nullable=False, default=PurchaseOrderStatus.PENDING, server_default=PurchaseOrderStatus.PENDING.value)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    quantity_received = Column(Integer, default=0, nullable=False)
    unit_price_paid = Column(Numeric(10, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    stock_movements = relationship("StockMovement", back_populates="purchase_order_item_ref")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity_changed = Column(Integer, nullable=False)
    # Using SAEnum for direct mapping
    movement_type = Column(PGEnum(StockMovementType, name="sm_type_enum", create_type=True), nullable=False)
    movement_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reason = Column(String(255), nullable=True)

    purchase_order_item_id = Column(Integer, ForeignKey("purchase_order_items.id"), nullable=True)
    # related_pos_transaction_id = Column(Integer, ForeignKey("pos_transactions.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # No updated_at for stock movements typically

    product = relationship("Product")
    purchase_order_item_ref = relationship("PurchaseOrderItem", back_populates="stock_movements")

# Removed EnumTable models as per decision to use SAEnum/PGEnum directly.
