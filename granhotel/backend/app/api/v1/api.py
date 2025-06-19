from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, rooms, guests, reservations,
    product_categories, products,
    suppliers, inventory_stock, purchase_orders,
    housekeeping,
    pos # Add pos
)

api_router = APIRouter()

# Core services like auth and users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# Hotel operational services
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(guests.router, prefix="/guests", tags=["Guests"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(housekeeping.router, prefix="/housekeeping", tags=["Housekeeping"])

# Product/Sales and Inventory services
api_router.include_router(product_categories.router, prefix="/product-categories", tags=["Product Categories"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
api_router.include_router(inventory_stock.router, prefix="/inventory-stock", tags=["Inventory Stock Management"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
api_router.include_router(pos.router, prefix="/pos", tags=["Point of Sale"])
