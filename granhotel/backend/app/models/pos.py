import enum
from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SAEnum, ForeignKey, Numeric, Text, Date
from sqlalchemy.dialects.postgresql import UUID # For user_id, guest_id
from sqlalchemy.orm import relationship
from ..db.base_class import Base

# --- Enums ---
class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD_DEBIT = "CARD_DEBIT"
    CARD_CREDIT = "CARD_CREDIT"
    YAPE = "YAPE"
    PLIN = "PLIN"
    TRANSFER = "BANK_TRANSFER"
    ROOM_CHARGE = "ROOM_CHARGE"
    OTHER = "OTHER"

class POSSaleStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    VOIDED = "VOIDED"
    PENDING_PAYMENT = "PENDING_PAYMENT"

# --- Models ---
class POSSale(Base):
    __tablename__ = "pos_sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    cashier_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=True, index=True)

    total_amount_before_tax = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False)
    total_amount_after_tax = Column(Numeric(10, 2), nullable=False)

    payment_method = Column(SAEnum(PaymentMethod, name="pos_payment_method_enum", create_constraint=True), nullable=True)
    payment_reference = Column(String(100), nullable=True)

    status = Column(SAEnum(POSSaleStatus, name="pos_sale_status_enum", create_constraint=True), nullable=False, default=POSSaleStatus.COMPLETED)

    notes = Column(Text, nullable=True)
    void_reason = Column(Text, nullable=True)
    voided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    voided_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    cashier = relationship("User", foreign_keys=[cashier_user_id], backref="pos_sales_handled")
    guest = relationship("Guest", foreign_keys=[guest_id], backref="pos_sales") # backref on Guest model
    voided_by = relationship("User", foreign_keys=[voided_by_user_id], backref="pos_sales_voided")
    items = relationship("POSSaleItem", back_populates="pos_sale", cascade="all, delete-orphan")

class POSSaleItem(Base):
    __tablename__ = "pos_sale_items"

    id = Column(Integer, primary_key=True, index=True)
    pos_sale_id = Column(Integer, ForeignKey("pos_sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    unit_price_before_tax = Column(Numeric(10, 2), nullable=False)
    tax_rate_applied = Column(Numeric(4,2), nullable=False, default=0.18)
    tax_amount_for_item = Column(Numeric(10, 2), nullable=False)
    total_price_for_item_after_tax = Column(Numeric(10,2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    pos_sale = relationship("POSSale", back_populates="items")
    product = relationship("Product") # No backref needed if Product doesn't link back to POSSaleItem directly
