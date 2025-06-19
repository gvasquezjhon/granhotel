from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
from datetime import date, datetime, timezone # Ensure all are imported
import uuid

from app import models
from app import schemas
from app.models.housekeeping import HousekeepingLog, HousekeepingStatus, HousekeepingTaskType
from app.models.user import User, UserRole # For role checks and fetching user details
from app.models.room import Room # For room validation
from fastapi import HTTPException, status

def create_housekeeping_log(
    db: Session, log_in: schemas.housekeeping.HousekeepingLogCreate, creator_user_id: uuid.UUID
) -> models.housekeeping.HousekeepingLog:
    '''Create a new housekeeping log/task.'''
    room = db.query(models.room.Room).filter(models.room.Room.id == log_in.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with ID {log_in.room_id} not found.")

    assigned_to_user = None
    if log_in.assigned_to_user_id:
        assigned_to_user = db.query(models.user.User).filter(models.user.User.id == log_in.assigned_to_user_id).first()
        if not assigned_to_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assigned user with ID {log_in.assigned_to_user_id} not found.")
        # Ensure assigned user is a housekeeper or admin/manager who might self-assign for oversight
        if assigned_to_user.role not in [UserRole.HOUSEKEEPER, UserRole.MANAGER, UserRole.ADMIN]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {log_in.assigned_to_user_id} does not have an appropriate role for housekeeping tasks.")

    db_log_data = log_in.model_dump()
    db_log_data["created_by_user_id"] = creator_user_id
    db_log_data["updated_by_user_id"] = creator_user_id

    db_log = models.housekeeping.HousekeepingLog(**db_log_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    # Eager load for a consistent response object matching get_housekeeping_log
    # This ensures that related objects are available on the returned instance.
    refreshed_log = db.query(models.housekeeping.HousekeepingLog).options(
        joinedload(models.housekeeping.HousekeepingLog.room),
        joinedload(models.housekeeping.HousekeepingLog.assigned_to),
        joinedload(models.housekeeping.HousekeepingLog.creator),
        joinedload(models.housekeeping.HousekeepingLog.updater)
    ).filter(models.housekeeping.HousekeepingLog.id == db_log.id).first()
    return refreshed_log if refreshed_log else db_log # Fallback to db_log if somehow not found (should not happen)


def get_housekeeping_log(db: Session, log_id: int) -> Optional[models.housekeeping.HousekeepingLog]:
    '''Retrieve a housekeeping log by ID, including room and assigned staff details.'''
    return db.query(models.housekeeping.HousekeepingLog).options(
        joinedload(models.housekeeping.HousekeepingLog.room),
        joinedload(models.housekeeping.HousekeepingLog.assigned_to),
        joinedload(models.housekeeping.HousekeepingLog.creator),
        joinedload(models.housekeeping.HousekeepingLog.updater)
    ).filter(models.housekeeping.HousekeepingLog.id == log_id).first()

def get_housekeeping_logs(
    db: Session, skip: int = 0, limit: int = 100,
    room_id: Optional[int] = None,
    assigned_to_user_id: Optional[uuid.UUID] = None,
    status: Optional[HousekeepingStatus] = None,
    task_type: Optional[HousekeepingTaskType] = None,
    scheduled_date_from: Optional[date] = None,
    scheduled_date_to: Optional[date] = None
) -> List[models.housekeeping.HousekeepingLog]:
    '''Retrieve housekeeping logs with various filters and pagination.'''
    query = db.query(models.housekeeping.HousekeepingLog).options(
        joinedload(models.housekeeping.HousekeepingLog.room),
        joinedload(models.housekeeping.HousekeepingLog.assigned_to)
    )
    if room_id is not None:
        query = query.filter(models.housekeeping.HousekeepingLog.room_id == room_id)
    if assigned_to_user_id:
        query = query.filter(models.housekeeping.HousekeepingLog.assigned_to_user_id == assigned_to_user_id)
    if status:
        query = query.filter(models.housekeeping.HousekeepingLog.status == status)
    if task_type:
        query = query.filter(models.housekeeping.HousekeepingLog.task_type == task_type)
    if scheduled_date_from:
        query = query.filter(models.housekeeping.HousekeepingLog.scheduled_date >= scheduled_date_from)
    if scheduled_date_to:
        query = query.filter(models.housekeeping.HousekeepingLog.scheduled_date <= scheduled_date_to)

    return query.order_by(
        models.housekeeping.HousekeepingLog.scheduled_date.desc(),
        models.housekeeping.HousekeepingLog.id.desc()
    ).offset(skip).limit(limit).all()


def update_housekeeping_log_status(
    db: Session, log_id: int, new_status: HousekeepingStatus, updater_user_id: uuid.UUID, notes_issues: Optional[str] = None
) -> Optional[models.housekeeping.HousekeepingLog]:
    '''Update the status of a housekeeping log. Also updates notes if provided.'''
    # Fetch with related objects to ensure they are available if needed for subsequent logic or response
    db_log = get_housekeeping_log(db, log_id)
    if not db_log:
        return None

    # Example business rule: Prevent staff from reverting a completed task unless they are admin/manager
    is_assigned_staff = db_log.assigned_to_user_id == updater_user_id
    updater_user = db.query(User).filter(User.id == updater_user_id).first()
    is_privileged_user = updater_user and updater_user.role in [UserRole.ADMIN, UserRole.MANAGER]

    if db_log.status == HousekeepingStatus.COMPLETED and new_status != HousekeepingStatus.COMPLETED:
        if is_assigned_staff and not is_privileged_user: # Staff cannot revert completed task
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task is already completed and cannot be changed by assigned staff without manager/admin rights.")

    db_log.status = new_status
    db_log.updated_by_user_id = updater_user_id

    current_time_utc = datetime.now(timezone.utc)
    if new_status == HousekeepingStatus.IN_PROGRESS and not db_log.started_at:
        db_log.started_at = current_time_utc
    elif new_status in [HousekeepingStatus.COMPLETED, HousekeepingStatus.NEEDS_INSPECTION] and not db_log.completed_at:
        db_log.completed_at = current_time_utc
        if not db_log.started_at : # If task moved directly to completed (e.g. by admin)
            db_log.started_at = current_time_utc # Set started_at to completed_at time

    if notes_issues is not None: # Allow updating notes regardless of status change
        db_log.notes_issues_reported = notes_issues if notes_issues.strip() else db_log.notes_issues_reported

    db.commit()
    db.refresh(db_log)
    # Re-fetch with all joins for consistent response
    return get_housekeeping_log(db, log_id)


def assign_housekeeping_task(
    db: Session, log_id: int, assigned_to_user_id: Optional[uuid.UUID], updater_user_id: uuid.UUID # Allow None to unassign
) -> Optional[models.housekeeping.HousekeepingLog]:
    '''Assign or reassign a housekeeping task to a staff member, or unassign.'''
    db_log = get_housekeeping_log(db, log_id)
    if not db_log:
        return None

    if assigned_to_user_id is not None:
        new_assigned_user = db.query(models.user.User).filter(models.user.User.id == assigned_to_user_id).first()
        if not new_assigned_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User to assign (ID: {assigned_to_user_id}) not found.")
        if new_assigned_user.role not in [UserRole.HOUSEKEEPER, UserRole.MANAGER, UserRole.ADMIN]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {assigned_to_user_id} does not have an appropriate role for housekeeping tasks.")
        db_log.assigned_to_user_id = assigned_to_user_id
    else: # Unassigning
        db_log.assigned_to_user_id = None

    db_log.updated_by_user_id = updater_user_id

    db.commit()
    db.refresh(db_log)
    return get_housekeeping_log(db, log_id) # Re-fetch for consistent response

def update_housekeeping_log_details(
    db: Session, log_id: int, log_in: schemas.housekeeping.HousekeepingLogUpdate, updater_user_id: uuid.UUID
) -> Optional[models.housekeeping.HousekeepingLog]:
    '''Update general details of a housekeeping log (e.g., room, task type, schedule, notes).'''
    db_log = get_housekeeping_log(db, log_id)
    if not db_log:
        return None

    update_data = log_in.model_dump(exclude_unset=True)

    if "room_id" in update_data and update_data["room_id"] != db_log.room_id:
        room = db.query(models.room.Room).filter(models.room.Room.id == update_data["room_id"]).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with ID {update_data['room_id']} not found.")

    if "assigned_to_user_id" in update_data and update_data["assigned_to_user_id"] != db_log.assigned_to_user_id:
        if update_data["assigned_to_user_id"] is not None:
            assigned_to_user = db.query(models.user.User).filter(models.user.User.id == update_data["assigned_to_user_id"]).first()
            if not assigned_to_user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assigned user with ID {update_data['assigned_to_user_id']} not found.")
            if assigned_to_user.role not in [UserRole.HOUSEKEEPER, UserRole.MANAGER, UserRole.ADMIN]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {update_data['assigned_to_user_id']} does not have an appropriate role.")

    for field, value in update_data.items():
        setattr(db_log, field, value)

    db_log.updated_by_user_id = updater_user_id
    db.commit()
    db.refresh(db_log)
    return get_housekeeping_log(db, log_id) # Re-fetch for consistent response with all joins
