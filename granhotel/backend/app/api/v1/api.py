from fastapi import APIRouter
from app.api.v1.endpoints import rooms # Corrected import

api_router = APIRouter()
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
