from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any # Updated Any to Dict for data_to_encode
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.token import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
# Access Token
JWT_SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
# Refresh Token
JWT_REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data_to_encode: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    '''
    Creates a new access token.
    'data_to_encode' should be a dictionary containing claims like 'user_id' and 'role'.
    The 'sub' claim will be set to the value of 'user_id' from data_to_encode.
    '''
    to_encode = data_to_encode.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    # Ensure 'sub' is set, typically to user_id.
    if "user_id" in to_encode and "sub" not in to_encode: # Set sub if not already present
        to_encode["sub"] = str(to_encode["user_id"])

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data_to_encode: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    '''
    Creates a new refresh token.
    'data_to_encode' should contain 'user_id'.
    The 'sub' claim will be set to 'user_id'.
    '''
    to_encode = data_to_encode.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    if "user_id" in to_encode and "sub" not in to_encode: # Set sub if not already present
        to_encode["sub"] = str(to_encode["user_id"])

    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str, secret_key: str) -> Optional[TokenPayload]:
    '''
    Decodes a JWT token and validates its payload against TokenPayload schema.
    Returns TokenPayload if valid, None otherwise.
    '''
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

        # Prepare data for TokenPayload validation.
        # TokenPayload expects 'user_id'. If 'sub' exists and 'user_id' does not, map 'sub' to 'user_id'.
        # However, our create functions now ensure 'user_id' is in the claims directly.
        # 'sub' is also set from 'user_id'.
        # TokenPayload also has 'sub' and 'exp' as optional fields.

        token_data = TokenPayload(**payload) # Pydantic will validate against its defined fields
        return token_data
    except JWTError:
        # This can catch expired tokens, invalid signatures, etc.
        return None
    except ValidationError:
        # This catches if the payload doesn't match TokenPayload schema
        return None
