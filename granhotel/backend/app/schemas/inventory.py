from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from .product import Product # For nesting in responses
from app.models.inventory import PurchaseOrderStatus, StockMovementType # Import enums

# Supplier Schemas
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None # Using str for Text model field

class SupplierCreate(SupplierBase): pass

class SupplierUpdate(BaseModel): # Allow full partial updates
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None

class Supplier(SupplierBase): # Response model
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

# InventoryItem Schemas
class InventoryItemBase(BaseModel):
    product_id: int
    quantity_on_hand: int = Field(..., ge=0) # Must be greater than or equal to 0
    low_stock_threshold: Optional[int] = Field(0, ge=0) # Default to 0, must be >= 0

class InventoryItemCreate(InventoryItemBase):
    # Usually created internally when a product is first added, or via an initial stock movement.
    # This schema can be used for explicit creation if needed.
    pass

class InventoryItemUpdate(BaseModel): # For updating threshold or direct stock adjustment (via service)
    quantity_on_hand: Optional[int] = Field(None, ge=0) # Service should handle logic for this
    low_stock_threshold: Optional[int] = Field(None, ge=0)

class InventoryItem(InventoryItemBase): # Response model
    id: int
    last_restocked_at: Optional[datetime] = None
    product: Optional[Product] = None # Nested product info
    updated_at: datetime # From model
    created_at: datetime # From model
    class Config: from_attributes = True

class InventoryAdjustment(BaseModel): # For manual stock changes via a dedicated endpoint
    quantity_changed: int # Positive for increase, negative for decrease. Not zero.
    reason: Optional[str] = Field(None, max_length=255)
    # movement_type will be determined by service based on sign of quantity_changed
    # e.g. ADJUSTMENT_INCREASE or ADJUSTMENT_DECREASE

    @field_validator('quantity_changed')
    def quantity_not_zero(cls, v):
        if v == 0:
            raise ValueError("Quantity changed cannot be zero for an adjustment.")
        return v

# PurchaseOrderItem Schemas
class PurchaseOrderItemBase(BaseModel):
    product_id: int
    quantity_ordered: int = Field(..., gt=0) # Must be greater than 0
    unit_price_paid: Optional[Decimal] = Field(None, gt=Decimal(0), decimal_places=2) # Must be > 0 if provided

class PurchaseOrderItemCreate(PurchaseOrderItemBase): pass

class PurchaseOrderItemUpdate(BaseModel): # Primarily for internal updates like quantity_received by a service
    quantity_received: Optional[int] = Field(None, ge=0) # Must be >= 0
    unit_price_paid: Optional[Decimal] = Field(None, gt=Decimal(0), decimal_places=2)


class PurchaseOrderItem(PurchaseOrderItemBase): # Response model for PO item
    id: int
    quantity_received: int
    product: Optional[Product] = None
    # created_at and updated_at could be added if needed in response
    class Config: from_attributes = True

# PurchaseOrder Schemas
class PurchaseOrderBase(BaseModel):
    supplier_id: int
    order_date: Optional[date] = None # Defaults to today in model
    expected_delivery_date: Optional[date] = None
    status: PurchaseOrderStatus = PurchaseOrderStatus.PENDING
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1) # Must have at least one item

class PurchaseOrderUpdate(BaseModel): # For status, notes, or expected_delivery_date update
    expected_delivery_date: Optional[date] = None
    status: Optional[PurchaseOrderStatus] = None
    notes: Optional[str] = None
    # Items are typically not updated directly on PO; new PO or adjustments to items handled differently.

class PurchaseOrder(PurchaseOrderBase): # Response model
    id: int
    supplier: Optional[Supplier] = None
    items: List[PurchaseOrderItem] = []
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

# Schema for receiving items against a PO line item
class PurchaseOrderItemReceive(BaseModel):
    quantity_received: int = Field(..., gt=0) # Quantity received in this specific transaction
    # movement_date can be implicit (now) or explicit if needed
    # reason for movement can be implicit ("PO Receipt") or explicit

# StockMovement Schemas
class StockMovementBase(BaseModel):
    product_id: int
    quantity_changed: int # Not zero. Positive for stock in, negative for stock out.
    movement_type: StockMovementType
    reason: Optional[str] = Field(None, max_length=255)
    purchase_order_item_id: Optional[int] = None
    # related_pos_transaction_id: Optional[int] = None

    @field_validator('quantity_changed')
    def stock_movement_quantity_not_zero(cls, v):
        if v == 0:
            raise ValueError("Stock movement quantity_changed cannot be zero.")
        return v

class StockMovementCreate(StockMovementBase): pass # Usually created internally by services

class StockMovement(StockMovementBase): # Response model
    id: int
    movement_date: datetime
    product: Optional[Product] = None
    # created_at from model (if it had one, current model does not for StockMovement)
    class Config: from_attributes = True

class InventoryItemLowStockThresholdUpdate(BaseModel):
    low_stock_threshold: int = Field(..., ge=0)

class PurchaseOrderStatusUpdate(BaseModel):
    status: PurchaseOrderStatus # The new status to set
