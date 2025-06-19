from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid # For UUID type hint
from app.models.user import UserRole # Import UserRole enum

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.RECEPTIONIST

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# Properties to receive via API on update
class UserUpdate(BaseModel): # Allow partial updates
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8) # Optional password update

# Properties shared by models stored in DB that are safe to return
class UserInDBBase(UserBase):
    id: uuid.UUID # Use uuid.UUID for type hint
    created_at: datetime
    updated_at: datetime
    # Note: hashed_password is not included here

    class Config:
        from_attributes = True

# Properties to return to client (API response)
class User(UserInDBBase):
    # This schema is what's typically returned by API endpoints.
    # It inherits fields from UserInDBBase (id, email, first_name, last_name, is_active, role, created_at, updated_at)
    pass

# Properties stored in DB, including sensitive ones like hashed_password
class UserInDB(UserInDBBase):
    hashed_password: str
    # This schema represents the full user object as stored in the database.
    # It's typically used internally, not directly returned by APIs.
    pass
