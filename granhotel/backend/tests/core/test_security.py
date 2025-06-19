from datetime import timedelta, timezone # Added timezone for datetime.now(timezone.utc)
from jose import jwt as jose_jwt, JWTError # To check for JWTError, changed from just jwt
import pytest # For raises
import uuid # For generating UUIDs

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.schemas.token import TokenPayload

def test_password_hashing():
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_and_decode_access_token():
    user_id_val = str(uuid.uuid4())
    role_val = "ADMIN"
    # Data to encode now includes user_id which will be used for 'sub'
    token_data_to_encode = {"user_id": user_id_val, "role": role_val}

    token = create_access_token(data_to_encode=token_data_to_encode)
    assert token is not None

    decoded_payload = decode_token(token, settings.SECRET_KEY)
    assert decoded_payload is not None
    assert decoded_payload.user_id == user_id_val
    assert decoded_payload.role == role_val
    assert decoded_payload.sub == user_id_val # Check sub is set to user_id

def test_create_and_decode_refresh_token():
    user_id_val = str(uuid.uuid4())
    token_data_to_encode = {"user_id": user_id_val} # Refresh token might have less data

    token = create_refresh_token(data_to_encode=token_data_to_encode)
    assert token is not None

    decoded_payload = decode_token(token, settings.REFRESH_SECRET_KEY)
    assert decoded_payload is not None
    assert decoded_payload.user_id == user_id_val
    assert decoded_payload.sub == user_id_val

def test_decode_invalid_token():
    invalid_token = "this.is.not.a.valid.token"
    assert decode_token(invalid_token, settings.SECRET_KEY) is None

    # Test with a token signed with a different key
    user_id_val = str(uuid.uuid4())
    # The 'data_to_encode' for create_access_token expects 'user_id' for 'sub'
    token_payload_dict = {"user_id": user_id_val, "role": "USER", "sub": user_id_val, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    token_signed_wrong_key = jose_jwt.encode(token_payload_dict, "WRONG_KEY", algorithm=settings.ALGORITHM)
    assert decode_token(token_signed_wrong_key, settings.SECRET_KEY) is None

def test_token_expiry():
    user_id_val = str(uuid.uuid4())
    # Create token that expires immediately
    # data_to_encode for create_access_token expects 'user_id'
    expired_token = create_access_token(data_to_encode={"user_id": user_id_val}, expires_delta=timedelta(seconds=-1))

    # Wait a moment to ensure expiry, though negative delta should guarantee it
    # import time; time.sleep(0.1) # Usually not needed for negative delta

    with pytest.raises(JWTError): # jose.jwt.decode raises JWTError for expired tokens directly
         jose_jwt.decode(expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # Our decode_token catches JWTError and returns None
    assert decode_token(expired_token, settings.SECRET_KEY) is None
