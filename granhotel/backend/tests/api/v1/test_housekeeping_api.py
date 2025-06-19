from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
import uuid

from app.core.config import settings
from app.models.user import UserRole # For creating users with specific roles
from app.models.housekeeping import HousekeepingStatus, HousekeepingTaskType
from app.schemas.housekeeping import HousekeepingLogCreate, HousekeepingLogStatusUpdate, HousekeepingLogAssignmentUpdate, HousekeepingLogUpdate
from tests.utils.user import create_user_in_db
from tests.utils.room import create_random_room
from tests.utils.housekeeping import create_random_housekeeper, create_random_housekeeping_log, create_random_housekeeping_log_data
from app.core.security import create_access_token # Use this directly for test tokens
from tests.utils.common import random_email, random_lower_string


API_V1_HK_URL = f"{settings.API_V1_STR}/housekeeping/logs" # Base URL for logs

# Local get_auth_headers, similar to other API test files
def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}


def test_create_housekeeping_log_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_chklog"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)

    room = create_random_room(db, room_number_suffix="_hk_api_cr")
    housekeeper = create_random_housekeeper(db, suffix="_hk_api_cr")

    log_data = {
        "room_id": room.id,
        "assigned_to_user_id": str(housekeeper.id),
        "task_type": HousekeepingTaskType.FULL_CLEAN.value,
        "scheduled_date": (date.today() + timedelta(days=1)).isoformat(),
        "notes_instructions": "API Test: Full clean instructions"
    }

    response = client.post(f"{API_V1_HK_URL}/", json=log_data, headers=manager_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["room_id"] == room.id
    assert content["assigned_to_user_id"] == str(housekeeper.id)
    assert content["task_type"] == HousekeepingTaskType.FULL_CLEAN.value
    assert content["status"] == HousekeepingStatus.PENDING.value

def test_create_hk_log_api_as_housekeeper_fail(client: TestClient, db: Session):
    hk_user = create_random_housekeeper(db, suffix="_hk_chklog_fail")
    hk_headers = get_auth_headers(hk_user.id, hk_user.role)
    room = create_random_room(db, room_number_suffix="_hk_api_crf")
    log_data = {"room_id": room.id, "task_type": HousekeepingTaskType.LINEN_CHANGE.value, "scheduled_date": date.today().isoformat()}

    response = client.post(f"{API_V1_HK_URL}/", json=log_data, headers=hk_headers)
    assert response.status_code == 403

def test_read_all_housekeeping_logs_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_rhklogs"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)

    create_random_housekeeping_log(db, creator_user_id=manager_user.id, days_from_today=1)
    create_random_housekeeping_log(db, creator_user_id=manager_user.id, days_from_today=2)

    response = client.get(f"{API_V1_HK_URL}/", headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2

def test_read_my_assigned_logs_api_as_housekeeper(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_rmyhk"))
    housekeeper_user = create_random_housekeeper(db, suffix="_rmyhk")
    hk_headers = get_auth_headers(housekeeper_user.id, housekeeper_user.role)

    create_random_housekeeping_log(db, creator_user_id=manager_user.id, assigned_to_user_id=housekeeper_user.id, days_from_today=0)
    create_random_housekeeping_log(db, creator_user_id=manager_user.id, days_from_today=0) # Unassigned or assigned to another

    response = client.get(f"{API_V1_HK_URL}/staff/me", headers=hk_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    # This user might have other tasks from other tests, so check >=1 and all returned are assigned to them
    assert len(content) >= 1
    assert all(log["assigned_to_user_id"] == str(housekeeper_user.id) for log in content)


def test_read_single_hk_log_api_as_assigned_hk(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_rsinglehk"))
    hk_user = create_random_housekeeper(db, suffix="_rsinglehk")
    hk_headers = get_auth_headers(hk_user.id, hk_user.role)

    hk_log = create_random_housekeeping_log(db, creator_user_id=manager_user.id, assigned_to_user_id=hk_user.id)

    response = client.get(f"{API_V1_HK_URL}/{hk_log.id}", headers=hk_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == hk_log.id

def test_read_single_hk_log_api_unassigned_hk_fail(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_rsinglehkf"))
    hk_user_viewer = create_random_housekeeper(db, suffix="_rsinglehkf_v")
    hk_user_assigned = create_random_housekeeper(db, suffix="_rsinglehkf_a")
    viewer_headers = get_auth_headers(hk_user_viewer.id, hk_user_viewer.role)

    hk_log_other = create_random_housekeeping_log(db, creator_user_id=manager_user.id, assigned_to_user_id=hk_user_assigned.id)

    response = client.get(f"{API_V1_HK_URL}/{hk_log_other.id}", headers=viewer_headers)
    assert response.status_code == 403

def test_update_log_status_api_by_assigned_hk(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_uhkstat"))
    hk_user = create_random_housekeeper(db, suffix="_uhkstat")
    hk_headers = get_auth_headers(hk_user.id, hk_user.role)

    hk_log = create_random_housekeeping_log(db, creator_user_id=manager_user.id, assigned_to_user_id=hk_user.id, status=HousekeepingStatus.PENDING)

    status_update_data = {"status": HousekeepingStatus.IN_PROGRESS.value, "notes_issues_reported": "Started cleaning."}
    response = client.patch(f"{API_V1_HK_URL}/{hk_log.id}/status", json=status_update_data, headers=hk_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["status"] == HousekeepingStatus.IN_PROGRESS.value
    assert content["notes_issues_reported"] == "Started cleaning."
    assert content["started_at"] is not None

def test_update_log_status_api_by_hk_invalid_transition(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_uhkstat_inv"))
    hk_user = create_random_housekeeper(db, suffix="_uhkstat_inv")
    hk_headers = get_auth_headers(hk_user.id, hk_user.role)

    # Create a PENDING task, housekeeper tries to set it back to PENDING (which is not in allowed_statuses_for_hk if current status is PENDING)
    # The endpoint logic allows IN_PROGRESS -> PENDING, but not PENDING -> PENDING if it's filtered by allowed_statuses_for_hk
    # The current endpoint logic for housekeeper status update:
    # `if status_update_in.status not in allowed_statuses_for_hk:`
    # `allowed_statuses_for_hk = [IN_PROGRESS, COMPLETED, NEEDS_INSPECTION, ISSUE_REPORTED]`
    # So setting to PENDING is disallowed for housekeeper unless they are also manager/admin.
    hk_log = create_random_housekeeping_log(db, creator_user_id=manager_user.id, assigned_to_user_id=hk_user.id, status=HousekeepingStatus.IN_PROGRESS)

    status_update_data = {"status": HousekeepingStatus.PENDING.value} # This is allowed from IN_PROGRESS by endpoint logic
    response = client.patch(f"{API_V1_HK_URL}/{hk_log.id}/status", json=status_update_data, headers=hk_headers)
    assert response.status_code == 200, response.text # Should be allowed as per endpoint logic: IN_PROGRESS -> PENDING is allowed

    # Try setting to CANCELLED (which is not in allowed_statuses_for_hk)
    status_update_data_cancelled = {"status": HousekeepingStatus.CANCELLED.value}
    response_cancel = client.patch(f"{API_V1_HK_URL}/{hk_log.id}/status", json=status_update_data_cancelled, headers=hk_headers)
    assert response_cancel.status_code == 403 # Forbidden


def test_assign_log_task_api_as_admin(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, email=random_email("_admin_ahk"))
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)

    hk_log = create_random_housekeeping_log(db, creator_user_id=admin_user.id, assigned_to_user_id=None)
    new_assignee = create_random_housekeeper(db, suffix="_ahk_new")

    assignment_data = {"assigned_to_user_id": str(new_assignee.id)}
    response = client.patch(f"{API_V1_HK_URL}/{hk_log.id}/assign", json=assignment_data, headers=admin_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["assigned_to_user_id"] == str(new_assignee.id)

def test_update_log_details_api_as_manager(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_upd_hk_det"))
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)

    hk_log = create_random_housekeeping_log(db, creator_user_id=manager_user.id)
    new_room = create_random_room(db, room_number_suffix="_hk_api_upd_room")
    new_notes = "Updated API notes for details."
    new_scheduled_date = (date.today() + timedelta(days=3)).isoformat()

    update_payload = {
        "room_id": new_room.id,
        "notes_instructions": new_notes,
        "scheduled_date": new_scheduled_date,
        "task_type": HousekeepingTaskType.MAINTENANCE_CHECK.value
    }
    response = client.put(f"{API_V1_HK_URL}/{hk_log.id}", json=update_payload, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["room_id"] == new_room.id
    assert content["notes_instructions"] == new_notes
    assert content["scheduled_date"] == new_scheduled_date
    assert content["task_type"] == HousekeepingTaskType.MAINTENANCE_CHECK.value
