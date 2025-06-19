from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime # Add datetime

class RoomBase(BaseModel):
    room_number: str
    name: str
    description: Optional[str] = None
    price: float
    type: str
    status: str = "Available"
    floor: Optional[int] = None
    building: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class RoomUpdate(RoomBase):
    room_number: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    type: Optional[str] = None
    status: Optional[str] = None
    # updated_at will be set by the server

class Room(RoomBase):
    id: int
    created_at: datetime # Add created_at
    updated_at: datetime # Add updated_at

    class Config:
        # Pydantic V2 uses `from_attributes` instead of `orm_mode`
        from_attributes = True
