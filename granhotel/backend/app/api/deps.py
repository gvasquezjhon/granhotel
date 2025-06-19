from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid # For converting user_id string from token to UUID

from app.core.security import decode_token # Use access token secret
from app.core.config import settings # For JWT_SECRET_KEY and API_V1_STR
from app.schemas.token import TokenPayload
from app import models # For User model
from app.services import user_service # To get user from DB
from app.db.session import get_db # Session dependency

# OAuth2PasswordBearer points to the tokenUrl, which is the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    '''
    Dependency to get current user from JWT token.
    Validates token, decodes it, retrieves user from DB.
    '''
    token_payload = decode_token(token=token, secret_key=settings.SECRET_KEY) # Use access token secret
    if not token_payload or not token_payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials - Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(token_payload.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials - Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_service.get_user(db, user_id=user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Changed from 404 for consistency: token valid, user gone
            detail="User not found for token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user_from_token)
) -> models.User:
    '''
    Dependency to get current active user.
    Builds on get_current_user_from_token and checks is_active.
    '''
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# Role-based dependencies (examples)
def require_admin_user(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    if current_user.role != models.user.UserRole.ADMIN: # Corrected access to UserRole
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Admin required)"
        )
    return current_user

def require_manager_or_admin_user(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    if current_user.role not in [models.user.UserRole.ADMIN, models.user.UserRole.MANAGER]: # Corrected access to UserRole
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Manager or Admin required)"
        )
    return current_user
