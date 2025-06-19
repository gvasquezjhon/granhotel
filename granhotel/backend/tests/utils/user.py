from sqlalchemy.orm import Session
from typing import Optional
import uuid
import random # Ensure random is imported
import string # Ensure string is imported

from app import models, schemas, services
from app.models.user import UserRole
from app.core.security import hash_password # To help create users with known passwords for testing auth

def random_lower_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"

def create_user_in_db(
    db: Session,
    email: Optional[str] = None,
    password: Optional[str] = "testpassword", # Known password for login tests
    first_name: str = "Test",
    last_name: str = "User",
    role: UserRole = UserRole.RECEPTIONIST,
    is_active: bool = True,
    suffix_for_email: str = "" # Added suffix parameter
) -> models.User:
    if suffix_for_email and not email: # If suffix is provided and email is not, construct email with suffix
        email = f"testuser_{suffix_for_email}_{random_lower_string(3)}@example.com"
    elif not email: # Default random email if no suffix and no email provided
        email = random_email()

    user_in_create = schemas.UserCreate(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=is_active
    )

    # Check if user already exists to prevent test errors if email is not perfectly unique
    # This can happen if random_email() by chance generates an existing one or if suffix logic isn't enough
    existing_user = services.user_service.get_user_by_email(db, email=user_in_create.email)
    if existing_user:
        # If user exists, just return it, assuming it was created by a previous step in the test setup
        # Or, modify email slightly to ensure uniqueness for this specific test call
        user_in_create.email = f"retry_{random_lower_string(2)}_{user_in_create.email}"[:100] # Ensure email length is valid
        # print(f"Warning: User with email {email} already existed. Retrying with {user_in_create.email}")

    user = services.user_service.create_user(db=db, user_in=user_in_create)

    # If is_active was not part of UserCreate (it is in our current schema) or if service default overrides,
    # and we need a specific state for is_active not matching the created one:
    if user.is_active != is_active:
       user.is_active = is_active
       db.add(user) # Add to session before commit
       db.commit()
       db.refresh(user)
    return user
