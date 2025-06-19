import enum
import uuid # For UUID primary key
from sqlalchemy import Column, String, Boolean, DateTime, func, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID # Specific UUID type for PostgreSQL
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    RECEPTIONIST = "RECEPTIONIST"
    HOUSEKEEPER = "HOUSEKEEPER"
    # GUEST_USER = "GUEST_USER" # If guests can also log in

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    is_active = Column(Boolean(), default=True, nullable=False)
    # is_superuser = Column(Boolean(), default=False) # Alternative to role string for simple admin

    role = Column(SAEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.RECEPTIONIST)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Example relationship if users create reservations (booked_by_user_id)
    # created_reservations = relationship("Reservation", back_populates="user", foreign_keys="[Reservation.booked_by_user_id]")
