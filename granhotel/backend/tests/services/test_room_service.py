from sqlalchemy.orm import Session
from app import schemas
from app.services import room_service
from app.models import Room as RoomModel # Alias to avoid confusion
from tests.utils.room import create_random_room

def test_create_room_service(db: Session) -> None:
    room_in = schemas.RoomCreate(
        room_number="S101",
        name="Service Test Room",
        description="Room for service test",
        price=175.00,
        type="Suite",
        status="Cleaning"
    )
    room = room_service.create_room(db=db, room_in=room_in)
    assert room is not None
    assert room.room_number == "S101"
    assert room.name == "Service Test Room"
    assert room.price == 175.00
    assert isinstance(room, RoomModel) # Check it's a SQLAlchemy model instance

def test_get_room_service(db: Session) -> None:
    room_created = create_random_room(db, room_number_suffix="SVC_GET")
    room_fetched = room_service.get_room(db, room_id=room_created.id)
    assert room_fetched is not None
    assert room_fetched.id == room_created.id
    assert room_fetched.room_number == room_created.room_number

def test_get_room_by_room_number_service(db: Session) -> None:
    room_created = create_random_room(db, room_number_suffix="SVC_GET_NUM")
    room_fetched = room_service.get_room_by_room_number(db, room_number=room_created.room_number)
    assert room_fetched is not None
    assert room_fetched.id == room_created.id
    assert room_fetched.room_number == room_created.room_number

def test_get_rooms_service(db: Session) -> None:
    create_random_room(db, room_number_suffix="SVC_LIST1")
    create_random_room(db, room_number_suffix="SVC_LIST2")
    rooms = room_service.get_rooms(db, skip=0, limit=10)
    assert len(rooms) >= 2 # Check if at least 2 rooms were fetched, could be more if DB is not perfectly clean
    assert isinstance(rooms[0], RoomModel)

def test_update_room_service(db: Session) -> None:
    room_to_update = create_random_room(db, room_number_suffix="SVC_UPD")
    update_data = schemas.RoomUpdate(name="Updated Service Room Name", price=250.00)

    updated_room = room_service.update_room(db=db, room_db_obj=room_to_update, room_in=update_data)
    assert updated_room is not None
    assert updated_room.name == "Updated Service Room Name"
    assert updated_room.price == 250.00
    assert updated_room.id == room_to_update.id

def test_delete_room_service(db: Session) -> None:
    room_to_delete = create_random_room(db, room_number_suffix="SVC_DEL")
    room_id = room_to_delete.id

    deleted_room = room_service.delete_room(db=db, room_id=room_id)
    assert deleted_room is not None
    assert deleted_room.id == room_id

    # Verify it's no longer retrievable by ID
    assert room_service.get_room(db, room_id=room_id) is None
