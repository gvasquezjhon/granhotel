from sqlalchemy.orm import Session
from app import models, schemas
from app.services import guest_service # Use the actual service
from app.models.guest import DocumentType
import random
import string

def random_lower_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"

def random_document_number(doc_type: DocumentType) -> str:
    if doc_type == DocumentType.DNI:
        return "".join(random.choices(string.digits, k=8))
    if doc_type == DocumentType.RUC:
        return "".join(random.choices(string.digits, k=11))
    if doc_type == DocumentType.CE: # Carné de Extranjería
        # Typically starts with a letter or two then digits. Example: 'E1234567' or 'V123456789'
        # For simplicity, let's use a common pattern like 'CE' + 7 digits.
        return "CE" + "".join(random.choices(string.digits, k=7))
    if doc_type == DocumentType.PASSPORT:
        # Passport numbers vary greatly. Max 20 chars as per schema.
        # Let's generate something like 'PASS' + 6 alphanumeric.
        return "PASS" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return random_lower_string(10) # Fallback for undefined types


def create_random_guest(db: Session, suffix: str = "") -> models.Guest:
    doc_type = random.choice(list(DocumentType))
    # Construct a somewhat unique document number for testing to avoid collisions during test runs
    # The service layer already checks for uniqueness, this is to help test setup itself.
    unique_part = random_lower_string(4) + "".join(random.choices(string.digits, k=4))
    test_doc_num = f"{doc_type.value[:3].upper()}{unique_part}{suffix}"[:20] # Ensure it fits in constr

    guest_in = schemas.GuestCreate(
        first_name=f"TestF{suffix}",
        last_name=f"TestL{suffix}",
        email=f"test{suffix}{random_lower_string(3)}@example.com",
        document_type=doc_type,
        document_number=test_doc_num,
        phone_number="123456789",
        address_country="Perú", # Test default
        nationality="Peruana" # Test default
    )
    return guest_service.create_guest(db=db, guest_in=guest_in)

def create_guest_with_data(db: Session, guest_data: schemas.GuestCreate) -> models.Guest:
    return guest_service.create_guest(db=db, guest_in=guest_data)
