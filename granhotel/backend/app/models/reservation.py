import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Enum as SAEnum, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from ..db.base_class import Base

class ReservationStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
    WAITLIST = "WAITLIST" # As per issue spec for waitlist management

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)

    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True) # Assuming direct room assignment for now

    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    reservation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    status = Column(SAEnum(ReservationStatus, name="reservation_status_enum"), nullable=False, default=ReservationStatus.PENDING, index=True)

    # total_price will store the calculated price. Numeric for precision.
    # Precision and scale can be adjusted based on currency needs.
    total_price = Column(Numeric(10, 2), nullable=True) # Allow null initially if price calculated later

    notes = Column(String, nullable=True)

    # Placeholder for who booked it, assuming a User model will exist later
    # booked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    guest = relationship("Guest", backref="reservations") # Simple backref for now
    room = relationship("Room", backref="reservations")   # Simple backref

    # user = relationship("User", backref="reservations") # For booked_by_user_id
