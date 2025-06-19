import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SAEnum, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID # For user_id if it's UUID
from sqlalchemy.orm import relationship
from ..db.base_class import Base

# --- Enums ---
class HousekeepingTaskType(str, enum.Enum):
    FULL_CLEAN = "FULL_CLEAN"
    STAY_OVER_CLEAN = "STAY_OVER_CLEAN"
    TURNDOWN_SERVICE = "TURNDOWN_SERVICE"
    MAINTENANCE_CHECK = "MAINTENANCE_CHECK"
    LINEN_CHANGE = "LINEN_CHANGE"
    VACANT_ROOM_CHECK = "VACANT_ROOM_CHECK"

class HousekeepingStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NEEDS_INSPECTION = "NEEDS_INSPECTION"
    ISSUE_REPORTED = "ISSUE_REPORTED"
    CANCELLED = "CANCELLED"

# --- Model ---
class HousekeepingLog(Base):
    __tablename__ = "housekeeping_logs"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    task_type = Column(SAEnum(HousekeepingTaskType, name="hk_task_type_enum", create_constraint=True), nullable=False)
    status = Column(SAEnum(HousekeepingStatus, name="hk_status_enum", create_constraint=True), nullable=False, default=HousekeepingStatus.PENDING)

    scheduled_date = Column(Date, nullable=False, index=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    notes_instructions = Column(Text, nullable=True)
    notes_issues_reported = Column(Text, nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    room = relationship("Room", backref="housekeeping_logs")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id], backref="assigned_housekeeping_tasks")
    creator = relationship("User", foreign_keys=[created_by_user_id], backref="created_housekeeping_logs")
    updater = relationship("User", foreign_keys=[updated_by_user_id], backref="updated_housekeeping_logs")
