from sqlalchemy.orm import Session
from app import models, schemas
from app.services import room_service # Use the actual service

def create_random_room(db: Session, room_number_suffix: str = "A") -> models.Room:
    room_in = schemas.RoomCreate(
        room_number=f"101{room_number_suffix}",
        name=f"Test Room {room_number_suffix}",
        description="A nice test room",
        price=150.00,
        type="Double",
        status="Available",
        floor=1
    )
    return room_service.create_room(db=db, room_in=room_in)
