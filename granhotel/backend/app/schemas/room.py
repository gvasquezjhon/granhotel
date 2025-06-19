from pydantic import BaseModel
from typing import Optional, List

class RoomBase(BaseModel):
    room_number: str
    name: str
    description: Optional[str] = None
    price: float
    type: str  # e.g., Single, Double, Suite
    status: str = "Available"  # Available, Occupied, Maintenance, Cleaning
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

class Room(RoomBase):
    id: int

    class Config:
        orm_mode = True # Changed from from_attributes = True for SQLAlchemy < 2.0 compatibility if needed
