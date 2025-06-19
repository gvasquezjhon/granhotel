from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..db.base_class import Base # Assuming base_class.py will be created

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False) # Consider a separate RoomType table later
    status = Column(String, default="Available", nullable=False)
    floor = Column(Integer, nullable=True)
    building = Column(String, nullable=True)
    # Add created_at, updated_at later as per guidelines
