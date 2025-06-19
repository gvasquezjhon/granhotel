from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.schemas.room import RoomCreate, RoomUpdate # Import RoomUpdate
from tests.utils.room import create_random_room # Utility to create rooms

def test_create_room(client: TestClient, db: Session) -> None:
    data = {
        "room_number": "T101",
        "name": "Test Room API",
        "description": "Room for API test",
        "price": 120.50,
        "type": "Single",
        "status": "Available",
        "floor": 1
    }
    response = client.post(f"{settings.API_V1_STR}/rooms/", json=data)
    assert response.status_code == 201, response.text # Include response text on failure
    content = response.json()
    assert content["room_number"] == data["room_number"]
    assert content["name"] == data["name"]
    assert "id" in content

def test_create_room_duplicate_room_number(client: TestClient, db: Session) -> None:
    room = create_random_room(db, room_number_suffix="API_DUP") # Create a room first
    data = {
        "room_number": room.room_number, # Use the same room number
        "name": "Test Room API Duplicate",
        "price": 130.00,
        "type": "Single",
        "status": "Available"
    }
    response = client.post(f"{settings.API_V1_STR}/rooms/", json=data)
    assert response.status_code == 400, response.text
    content = response.json()
    assert "detail" in content
    assert f"Room with number '{room.room_number}' already exists" in content["detail"]

def test_read_rooms(client: TestClient, db: Session) -> None:
    room1 = create_random_room(db, room_number_suffix="R1")
    room2 = create_random_room(db, room_number_suffix="R2")
    response = client.get(f"{settings.API_V1_STR}/rooms/")
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    # Ensure the created rooms are in the response (order might vary)
    room_ids = [r["id"] for r in content]
    assert room1.id in room_ids
    assert room2.id in room_ids


def test_read_room(client: TestClient, db: Session) -> None:
    room = create_random_room(db, room_number_suffix="GET")
    response = client.get(f"{settings.API_V1_STR}/rooms/{room.id}")
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == room.id
    assert content["room_number"] == room.room_number

def test_read_room_not_found(client: TestClient, db: Session) -> None:
    response = client.get(f"{settings.API_V1_STR}/rooms/99999") # Non-existent ID
    assert response.status_code == 404, response.text
    content = response.json()
    assert content["detail"] == "Room not found"

def test_update_room(client: TestClient, db: Session) -> None:
    room = create_random_room(db, room_number_suffix="UPD")
    update_data = RoomUpdate(name="Updated Test Room", price=200.75, status="Maintenance").model_dump(exclude_unset=True)

    response = client.put(f"{settings.API_V1_STR}/rooms/{room.id}", json=update_data)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["name"] == update_data["name"]
    assert content["price"] == update_data["price"]
    assert content["status"] == update_data["status"]
    assert content["id"] == room.id

def test_update_room_not_found(client: TestClient, db: Session) -> None:
    update_data = RoomUpdate(name="Updated Non Existent Room").model_dump(exclude_unset=True)
    response = client.put(f"{settings.API_V1_STR}/rooms/99999", json=update_data)
    assert response.status_code == 404, response.text

def test_update_room_duplicate_room_number(client: TestClient, db: Session) -> None:
    room1 = create_random_room(db, room_number_suffix="UPD_DUP1")
    room2 = create_random_room(db, room_number_suffix="UPD_DUP2") # This room's number will be used

    update_data = RoomUpdate(room_number=room1.room_number).model_dump(exclude_unset=True)

    response = client.put(f"{settings.API_V1_STR}/rooms/{room2.id}", json=update_data)
    assert response.status_code == 400, response.text
    content = response.json()
    assert f"Room with number '{room1.room_number}' already exists" in content["detail"]


def test_delete_room(client: TestClient, db: Session) -> None:
    room = create_random_room(db, room_number_suffix="DEL")
    response = client.delete(f"{settings.API_V1_STR}/rooms/{room.id}")
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == room.id

    # Verify it's actually deleted
    get_response = client.get(f"{settings.API_V1_STR}/rooms/{room.id}")
    assert get_response.status_code == 404, get_response.text

def test_delete_room_not_found(client: TestClient, db: Session) -> None:
    response = client.delete(f"{settings.API_V1_STR}/rooms/99999")
    assert response.status_code == 404, response.text
