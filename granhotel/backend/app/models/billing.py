import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SAEnum, ForeignKey, Numeric, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from ..db.base_class import Base
# Removed POSSale and Reservation direct imports as they are used as string table names in ForeignKey
# and relationships will handle the linkage. This avoids potential circular import issues at model definition time.

# --- Enums ---
class FolioStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    SETTLED = "SETTLED"
    VOIDED = "VOIDED"

class FolioTransactionType(str, enum.Enum):
    ROOM_CHARGE = "ROOM_CHARGE"
    POS_CHARGE = "POS_CHARGE"
    SERVICE_CHARGE = "SERVICE_CHARGE"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    DISCOUNT_ADJUSTMENT = "DISCOUNT_ADJUSTMENT"
    TAX_CHARGE = "TAX_CHARGE"

# --- Models ---
class GuestFolio(Base):
    __tablename__ = "guest_folios"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=True, index=True)

    status = Column(SAEnum(FolioStatus, name="folio_status_enum", create_constraint=True), nullable=False, default=FolioStatus.OPEN)

    total_charges = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_payments = Column(Numeric(12, 2), default=0.00, nullable=False)

    @hybrid_property
    def balance(self):
        return self.total_charges - self.total_payments

    opened_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    guest = relationship("Guest", backref="folios")
    reservation = relationship("Reservation", backref="folio")
    transactions = relationship("FolioTransaction", back_populates="guest_folio", cascade="all, delete-orphan", order_by="FolioTransaction.transaction_date")

class FolioTransaction(Base):
    __tablename__ = "folio_transactions"

    id = Column(Integer, primary_key=True, index=True)
    guest_folio_id = Column(Integer, ForeignKey("guest_folios.id"), nullable=False, index=True)

    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text, nullable=False)

    charge_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    payment_amount = Column(Numeric(10, 2), default=0.00, nullable=False)

    transaction_type = Column(SAEnum(FolioTransactionType, name="folio_transaction_type_enum", create_constraint=True), nullable=False)

    related_pos_sale_id = Column(Integer, ForeignKey("pos_sales.id"), nullable=True)
    related_reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    guest_folio = relationship("GuestFolio", back_populates="transactions")
    # Ensure correct model name for relationship if needed, e.g., "POSSale"
    pos_sale = relationship("POSSale", backref="folio_transactions")
    reservation_ref = relationship("Reservation")
    created_by = relationship("User")
