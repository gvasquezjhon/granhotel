from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from ..db.base_class import Base
import enum

# Enum for Document Types (Peruvian context)
class DocumentType(str, enum.Enum):
    DNI = "DNI"
    RUC = "RUC" # Typically for companies, but can be for individuals with business
    PASSPORT = "PASSPORT"
    CE = "CE" # Carné de Extranjería

class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)

    document_type = Column(SAEnum(DocumentType, name="document_type_enum"), nullable=True) # Allow null if not always required
    document_number = Column(String, unique=True, index=True, nullable=True) # Unique if provided

    email = Column(String, unique=True, index=True, nullable=True) # Unique if provided
    phone_number = Column(String, nullable=True)

    address_street = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state_province = Column(String, nullable=True)
    address_postal_code = Column(String, nullable=True)
    address_country = Column(String, nullable=True, default="Perú") # Default to Perú

    nationality = Column(String, nullable=True, default="Peruana") # Default to Peruana

    preferences = Column(String, nullable=True) # Could be JSON or Text
    is_blacklisted = Column(Boolean, default=False, nullable=False)

    # GDPR/Data handling related fields (example)
    # consent_given_at = Column(DateTime(timezone=True), nullable=True)
    # data_retention_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (e.g., to Reservations) can be added later
    # reservations = relationship("Reservation", back_populates="guest")
