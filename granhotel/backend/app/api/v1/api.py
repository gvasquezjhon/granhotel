from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, rooms, guests, reservations,
    product_categories, products
)

api_router = APIRouter()

# Core services like auth and users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Hotel operational services
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(guests.router, prefix="/guests", tags=["Guests"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])

# Product/Sales services
api_router.include_router(product_categories.router, prefix="/product-categories", tags=["Product Categories"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
