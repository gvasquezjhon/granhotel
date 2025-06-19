from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
import uuid

from app import schemas, models, services
from app.api import deps # Import dependencies
from app.db import session as db_session # For get_db, though deps handle it
from app.models.user import UserRole # For Query parameter type hint

router = APIRouter()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_new_user_api(
    *,
    db: Session = Depends(db_session.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.require_admin_user) # Only admins can create users
) -> Any:
    '''
    Create new user. (Admin Only)
    '''
    # The service layer (create_user) handles HTTPException for duplicate email
    user = services.user_service.create_user(db=db, user_in=user_in)
    return user

@router.get("/me", response_model=schemas.User)
def read_current_user_me_api(
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Get current logged-in user.
    '''
    return current_user

@router.get("/", response_model=List[schemas.User]) # Moved before /me and /{user_id} to avoid path conflicts if path parameters were less specific
def list_all_users_api(
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="Filter by active status"), # Added Optional
    role: Optional[UserRole] = Query(None, description="Filter by user role"), # Added Optional
    current_admin: models.User = Depends(deps.require_admin_user)
):
    '''List all users. (Admin access) With optional filters for active status and role.'''
    users = services.user_service.get_users(db, skip=skip, limit=limit, is_active=is_active, role=role)
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id_api(
    *,
    user_id: uuid.UUID,
    db: Session = Depends(db_session.get_db),
    current_user: models.User = Depends(deps.require_manager_or_admin_user) # Manager or Admin
) -> Any:
    '''
    Get a specific user by ID. (Manager or Admin access)
    '''
    user = services.user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # If not admin, manager can only see non-admin users (optional additional check)
    # if current_user.role == models.user.UserRole.MANAGER and user.role == models.user.UserRole.ADMIN:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager cannot view Admin details")
    return user

@router.put("/me", response_model=schemas.User)
def update_current_user_me_api(
    *,
    db: Session = Depends(db_session.get_db),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Update current logged-in user's information.
    '''
    # The service layer (update_user) handles HTTPException for duplicate email
    updated_user = services.user_service.update_user(db=db, user_db_obj=current_user, user_in=user_in)
    return updated_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user_by_id_api(
    *,
    db: Session = Depends(db_session.get_db),
    user_id: uuid.UUID,
    user_in: schemas.UserUpdate,
    current_admin: models.User = Depends(deps.require_admin_user)
):
    '''
    Update a user by ID. (Admin access)
    '''
    user_to_update = services.user_service.get_user(db, user_id=user_id)
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for update")

    # Prevent deactivating the last admin or changing their role if they are the only one (example advanced check)
    # For now, simple update
    updated_user = services.user_service.update_user(db=db, user_db_obj=user_to_update, user_in=user_in)
    return updated_user

@router.patch("/{user_id}/activate", response_model=schemas.User)
def activate_user_api(
    *,
    db: Session = Depends(db_session.get_db),
    user_id: uuid.UUID,
    current_admin: models.User = Depends(deps.require_admin_user)
):
    '''Activate a user by ID. (Admin access)'''
    user = services.user_service.activate_user(db, user_id)
    if not user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.patch("/{user_id}/deactivate", response_model=schemas.User)
def deactivate_user_api(
    *,
    db: Session = Depends(db_session.get_db),
    user_id: uuid.UUID,
    current_admin: models.User = Depends(deps.require_admin_user)
):
    '''Deactivate a user by ID. (Admin access)'''
    # Add check: cannot deactivate self if admin (or last admin)
    if current_admin.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin user cannot deactivate self.")
    user = services.user_service.deactivate_user(db, user_id)
    if not user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.patch("/{user_id}/role", response_model=schemas.User)
def update_user_role_api(
    *,
    db: Session = Depends(db_session.get_db),
    user_id: uuid.UUID,
    new_role: UserRole = Query(..., description="New role for the user"), # Using UserRole from app.models.user
    current_admin: models.User = Depends(deps.require_admin_user)
):
    '''Update a user's role by ID. (Admin access)'''
    # Add check: cannot change own role if admin (or last admin needs specific handling)
    if current_admin.id == user_id and new_role != UserRole.ADMIN:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin user cannot change own role from Admin.")
    user = services.user_service.update_user_role(db, user_id, new_role)
    if not user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
