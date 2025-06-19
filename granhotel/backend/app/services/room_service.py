from sqlalchemy.orm import Session
from typing import List, Optional

from app import models
from app import schemas

def get_room(db: Session, room_id: int) -> Optional[models.Room]:
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_room_by_room_number(db: Session, room_number: str) -> Optional[models.Room]:
    return db.query(models.Room).filter(models.Room.room_number == room_number).first()

def get_rooms(db: Session, skip: int = 0, limit: int = 100) -> List[models.Room]:
    return db.query(models.Room).offset(skip).limit(limit).all()

def create_room(db: Session, room_in: schemas.RoomCreate) -> models.Room:
    # Ensure created_at and updated_at are handled if they are part of the model
    # For now, assuming they are auto-managed by DB or added later
    db_room = models.Room(**room_in.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def update_room(db: Session, room_db_obj: models.Room, room_in: schemas.RoomUpdate) -> models.Room:
    update_data = room_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Only update if the value is actually provided in the input (not None)
        # and also if the field exists in the model to prevent arbitrary attribute setting
        if hasattr(room_db_obj, field): # Check if field exists
             setattr(room_db_obj, field, value)

    # Handle updated_at timestamp if it's manually managed
    # if hasattr(room_db_obj, "updated_at"):
    #     room_db_obj.updated_at = datetime.utcnow()

    db.add(room_db_obj)
    db.commit()
    db.refresh(room_db_obj)
    return room_db_obj

def delete_room(db: Session, room_id: int) -> Optional[models.Room]:
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if db_room:
        # Implement soft delete later if required by setting a flag e.g. db_room.is_deleted = True
        db.delete(db_room)
        db.commit()
    return db_room
