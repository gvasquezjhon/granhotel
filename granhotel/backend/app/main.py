from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any # Added for type hint

from app.core.config import settings
from app.api.v1.api import api_router
# from app.db.session import engine # Not needed here if using Alembic
# from app.db.base_class import Base # Not needed here

# Base.metadata.create_all(bind=engine) # IMPORTANT: This should be handled by Alembic, not run on app startup in prod

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="API for Gran Hotel Management System - Perú Edition (Lite)" # Added description
)

# CORS Middleware
# In production, restrict origins to your frontend domain for security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') and settings.CORS_ORIGINS else ["*"], # Allow specific origins or all
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"]) # Added tag for root endpoint
async def root() -> Any: # Added type hint
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Visit /docs for API documentation."}
