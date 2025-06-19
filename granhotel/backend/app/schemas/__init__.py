from .room import Room, RoomCreate, RoomUpdate, RoomBase  # noqa , added RoomBase
from .guest import Guest, GuestCreate, GuestUpdate, GuestBase as GuestBaseSchema, DocumentType as GuestDocumentType # noqa, added GuestBaseSchema and aliased Enum
# GuestDocumentType could be useful if you need to expose the enum via API directly
