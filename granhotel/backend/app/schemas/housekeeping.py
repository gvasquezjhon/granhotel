from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
import uuid # For UUID type hint

from app.models.housekeeping import HousekeepingTaskType, HousekeepingStatus
from .user import User as UserSchema # For assigned_to details in response
from .room import Room as RoomSchema # For room details in response

# HousekeepingLog Schemas
class HousekeepingLogBase(BaseModel):
    room_id: int
    assigned_to_user_id: Optional[uuid.UUID] = None
    task_type: HousekeepingTaskType
    status: HousekeepingStatus = HousekeepingStatus.PENDING
    scheduled_date: date
    notes_instructions: Optional[str] = None

    # notes_issues_reported is usually set during status updates, not base creation
    # started_at and completed_at are usually set by the system/service logic

class HousekeepingLogCreate(HousekeepingLogBase):
    # created_by_user_id will be set from current_user in service/API
    pass

class HousekeepingLogUpdate(BaseModel): # For general updates by manager/admin
    room_id: Optional[int] = None
    assigned_to_user_id: Optional[uuid.UUID] = None # Allow unassigning by setting to None
    task_type: Optional[HousekeepingTaskType] = None
    status: Optional[HousekeepingStatus] = None
    scheduled_date: Optional[date] = None
    notes_instructions: Optional[str] = None
    notes_issues_reported: Optional[str] = None # Manager can also update this
    # updated_by_user_id will be set from current_user

class HousekeepingLogStatusUpdate(BaseModel): # For staff updating their task status
    status: HousekeepingStatus
    notes_issues_reported: Optional[str] = None # Staff can add notes when updating status

class HousekeepingLogAssignmentUpdate(BaseModel): # For re-assigning tasks
    assigned_to_user_id: Optional[uuid.UUID] = None # Allow unassigning by setting to None


class HousekeepingLogInDBBase(HousekeepingLogBase):
    id: int
    notes_issues_reported: Optional[str] = None # Ensure this is part of DB base if in model
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: Optional[uuid.UUID] = None
    updated_by_user_id: Optional[uuid.UUID] = None

    # Nested details for responses
    room: Optional[RoomSchema] = None
    assigned_to: Optional[UserSchema] = None
    creator: Optional[UserSchema] = None # For richer response if needed
    updater: Optional[UserSchema] = None # For richer response if needed

    class Config:
        from_attributes = True

class HousekeepingLog(HousekeepingLogInDBBase):
    pass # Main response schema
