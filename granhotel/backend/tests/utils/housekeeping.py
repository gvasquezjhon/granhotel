from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta, datetime
import random
import uuid

from app import models, schemas, services
from app.models.housekeeping import HousekeepingTaskType, HousekeepingStatus
from app.models.user import UserRole
from tests.utils.user import create_user_in_db # Assumes this utility exists and works
from tests.utils.room import create_random_room # Assumes this utility exists and works
from tests.utils.common import random_lower_string, random_email # Import random_email

def create_random_housekeeper(db: Session, suffix: str = "") -> models.User:
    '''Helper to create a user with the HOUSEKEEPER role.'''
    # Construct a more unique email for the housekeeper
    hk_email = random_email(prefix=f"hk_{suffix}{random_lower_string(4)}")

    # Check if this email already exists to prevent test failures
    # This is a simple check; more robust would be a loop with retries or ensuring create_user_in_db handles it
    existing_user = services.user_service.get_user_by_email(db, email=hk_email)
    if existing_user:
        # If email is taken, generate another variation.
        # This could happen in rapid test runs if random_email isn't perfectly unique or if db isn't fully clean.
        hk_email = random_email(prefix=f"hk_{suffix}{random_lower_string(5)}")


    return create_user_in_db( # create_user_in_db should handle actual user creation via service
        db,
        email=hk_email,
        role=UserRole.HOUSEKEEPER,
        first_name=f"HK_FN_{suffix}{random_lower_string(2)}",
        last_name=f"HK_LN_{suffix}{random_lower_string(2)}",
        is_active=True # Housekeepers should generally be active
    )

def create_random_housekeeping_log_data(
    db: Session,
    room_id: Optional[int] = None,
    assigned_to_user_id: Optional[uuid.UUID] = None, # Accepts UUID
    task_type: Optional[HousekeepingTaskType] = None,
    status: HousekeepingStatus = HousekeepingStatus.PENDING,
    days_from_today: int = 0
) -> schemas.housekeeping.HousekeepingLogCreate:

    if room_id is None:
        room_suffix = f"_hk_log_util_{random_lower_string(3)}"
        room = create_random_room(db, room_number_suffix=room_suffix) # from tests.utils.room
        room_id = room.id

    final_assigned_to_user_id = assigned_to_user_id
    # Optionally assign to a housekeeper if not specified
    if assigned_to_user_id is None and random.choice([True, False, False]): # Reduce frequency of auto-assign for more varied tests
        housekeeper_suffix = f"_hk_assign_{random_lower_string(3)}"
        housekeeper = create_random_housekeeper(db, suffix=housekeeper_suffix)
        final_assigned_to_user_id = housekeeper.id # housekeeper.id is UUID

    final_task_type = task_type or random.choice(list(HousekeepingTaskType))
    scheduled = date.today() + timedelta(days=days_from_today)

    return schemas.housekeeping.HousekeepingLogCreate(
        room_id=room_id,
        assigned_to_user_id=final_assigned_to_user_id, # This is UUID or None
        task_type=final_task_type,
        status=status,
        scheduled_date=scheduled,
        notes_instructions=f"Test instructions for {final_task_type.value} on {scheduled.isoformat()} {random_lower_string(4)}"
    )

def create_random_housekeeping_log(
    db: Session,
    creator_user_id: uuid.UUID, # creator_user_id must be UUID
    room_id: Optional[int] = None,
    assigned_to_user_id: Optional[uuid.UUID] = None, # assigned_to_user_id must be UUID
    task_type: Optional[HousekeepingTaskType] = None,
    status: HousekeepingStatus = HousekeepingStatus.PENDING,
    days_from_today: int = 0
) -> models.housekeeping.HousekeepingLog:

    log_create_schema = create_random_housekeeping_log_data(
        db, room_id, assigned_to_user_id, task_type, status, days_from_today
    )
    return services.housekeeping_service.create_housekeeping_log(
        db=db, log_in=log_create_schema, creator_user_id=creator_user_id
    )
