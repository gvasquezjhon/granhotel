from pydantic import BaseModel, Field, model_validator # Added model_validator for Pydantic v2
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
import uuid

from app.models.billing import FolioStatus, FolioTransactionType
from .guest import Guest as GuestSchema
from .reservations import Reservation as ReservationSchema
# POSSaleItemSchema is not directly used here, but POSSale might be linked.
# For FolioTransaction, we'd link to POSSale schema if we want to show full sale details.
# For now, keeping it simple with related_pos_sale_id.
from .pos import POSSale as POSSaleSchema
from .user import User as UserSchema

# FolioTransaction Schemas
class FolioTransactionBase(BaseModel):
    description: str
    charge_amount: Decimal = Field(Decimal("0.00"), ge=0)
    payment_amount: Decimal = Field(Decimal("0.00"), ge=0)
    transaction_type: FolioTransactionType
    transaction_date: Optional[datetime] = None # Defaults to now in service/model

    related_pos_sale_id: Optional[int] = None
    related_reservation_id: Optional[int] = None

    # Pydantic v2 style model_validator
    @model_validator(mode='before')
    @classmethod
    def check_charge_or_payment_set(cls, data: Any) -> Any:
        if isinstance(data, dict): # Ensure data is a dict (for model_validator mode='before')
            charge = data.get('charge_amount', Decimal("0.00"))
            payment = data.get('payment_amount', Decimal("0.00"))

            # Convert to Decimal if they are strings from input
            if isinstance(charge, str): charge = Decimal(charge)
            if isinstance(payment, str): payment = Decimal(payment)

            if charge > Decimal("0.00") and payment > Decimal("0.00"):
                raise ValueError("Transaction cannot be both a charge and a payment.")
            # Allow zero amount for adjustments/notes (e.g. if transaction_type indicates this)
            # if charge == Decimal("0.00") and payment == Decimal("0.00") and \
            #    data.get('transaction_type') not in [FolioTransactionType.DISCOUNT_ADJUSTMENT]: # Example
            #     raise ValueError("Either charge_amount or payment_amount must be set for most transaction types.")
        return data

class FolioTransactionCreate(FolioTransactionBase):
    # guest_folio_id will be path param or determined by service
    # created_by_user_id will be set from current_user
    pass

class FolioTransaction(FolioTransactionBase): # Response schema
    id: int
    guest_folio_id: int
    transaction_date: datetime
    created_at: datetime
    created_by: Optional[UserSchema] = None
    pos_sale: Optional[POSSaleSchema] = None # If we want to show some POS sale details

    class Config:
        from_attributes = True

class FolioStatusUpdate(BaseModel):
    status: FolioStatus

# GuestFolio Schemas
class GuestFolioBase(BaseModel):
    guest_id: uuid.UUID
    reservation_id: Optional[int] = None
    status: FolioStatus = FolioStatus.OPEN
    # Totals are calculated and managed by the service

class GuestFolioCreate(GuestFolioBase):
    pass

class GuestFolioUpdate(BaseModel):
    status: Optional[FolioStatus] = None
    # Manual adjustment of totals is discouraged; use transactions.

class GuestFolio(GuestFolioBase): # Main response schema
    id: int
    total_charges: Decimal
    total_payments: Decimal
    balance: Decimal
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    guest: Optional[GuestSchema] = None
    reservation: Optional[ReservationSchema] = None
    transactions: List[FolioTransaction] = []

    class Config:
        from_attributes = True
