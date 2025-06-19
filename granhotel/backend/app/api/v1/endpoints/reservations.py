from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import date

from app import schemas
from app import services # Will use app.services.reservation_service
from app.db import session as db_session
from app.models.reservation import ReservationStatus # For query param enum

router = APIRouter()

@router.post("/", response_model=schemas.Reservation, status_code=status.HTTP_201_CREATED)
def create_new_reservation_api( # Renamed to avoid conflict
    *,
    db: Session = Depends(db_session.get_db),
    reservation_in: schemas.ReservationCreate,
) -> Any:
    '''
    Create a new reservation.
    - Checks guest validity, room availability, and calculates price.
    '''
    # Service layer (create_reservation) handles HTTPExceptions for business logic errors
    reservation = services.reservation_service.create_reservation(db=db, reservation_in=reservation_in)
    return reservation

@router.get("/", response_model=List[schemas.Reservation])
def read_all_reservations_api( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    guest_id: Optional[int] = Query(None, description="Filter by Guest ID"),
    room_id: Optional[int] = Query(None, description="Filter by Room ID"),
    status: Optional[ReservationStatus] = Query(None, description="Filter by reservation status"),
    date_from: Optional[date] = Query(None, description="Filter reservations active on or after this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter reservations active on or before this date (YYYY-MM-DD)")
) -> Any:
    '''
    Retrieve a list of reservations with optional filters.
    Supports pagination. Dates `date_from` and `date_to` define a period;
    reservations active within any part of this period are returned.
    '''
    reservations = services.reservation_service.get_reservations(
        db, skip=skip, limit=limit,
        guest_id=guest_id, room_id=room_id, status=status,
        date_from=date_from, date_to=date_to
    )
    return reservations

@router.get("/{reservation_id}", response_model=schemas.Reservation)
def read_single_reservation_api( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    reservation_id: int,
) -> Any:
    '''
    Retrieve a specific reservation by its ID.
    Includes guest and room details.
    '''
    reservation = services.reservation_service.get_reservation(db, reservation_id=reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    return reservation

@router.put("/{reservation_id}", response_model=schemas.Reservation)
def update_existing_reservation_api( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    reservation_id: int,
    reservation_in: schemas.ReservationUpdate,
) -> Any:
    '''
    Update an existing reservation's details.
    - If dates/room change, checks availability and recalculates price.
    '''
    # Service layer (update_reservation_details) handles not found and business logic exceptions
    updated_reservation = services.reservation_service.update_reservation_details(
        db=db, reservation_id=reservation_id, reservation_in=reservation_in
    )
    if not updated_reservation: # Service returns None if not found, API layer raises 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found for update")
    return updated_reservation

@router.patch("/{reservation_id}/status", response_model=schemas.Reservation)
def update_reservation_status_api(
    *,
    db: Session = Depends(db_session.get_db),
    reservation_id: int,
    new_status: ReservationStatus = Query(..., description="The new status for the reservation"),
) -> Any:
    '''
    Update the status of a specific reservation.
    (e.g., PENDING -> CONFIRMED, CONFIRMED -> CHECKED_IN)
    '''
    updated_reservation = services.reservation_service.update_reservation_status(
        db=db, reservation_id=reservation_id, new_status=new_status
    )
    if not updated_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found for status update")
    return updated_reservation

@router.post("/{reservation_id}/cancel", response_model=schemas.Reservation) # Using POST for cancellation as it's a significant state change
def cancel_existing_reservation_api( # Renamed
    *,
    db: Session = Depends(db_session.get_db),
    reservation_id: int,
) -> Any:
    '''
    Cancel a reservation. Sets status to CANCELLED.
    '''
    cancelled_reservation = services.reservation_service.cancel_reservation(db=db, reservation_id=reservation_id)
    if not cancelled_reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found for cancellation")
    return cancelled_reservation

# No DELETE endpoint for reservations for now, as they are usually kept for records (status: CANCELLED).
# If hard delete is needed, a separate endpoint with specific permissions could be added.
