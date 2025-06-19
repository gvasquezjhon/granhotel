from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Optional
from datetime import datetime, date
from decimal import Decimal # For total_price

from app.models.reservation import ReservationStatus # Import enum
from .guest import Guest # To nest guest info in response
from .room import Room # To nest room info in response

# Shared properties
class ReservationBase(BaseModel):
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    status: ReservationStatus = ReservationStatus.PENDING
    total_price: Optional[Decimal] = None # Price might be set by backend logic
    notes: Optional[str] = None

    @field_validator('check_out_date')
    def check_out_date_after_check_in_date(cls, v: date, info: ValidationInfo):
        if 'check_in_date' in info.data and v <= info.data['check_in_date']:
            raise ValueError("Check-out date must be after check-in date")
        return v

# Properties to receive on reservation creation
class ReservationCreate(ReservationBase):
    # total_price can be omitted on creation, to be calculated by backend
    pass

# Properties to receive on reservation update
class ReservationUpdate(BaseModel): # Not inheriting from ReservationBase to allow partial updates
    guest_id: Optional[int] = None
    room_id: Optional[int] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    status: Optional[ReservationStatus] = None
    total_price: Optional[Decimal] = None
    notes: Optional[str] = None

    @field_validator('check_out_date')
    def check_out_date_after_check_in_date_update(cls, v: Optional[date], info: ValidationInfo):
        # Only validate if both dates are present in the update payload
        if v is not None and 'check_in_date' in info.data and info.data['check_in_date'] is not None:
            if v <= info.data['check_in_date']:
                raise ValueError("Check-out date must be after check-in date")
        # If only check_out_date is provided, we can't validate against check_in_date from this validator alone.
        # A model_validator would be needed if we need to fetch guest_db_obj.check_in_date to compare.
        # For now, this field_validator only works if check_in_date is also part of the update payload.
        return v

# Properties shared by models stored in DB
class ReservationInDBBase(ReservationBase):
    id: int
    reservation_date: datetime
    created_at: datetime
    updated_at: datetime

    # Include guest and room details for richer responses
    # These will be populated if the ORM relationship is loaded
    guest: Optional[Guest] = None
    room: Optional[Room] = None

    class Config:
        from_attributes = True # Pydantic V2

# Properties to return to client
class Reservation(ReservationInDBBase):
    pass

# Properties stored in DB
class ReservationInDB(ReservationInDBBase):
    pass
