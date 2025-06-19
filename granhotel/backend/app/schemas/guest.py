from pydantic import BaseModel, EmailStr, field_validator, constr
from typing import Optional
from datetime import datetime
from ..models.guest import DocumentType # Import the enum from models

# Shared properties
class GuestBase(BaseModel):
    first_name: str
    last_name: str
    document_type: Optional[DocumentType] = None
    document_number: Optional[constr(min_length=8, max_length=20)] = None # Basic length validation
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state_province: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = "Perú"
    nationality: Optional[str] = "Peruana"
    preferences: Optional[str] = None
    is_blacklisted: bool = False

    # Basic validation for DNI/RUC (can be improved with specific regex)
    @field_validator('document_number', mode='before') # Use 'before' for Pydantic v2
    @classmethod
    def validate_document_number_general_length(cls, v: Optional[str]): # Renamed for clarity
        # This validator is simplified. For Pydantic v2, to access other fields for conditional validation (e.g. based on document_type),
        # you would typically use a `model_validator`.
        # e.g. from pydantic import model_validator
        # @model_validator(mode='before')
        # def check_document_logic(cls, data: Any) -> Any:
        #    if isinstance(data, dict):
        #        doc_type = data.get('document_type')
        #        doc_num = data.get('document_number')
        #        if doc_type == DocumentType.DNI and doc_num and len(doc_num) != 8:
        #            raise ValueError("DNI must be 8 characters long")
        #        # etc.
        #    return data
        #
        # For this field_validator, we'll stick to the provided simple length check on the field itself.
        if v is not None and not (8 <= len(v) <= 20): # General length check
             raise ValueError("Document number length (8-20 chars) is invalid.")
        return v


# Properties to receive on guest creation
class GuestCreate(GuestBase):
    pass # All fields from GuestBase are creatable by default

# Properties to receive on guest update
class GuestUpdate(GuestBase):
    # Allow optional updates for all fields from GuestBase
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # is_blacklisted can be updated directly, already bool in base
    # document_type, document_number, email, etc are already Optional in GuestBase

# Properties shared by models stored in DB
class GuestInDBBase(GuestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic V2

# Properties to return to client
class Guest(GuestInDBBase):
    pass # All fields from GuestInDBBase are returned

# Properties stored in DB
class GuestInDB(GuestInDBBase):
    pass
