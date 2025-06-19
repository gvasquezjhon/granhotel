import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date, timedelta, datetime, timezone
import uuid

from app import schemas, services, models
from app.models.housekeeping import HousekeepingStatus, HousekeepingTaskType
from app.models.user import UserRole
from tests.utils.user import create_user_in_db
from tests.utils.room import create_random_room
from tests.utils.housekeeping import create_random_housekeeper, create_random_housekeeping_log, create_random_housekeeping_log_data
from tests.utils.common import random_lower_string

def test_create_housekeeping_log_service(db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_c_hklog{random_lower_string(3)}@example.com")
    room = create_random_room(db, room_number_suffix="_hk_log_svc")
    housekeeper = create_random_housekeeper(db, suffix="_hk_log_svc")

    log_in_schema = create_random_housekeeping_log_data(
        db, room_id=room.id, assigned_to_user_id=housekeeper.id, task_type=HousekeepingTaskType.FULL_CLEAN
    )

    hk_log = services.housekeeping_service.create_housekeeping_log(db, log_in_schema, manager_user.id)

    assert hk_log is not None
    assert hk_log.room_id == room.id
    assert hk_log.assigned_to_user_id == housekeeper.id
    assert hk_log.task_type == HousekeepingTaskType.FULL_CLEAN
    assert hk_log.status == HousekeepingStatus.PENDING
    assert hk_log.created_by_user_id == manager_user.id
    assert hk_log.room is not None
    assert hk_log.assigned_to is not None
    assert hk_log.creator is not None
    assert hk_log.updater is not None


def test_create_hk_log_invalid_room(db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_hk_nr{random_lower_string(3)}@example.com")
    # Use a non-existent room_id without creating a room object for it via utility
    log_in_invalid_room_schema = schemas.housekeeping.HousekeepingLogCreate(
        room_id=99999,
        task_type=HousekeepingTaskType.FULL_CLEAN,
        scheduled_date=date.today()
    )
    with pytest.raises(HTTPException) as exc_info:
        services.housekeeping_service.create_housekeeping_log(db, log_in_invalid_room_schema, manager_user.id)
    assert exc_info.value.status_code == 404
    assert "room with id 99999 not found" in exc_info.value.detail.lower()

def test_create_hk_log_invalid_assignee(db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_hk_ia{random_lower_string(3)}@example.com")
    room = create_random_room(db, room_number_suffix="_hk_ia")
    non_existent_user_id = uuid.uuid4()
    log_in_invalid_assignee_schema = schemas.housekeeping.HousekeepingLogCreate(
        room_id=room.id,
        assigned_to_user_id=non_existent_user_id,
        task_type=HousekeepingTaskType.FULL_CLEAN,
        scheduled_date=date.today()
    )
    with pytest.raises(HTTPException) as exc_info:
        services.housekeeping_service.create_housekeeping_log(db, log_in_invalid_assignee_schema, manager_user.id)
    assert exc_info.value.status_code == 404
    assert f"assigned user with id {non_existent_user_id} not found" in exc_info.value.detail.lower()

def test_create_hk_log_assignee_invalid_role(db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_hk_nhk{random_lower_string(3)}@example.com")
    # Create a user who is not a housekeeper, manager or admin
    guest_role_user = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=f"recep_hk_nhk{random_lower_string(3)}@example.com") # Assuming RECEPTIONIST is not allowed
    room = create_random_room(db, room_number_suffix="_hk_nhk")
    log_in_assign_invalid_role_schema = schemas.housekeeping.HousekeepingLogCreate(
        room_id=room.id,
        assigned_to_user_id=guest_role_user.id,
        task_type=HousekeepingTaskType.FULL_CLEAN,
        scheduled_date=date.today()
    )
    with pytest.raises(HTTPException) as exc_info:
        services.housekeeping_service.create_housekeeping_log(db, log_in_assign_invalid_role_schema, manager_user.id)
    assert exc_info.value.status_code == 400
    assert f"user id {guest_role_user.id} does not have an appropriate role" in exc_info.value.detail.lower()


def test_get_housekeeping_log_service(db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_ghk{random_lower_string(3)}@example.com")
    hk_log_created = create_random_housekeeping_log(db, creator_user_id=manager_user.id)

    hk_log_fetched = services.housekeeping_service.get_housekeeping_log(db, log_id=hk_log_created.id)
    assert hk_log_fetched is not None
    assert hk_log_fetched.id == hk_log_created.id
    assert hk_log_fetched.room is not None
    if hk_log_created.assigned_to_user_id:
        assert hk_log_fetched.assigned_to is not None
    assert hk_log_fetched.creator is not None
    assert hk_log_fetched.updater is not None


def test_get_housekeeping_logs_filtering(db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_ghk_filt{random_lower_string(3)}@example.com")
    hk1 = create_random_housekeeper(db, suffix="_hkf1")
    hk2 = create_random_housekeeper(db, suffix="_hkf2")
    room1 = create_random_room(db, "_hkf_r1")
    room2 = create_random_room(db, "_hkf_r2")

    log1 = create_random_housekeeping_log(db, manager.id, room_id=room1.id, assigned_to_user_id=hk1.id, status=HousekeepingStatus.PENDING, task_type=HousekeepingTaskType.FULL_CLEAN, days_from_today=1)
    log2 = create_random_housekeeping_log(db, manager.id, room_id=room2.id, assigned_to_user_id=hk1.id, status=HousekeepingStatus.COMPLETED, task_type=HousekeepingTaskType.STAY_OVER_CLEAN, days_from_today=1)
    log3 = create_random_housekeeping_log(db, manager.id, room_id=room1.id, assigned_to_user_id=hk2.id, status=HousekeepingStatus.PENDING, task_type=HousekeepingTaskType.FULL_CLEAN, days_from_today=2)

    logs_hk1 = services.housekeeping_service.get_housekeeping_logs(db, assigned_to_user_id=hk1.id)
    assert len(logs_hk1) == 2 # log1 and log2
    assert all(log.assigned_to_user_id == hk1.id for log in logs_hk1)

    logs_pending = services.housekeeping_service.get_housekeeping_logs(db, status=HousekeepingStatus.PENDING)
    assert len(logs_pending) >= 2 # log1 and log3, could be more from other tests
    assert all(log.status == HousekeepingStatus.PENDING for log in logs_pending if log.id in [log1.id, log3.id])

    logs_room1 = services.housekeeping_service.get_housekeeping_logs(db, room_id=room1.id)
    assert len(logs_room1) == 2 # log1 and log3

    logs_full_clean = services.housekeeping_service.get_housekeeping_logs(db, task_type=HousekeepingTaskType.FULL_CLEAN)
    assert len(logs_full_clean) >= 2 # log1 and log3


def test_update_housekeeping_log_status_service(db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_uhk_stat{random_lower_string(3)}@example.com")
    housekeeper = create_random_housekeeper(db, suffix="_uhk_stat")
    hk_log = create_random_housekeeping_log(db, creator_user_id=manager.id, assigned_to_user_id=housekeeper.id, status=HousekeepingStatus.PENDING)

    time_before_start = datetime.now(timezone.utc) - timedelta(seconds=2) # Allow a bit more leeway
    updated_log_inprogress = services.housekeeping_service.update_housekeeping_log_status(
        db, log_id=hk_log.id, new_status=HousekeepingStatus.IN_PROGRESS, updater_user_id=housekeeper.id
    )
    time_after_start = datetime.now(timezone.utc) + timedelta(seconds=2)
    assert updated_log_inprogress.status == HousekeepingStatus.IN_PROGRESS
    assert updated_log_inprogress.started_at is not None
    assert time_before_start <= updated_log_inprogress.started_at <= time_after_start
    assert updated_log_inprogress.updated_by_user_id == housekeeper.id

    time_before_complete = datetime.now(timezone.utc) - timedelta(seconds=2)
    updated_log_completed = services.housekeeping_service.update_housekeeping_log_status(
        db, log_id=hk_log.id, new_status=HousekeepingStatus.COMPLETED, updater_user_id=housekeeper.id, notes_issues="All good."
    )
    time_after_complete = datetime.now(timezone.utc) + timedelta(seconds=2)
    assert updated_log_completed.status == HousekeepingStatus.COMPLETED
    assert updated_log_completed.completed_at is not None
    assert time_before_complete <= updated_log_completed.completed_at <= time_after_complete
    assert updated_log_completed.notes_issues_reported == "All good."

def test_assign_housekeeping_task_service(db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_ahk{random_lower_string(3)}@example.com")
    hk_log_unassigned = create_random_housekeeping_log(db, creator_user_id=manager.id, assigned_to_user_id=None)
    new_housekeeper = create_random_housekeeper(db, suffix="_new_assignee")

    assigned_log = services.housekeeping_service.assign_housekeeping_task(
        db, log_id=hk_log_unassigned.id, assigned_to_user_id=new_housekeeper.id, updater_user_id=manager.id
    )
    assert assigned_log.assigned_to_user_id == new_housekeeper.id
    assert assigned_log.updated_by_user_id == manager.id

    # Test unassigning
    unassigned_log = services.housekeeping_service.assign_housekeeping_task(
        db, log_id=assigned_log.id, assigned_to_user_id=None, updater_user_id=manager.id
    )
    assert unassigned_log.assigned_to_user_id is None


def test_update_housekeeping_log_details_service(db: Session):
    manager = create_user_in_db(db, role=UserRole.MANAGER, email=f"manager_uhk_det{random_lower_string(3)}@example.com")
    hk_log = create_random_housekeeping_log(db, creator_user_id=manager.id)

    new_room = create_random_room(db, room_number_suffix="_uhk_nr")
    new_hk = create_random_housekeeper(db, suffix="_uhk_nhk")
    new_date = date.today() + timedelta(days=5)
    new_notes = "Updated instructions."

    update_schema = schemas.housekeeping.HousekeepingLogUpdate(
        room_id=new_room.id,
        assigned_to_user_id=new_hk.id,
        task_type=HousekeepingTaskType.LINEN_CHANGE,
        status=HousekeepingStatus.PENDING, # Status can be part of general update
        scheduled_date=new_date,
        notes_instructions=new_notes
    )
    updated_log = services.housekeeping_service.update_housekeeping_log_details(
        db, log_id=hk_log.id, log_in=update_schema, updater_user_id=manager.id
    )
    assert updated_log.room_id == new_room.id
    assert updated_log.assigned_to_user_id == new_hk.id
    assert updated_log.task_type == HousekeepingTaskType.LINEN_CHANGE
    assert updated_log.scheduled_date == new_date
    assert updated_log.notes_instructions == new_notes
    assert updated_log.updated_by_user_id == manager.id
