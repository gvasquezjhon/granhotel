from sqlalchemy.orm import Session
from typing import List, Optional, Any
from fastapi import HTTPException, status # For potential errors
import uuid

from app import models
from app import schemas
from app.core.security import hash_password, verify_password # For password operations
from app.models.user import User, UserRole # Explicit imports for clarity

def get_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    '''
    Retrieve a user by their ID.
    '''
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    '''
    Retrieve a user by their email address.
    '''
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(
    db: Session, skip: int = 0, limit: int = 100,
    is_active: Optional[bool] = None,
    role: Optional[UserRole] = None
) -> List[models.User]:
    '''
    Retrieve a list of users with optional filtering.
    '''
    query = db.query(models.User)
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if role:
        query = query.filter(models.User.role == role)
    return query.order_by(models.User.email).offset(skip).limit(limit).all()

def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    '''
    Create a new user.
    - Hashes the password before storing.
    - Checks for uniqueness of email.
    '''
    existing_user = get_user_by_email(db, email=user_in.email)
    if existing_user:
        # Raising HTTPException here makes the service less reusable if different error handling
        # is needed by different callers. Often, returning a specific value or custom exception
        # is preferred, and the API layer translates that to an HTTPException.
        # However, for this project, we'll follow the pattern of raising it here.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    hashed_pass = hash_password(user_in.password)

    user_data = user_in.model_dump(exclude={"password"}) # Pydantic v2 uses model_dump
    user_data["hashed_password"] = hashed_pass

    db_user = models.User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_db_obj: models.User, user_in: schemas.UserUpdate) -> models.User:
    '''
    Update an existing user.
    - If password is provided, it's hashed.
    - Checks for email uniqueness if email is being changed.
    '''
    update_data = user_in.model_dump(exclude_unset=True) # Pydantic v2 uses model_dump

    if "email" in update_data and update_data["email"] != user_db_obj.email:
        existing_user_email = get_user_by_email(db, email=update_data["email"])
        if existing_user_email and existing_user_email.id != user_db_obj.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another user with this email already exists."
            )

    if "password" in update_data and update_data["password"]:
        hashed_pass = hash_password(update_data["password"])
        update_data["hashed_password"] = hashed_pass
        del update_data["password"]
    elif "password" in update_data:
        del update_data["password"]


    for field, value in update_data.items():
        if hasattr(user_db_obj, field): # Ensure field exists in the model
            setattr(user_db_obj, field, value)

    db.add(user_db_obj)
    db.commit()
    db.refresh(user_db_obj)
    return user_db_obj


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    '''
    Authenticate a user.
    - Retrieves user by email.
    - Verifies password.
    - Returns user object if authentication is successful, None otherwise.
    '''
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def activate_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    '''Activates a user.'''
    user = get_user(db, user_id)
    if user and not user.is_active:
        user.is_active = True
        db.commit()
        db.refresh(user)
    return user

def deactivate_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    '''Deactivates a user.'''
    user = get_user(db, user_id)
    if user and user.is_active:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user

def update_user_role(db: Session, user_id: uuid.UUID, new_role: UserRole) -> Optional[models.User]:
    '''Updates a user's role.'''
    user = get_user(db, user_id)
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
    return user
