from fastapi import APIRouter
from app.api.v1.endpoints import rooms, guests, reservations, auth # Add auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"]) # Add auth router
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(guests.router, prefix="/guests", tags=["Guests"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
# User management endpoints will be added separately
