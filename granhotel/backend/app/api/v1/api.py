from fastapi import APIRouter
from app.api.v1.endpoints import rooms, guests, reservations, auth, users # Add users

api_router = APIRouter()
# Auth and Users usually come first or are grouped
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(guests.router, prefix="/guests", tags=["Guests"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
