from pydantic import BaseModel, Field
from typing import Optional
import uuid

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    user_id: str  # Primary identifier we'll use internally from the token. Can be str(UUID).
    role: Optional[str] = None # Role of the user.
    exp: Optional[int] = None # Standard 'exp' claim (expiration time). Automatically handled by jose.jwt.
    sub: Optional[str] = None # Standard 'sub' claim (subject). Will be set to user_id.
    # Add any other custom claims you intend to include.

class RefreshTokenRequest(BaseModel): # New schema
    refresh_token: str
