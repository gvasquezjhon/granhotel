from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

# Corrected relative imports assuming 'backend' is the root for PYTHONPATH
from app import schemas
from app import models
from app.db import session as db_session
from app.services import room_service

router = APIRouter()

@router.post("/", response_model=schemas.Room, status_code=status.HTTP_201_CREATED)
def create_room(
    *,
    db: Session = Depends(db_session.get_db),
    room_in: schemas.RoomCreate,
) -> models.Room: # Added type hint for return
    existing_room = room_service.get_room_by_room_number(db, room_number=room_in.room_number)
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room with number '{room_in.room_number}' already exists."
        )
    room = room_service.create_room(db=db, room_in=room_in)
    return room

@router.get("/", response_model=List[schemas.Room])
def read_rooms(
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[models.Room]: # Added type hint for return
    rooms = room_service.get_rooms(db, skip=skip, limit=limit)
    return rooms

@router.get("/{room_id}", response_model=schemas.Room)
def read_room(
    *,
    db: Session = Depends(db_session.get_db),
    room_id: int,
) -> models.Room: # Added type hint for return
    room = room_service.get_room(db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room

@router.put("/{room_id}", response_model=schemas.Room)
def update_room_endpoint( # Renamed to avoid conflict with service function
    *,
    db: Session = Depends(db_session.get_db),
    room_id: int,
    room_in: schemas.RoomUpdate,
) -> models.Room: # Added type hint for return
    room_db = room_service.get_room(db, room_id=room_id)
    if not room_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    if room_in.room_number and room_in.room_number != room_db.room_number:
        existing_room = room_service.get_room_by_room_number(db, room_number=room_in.room_number)
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room with number '{room_in.room_number}' already exists for another room."
            )
    updated_room = room_service.update_room(db=db, room_db_obj=room_db, room_in=room_in)
    return updated_room

@router.delete("/{room_id}", response_model=schemas.Room)
def delete_room_endpoint( # Renamed to avoid conflict
    *,
    db: Session = Depends(db_session.get_db),
    room_id: int,
) -> models.Room: # Added type hint for return
    room = room_service.get_room(db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    deleted_room = room_service.delete_room(db=db, room_id=room_id)
    if not deleted_room: # Should not happen if found above, but good practice
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found for deletion")
    return deleted_room
