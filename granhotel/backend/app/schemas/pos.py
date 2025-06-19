from pydantic import BaseModel, Field, conlist
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.pos import PaymentMethod, POSSaleStatus
from .user import User as UserSchema
from .guest import Guest as GuestSchema
from .product import Product as ProductSchema

# POSSaleItem Schemas
class POSSaleItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    # unit_price_before_tax, tax_rate_applied, tax_amount_for_item, total_price_for_item_after_tax
    # will be calculated by the backend service. Client only sends product_id and quantity.

class POSSaleItemCreate(POSSaleItemBase):
    pass

class POSSaleItem(POSSaleItemBase): # Response schema for an item within a sale
    id: int
    unit_price_before_tax: Decimal
    tax_rate_applied: Decimal
    tax_amount_for_item: Decimal
    total_price_for_item_after_tax: Decimal
    product: Optional[ProductSchema] = None

    class Config:
        from_attributes = True

# POSSale Schemas
class POSSaleBase(BaseModel):
    guest_id: Optional[uuid.UUID] = None
    payment_method: PaymentMethod # Must be provided, even if PENDING_PAYMENT
    payment_reference: Optional[str] = Field(None, max_length=100)
    # status: POSSaleStatus = POSSaleStatus.PENDING_PAYMENT # Service might set initial status
    notes: Optional[str] = None
    # total_amount_before_tax, tax_amount, total_amount_after_tax are calculated by backend

class POSSaleCreate(BaseModel): # Different from Base for creation flexibility
    guest_id: Optional[uuid.UUID] = None
    payment_method: PaymentMethod
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    # cashier_user_id will be set from current_user in service/API
    items: conlist(POSSaleItemCreate, min_length=1) # Ensures at least one item

class POSSaleUpdate(BaseModel):
    # Limited updates typically allowed for a completed sale.
    # Voiding is a special action, not a generic update.
    # Payment details might be updatable if status was PENDING_PAYMENT.
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    # Status updates (like voiding) should have dedicated endpoints/service functions.

class POSSaleVoid(BaseModel): # Schema for voiding a sale
    void_reason: str = Field(..., min_length=5)


class POSSale(POSSaleBase): # Main response schema
    id: int
    sale_date: datetime
    cashier_user_id: uuid.UUID
    status: POSSaleStatus # Include status in response
    total_amount_before_tax: Decimal
    tax_amount: Decimal
    total_amount_after_tax: Decimal

    void_reason: Optional[str] = None
    voided_by_user_id: Optional[uuid.UUID] = None
    voided_at: Optional[datetime] = None

    items: List[POSSaleItem] = []
    cashier: Optional[UserSchema] = None
    guest: Optional[GuestSchema] = None
    # voided_by: Optional[UserSchema] = None

    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
