from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # For login form
from sqlalchemy.orm import Session
from typing import Any
import uuid # For converting str user_id from token back to UUID

from app import schemas, services, models # models for User type hint
from app.core.security import create_access_token, create_refresh_token, decode_token # decode_token for refresh
from app.core.config import settings # For refresh token secret
from app.db import session as db_session # For get_db dependency

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), # Use OAuth2 form for username/password
    db: Session = Depends(db_session.get_db)
) -> Any:
    '''
    OAuth2 compatible token login, get an access token for future requests.
    Username is the email.
    '''
    user = services.user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # is_active check is already in authenticate_user, but double check or rely on service
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 403 Forbidden
            detail="Inactive user",
        )

    token_data_payload = {
        "user_id": str(user.id), # Convert UUID to string for JWT
        "role": user.role.value if user.role else None # Enum value, handle if role can be None
    }
    access_token = create_access_token(data_to_encode=token_data_payload)

    # Refresh token might only need user_id or could also include a session identifier later
    refresh_token_payload = {"user_id": str(user.id)}
    refresh_token = create_refresh_token(data_to_encode=refresh_token_payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_access_token(
    token_request: schemas.RefreshTokenRequest, # Expects a JSON body with {"refresh_token": "..."}
    db: Session = Depends(db_session.get_db)
) -> Any:
    '''
    Refresh an access token using a valid refresh token.
    '''
    current_refresh_token_str = token_request.refresh_token
    token_payload = decode_token(token=current_refresh_token_str, secret_key=settings.REFRESH_SECRET_KEY)

    if not token_payload or not token_payload.user_id: # user_id is string here
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(token_payload.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Or 400 Bad Request
            detail="Invalid user identifier format in refresh token",
        )

    user = services.user_service.get_user(db, user_id=user_uuid)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for refresh token", # Could be user deleted after token issued
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user, cannot refresh token",
        )

    # Data for the new access token, including role for permission checks
    new_access_token_payload = {
        "user_id": str(user.id),
        "role": user.role.value if user.role else None
    }
    new_access_token = create_access_token(data_to_encode=new_access_token_payload)

    # Optionally, issue a new refresh token as well for refresh token rotation
    # For simplicity, this example re-uses the existing refresh token if it's still valid for its full lifetime
    # new_refresh_token_payload = {"user_id": str(user.id)}
    # new_refresh_token = create_refresh_token(data_to_encode=new_refresh_token_payload)

    return {
        "access_token": new_access_token,
        "refresh_token": current_refresh_token_str, # Or new_refresh_token if implementing rotation
        "token_type": "bearer",
    }
