from fastapi import APIRouter
from app.api.v1.endpoints import rooms, guests # Add guests

api_router = APIRouter()
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(guests.router, prefix="/guests", tags=["Guests"]) # Add guest router
