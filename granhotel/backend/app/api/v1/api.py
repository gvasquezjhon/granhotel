from fastapi import APIRouter
from app.api.v1.endpoints import rooms, guests, reservations # Add reservations

api_router = APIRouter()
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(guests.router, prefix="/guests", tags=["Guests"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"]) # Add reservations router
