from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date
import uuid

from app import schemas, models, services
from app.api import deps
from app.db import session as db_session
from app.models.housekeeping import HousekeepingStatus, HousekeepingTaskType
from app.models.user import UserRole

router = APIRouter()

@router.post("/logs/", response_model=schemas.housekeeping.HousekeepingLog, status_code=status.HTTP_201_CREATED)
def create_new_housekeeping_log_api(
    *,
    db: Session = Depends(db_session.get_db),
    log_in: schemas.housekeeping.HousekeepingLogCreate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Create a new housekeeping log/task.
    Requires Manager or Admin role.
    '''
    new_log = services.housekeeping_service.create_housekeeping_log(
        db=db, log_in=log_in, creator_user_id=current_user.id
    )
    return new_log

@router.get("/logs/", response_model=List[schemas.housekeeping.HousekeepingLog])
def read_all_housekeeping_logs_api(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    room_id: Optional[int] = Query(None, description="Filter by Room ID"),
    assigned_to_user_id: Optional[uuid.UUID] = Query(None, description="Filter by assigned staff User ID"),
    status: Optional[HousekeepingStatus] = Query(None, description="Filter by task status"),
    task_type: Optional[HousekeepingTaskType] = Query(None, description="Filter by task type"),
    scheduled_date_from: Optional[date] = Query(None, description="Filter by scheduled date (from)"),
    scheduled_date_to: Optional[date] = Query(None, description="Filter by scheduled date (to)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''
    Retrieve all housekeeping logs with optional filters.
    Requires Manager or Admin role.
    '''
    logs = services.housekeeping_service.get_housekeeping_logs(
        db, skip=skip, limit=limit, room_id=room_id, assigned_to_user_id=assigned_to_user_id,
        status=status, task_type=task_type, scheduled_date_from=scheduled_date_from, scheduled_date_to=scheduled_date_to
    )
    return logs

@router.get("/logs/staff/me", response_model=List[schemas.housekeeping.HousekeepingLog])
def read_my_assigned_housekeeping_logs_api(
    *,
    db: Session = Depends(db_session.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[HousekeepingStatus] = Query(None, description="Filter by task status"),
    scheduled_date_from: Optional[date] = Query(None, description="Filter by scheduled date (from)"),
    scheduled_date_to: Optional[date] = Query(None, description="Filter by scheduled date (to)"),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Retrieve housekeeping logs assigned to the currently authenticated user.
    '''
    if current_user.role not in [UserRole.HOUSEKEEPER, UserRole.MANAGER, UserRole.ADMIN]:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have a role with housekeeping task access.")

    logs = services.housekeeping_service.get_housekeeping_logs(
        db, skip=skip, limit=limit, assigned_to_user_id=current_user.id,
        status=status, task_type=None,
        scheduled_date_from=scheduled_date_from, scheduled_date_to=scheduled_date_to
    )
    return logs

@router.get("/logs/room/{room_id}", response_model=List[schemas.housekeeping.HousekeepingLog])
def read_room_housekeeping_logs_api(
    *,
    db: Session = Depends(db_session.get_db),
    room_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[HousekeepingStatus] = Query(None, description="Filter by task status"),
    task_type: Optional[HousekeepingTaskType] = Query(None, description="Filter by task type"),
    scheduled_date_from: Optional[date] = Query(None, description="Filter by scheduled date (from)"),
    scheduled_date_to: Optional[date] = Query(None, description="Filter by scheduled date (to)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Retrieve housekeeping logs for a specific room. Requires Manager or Admin.'''
    logs = services.housekeeping_service.get_housekeeping_logs(
        db, skip=skip, limit=limit, room_id=room_id,
        status=status, task_type=task_type,
        scheduled_date_from=scheduled_date_from, scheduled_date_to=scheduled_date_to
    )
    return logs


@router.get("/logs/{log_id}", response_model=schemas.housekeeping.HousekeepingLog)
def read_single_housekeeping_log_api(
    *,
    db: Session = Depends(db_session.get_db),
    log_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''Retrieve a specific housekeeping log by ID.'''
    log = services.housekeeping_service.get_housekeeping_log(db, log_id=log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping log not found")

    if current_user.role == UserRole.HOUSEKEEPER and log.assigned_to_user_id != current_user.id:
        # Also ensure manager/admin can see any log
        if not (current_user.role in [UserRole.MANAGER, UserRole.ADMIN]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this housekeeping log")
    return log

@router.patch("/logs/{log_id}/status", response_model=schemas.housekeeping.HousekeepingLog)
def update_log_status_api(
    *,
    db: Session = Depends(db_session.get_db),
    log_id: int,
    status_update_in: schemas.housekeeping.HousekeepingLogStatusUpdate,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    '''
    Update the status of a housekeeping log.
    Housekeepers can update their own tasks. Managers/Admins can update any.
    '''
    log_to_update = services.housekeeping_service.get_housekeeping_log(db, log_id)
    if not log_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping log not found")

    is_manager_or_admin = current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    is_assigned_housekeeper = current_user.role == UserRole.HOUSEKEEPER and \
                              log_to_update.assigned_to_user_id == current_user.id

    if not (is_manager_or_admin or is_assigned_housekeeper):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update status of this log")

    # Housekeepers have limited status transitions they can make
    if is_assigned_housekeeper and not is_manager_or_admin:
        allowed_statuses_for_hk = [
            HousekeepingStatus.IN_PROGRESS, HousekeepingStatus.COMPLETED,
            HousekeepingStatus.NEEDS_INSPECTION, HousekeepingStatus.ISSUE_REPORTED
        ]
        # Also allow moving from IN_PROGRESS to PENDING (e.g. interrupted) or ISSUE_REPORTED to IN_PROGRESS
        if log_to_update.status == HousekeepingStatus.IN_PROGRESS and status_update_in.status == HousekeepingStatus.PENDING:
            pass # Allow this transition
        elif status_update_in.status not in allowed_statuses_for_hk:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Housekeeper cannot set status to {status_update_in.status.value}")

    updated_log = services.housekeeping_service.update_housekeeping_log_status(
        db, log_id=log_id, new_status=status_update_in.status,
        updater_user_id=current_user.id, notes_issues=status_update_in.notes_issues_reported
    )
    return updated_log


@router.patch("/logs/{log_id}/assign", response_model=schemas.housekeeping.HousekeepingLog)
def assign_log_task_api(
    *,
    db: Session = Depends(db_session.get_db),
    log_id: int,
    assignment_in: schemas.housekeeping.HousekeepingLogAssignmentUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Assign or reassign a housekeeping task. Requires Manager or Admin role.'''
    updated_log = services.housekeeping_service.assign_housekeeping_task(
        db, log_id=log_id, assigned_to_user_id=assignment_in.assigned_to_user_id, updater_user_id=current_user.id
    )
    if not updated_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping log not found for assignment")
    return updated_log

@router.put("/logs/{log_id}", response_model=schemas.housekeeping.HousekeepingLog)
def update_log_details_api(
    *,
    db: Session = Depends(db_session.get_db),
    log_id: int,
    log_update_in: schemas.housekeeping.HousekeepingLogUpdate,
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Update general details of a housekeeping log. Requires Manager or Admin role.'''
    updated_log = services.housekeeping_service.update_housekeeping_log_details(
        db, log_id=log_id, log_in=log_update_in, updater_user_id=current_user.id
    )
    if not updated_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping log not found for update")
    return updated_log
