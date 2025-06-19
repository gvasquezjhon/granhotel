from sqlalchemy import Column, Integer, String, Float, DateTime # Added DateTime
from sqlalchemy.sql import func # Added func
from ..db.base_class import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default="Available", nullable=False)
    floor = Column(Integer, nullable=True)
    building = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
