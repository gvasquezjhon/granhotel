import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import schemas, services, models
from tests.utils.inventory import create_random_supplier # Utility to create suppliers
from tests.utils.common import random_lower_string, random_email # For unique test data

def test_create_supplier_service(db: Session):
    name = f"Supplier Inc {random_lower_string(4)}"
    email = random_email(prefix=f"contact_{random_lower_string(3)}")
    supplier_in = schemas.inventory.SupplierCreate(
        name=name,
        email=email,
        contact_person="John Doe",
        phone="555-1234",
        address="123 Main St"
    )
    supplier = services.supplier_service.create_supplier(db, supplier_in)
    assert supplier is not None
    assert supplier.name == name
    assert supplier.email == email
    assert supplier.contact_person == "John Doe"

def test_create_supplier_duplicate_name(db: Session):
    name = f"Duplicate Name Supplier {random_lower_string(3)}"
    # Create first supplier
    services.supplier_service.create_supplier(db, schemas.inventory.SupplierCreate(name=name, email=random_email(prefix="orig_dup_name")))

    # Attempt to create second supplier with same name
    supplier_in_dup = schemas.inventory.SupplierCreate(name=name, email=random_email(prefix="dup_name_other_email"))
    with pytest.raises(HTTPException) as exc_info:
        services.supplier_service.create_supplier(db, supplier_in_dup)
    assert exc_info.value.status_code == 400
    assert "name" in exc_info.value.detail.lower()
    assert "already exists" in exc_info.value.detail.lower()

def test_create_supplier_duplicate_email(db: Session):
    email = random_email(prefix=f"dup_email_test_{random_lower_string(3)}")
    # Create first supplier
    services.supplier_service.create_supplier(db, schemas.inventory.SupplierCreate(name=f"Supplier Original Name {random_lower_string(3)}", email=email))

    # Attempt to create second supplier with same email
    supplier_in_dup = schemas.inventory.SupplierCreate(name=f"Supplier Diff Name {random_lower_string(3)}", email=email)
    with pytest.raises(HTTPException) as exc_info:
        services.supplier_service.create_supplier(db, supplier_in_dup)
    assert exc_info.value.status_code == 400
    assert "email" in exc_info.value.detail.lower()
    assert "already exists" in exc_info.value.detail.lower()

def test_get_supplier_service(db: Session):
    supplier_created = create_random_supplier(db, suffix="_get")
    supplier_fetched = services.supplier_service.get_supplier(db, supplier_id=supplier_created.id)
    assert supplier_fetched is not None
    assert supplier_fetched.id == supplier_created.id
    assert supplier_fetched.name == supplier_created.name

def test_get_supplier_not_found(db: Session):
    supplier = services.supplier_service.get_supplier(db, supplier_id=999999) # Non-existent ID
    assert supplier is None

def test_get_all_suppliers_service(db: Session):
    s1 = create_random_supplier(db, suffix="_list1")
    s2 = create_random_supplier(db, suffix="_list2")

    suppliers = services.supplier_service.get_all_suppliers(db, limit=10)
    assert len(suppliers) >= 2

    supplier_ids = [s.id for s in suppliers]
    assert s1.id in supplier_ids
    assert s2.id in supplier_ids

    # Check if names are ordered (default order_by name)
    # This requires names to be sortable in a predictable way for a simple check
    # For random names, just check instance type.
    if len(suppliers) > 1:
        assert isinstance(suppliers[0], models.inventory.Supplier)
        # To strictly test ordering, create suppliers with known ordered names
        # Example: s_a = create_supplier_with_name(db, "A Supplier"), s_b = create_supplier_with_name(db, "B Supplier")
        # Then check if s_a appears before s_b in the list.

def test_update_supplier_service(db: Session):
    supplier = create_random_supplier(db, suffix="_upd")
    new_name = f"Updated Supplier Name {random_lower_string(3)}"
    new_email = random_email(prefix=f"updated_{random_lower_string(3)}")

    supplier_update_schema = schemas.inventory.SupplierUpdate(
        name=new_name,
        email=new_email,
        contact_person="Jane Updated"
    )
    updated_supplier = services.supplier_service.update_supplier(db, supplier_db_obj=supplier, supplier_in=supplier_update_schema)

    assert updated_supplier is not None
    assert updated_supplier.name == new_name
    assert updated_supplier.email == new_email
    assert updated_supplier.contact_person == "Jane Updated"
    assert updated_supplier.id == supplier.id

def test_update_supplier_name_conflict(db: Session):
    supplier1 = create_random_supplier(db, suffix="_upd_name_c1")
    supplier2 = create_random_supplier(db, suffix="_upd_name_c2")

    # Try to update supplier2 with supplier1's name
    update_conflict_schema = schemas.inventory.SupplierUpdate(name=supplier1.name)
    with pytest.raises(HTTPException) as exc_info:
        services.supplier_service.update_supplier(db, supplier_db_obj=supplier2, supplier_in=update_conflict_schema)
    assert exc_info.value.status_code == 400
    assert "name" in exc_info.value.detail.lower()

def test_update_supplier_email_conflict(db: Session):
    supplier1 = create_random_supplier(db, suffix="_upd_email_c1")
    supplier2 = create_random_supplier(db, suffix="_upd_email_c2")

    # Try to update supplier2 with supplier1's email
    update_conflict_schema = schemas.inventory.SupplierUpdate(email=supplier1.email)
    with pytest.raises(HTTPException) as exc_info:
        services.supplier_service.update_supplier(db, supplier_db_obj=supplier2, supplier_in=update_conflict_schema)
    assert exc_info.value.status_code == 400
    assert "email" in exc_info.value.detail.lower()

def test_delete_supplier_service(db: Session):
    supplier = create_random_supplier(db, suffix="_del_ok") # This supplier has no POs
    supplier_id = supplier.id

    deleted_supplier = services.supplier_service.delete_supplier(db, supplier_id=supplier_id)
    assert deleted_supplier is not None
    assert deleted_supplier.id == supplier_id

    assert services.supplier_service.get_supplier(db, supplier_id=supplier_id) is None

def test_delete_supplier_with_purchase_orders(db: Session):
    from tests.utils.inventory import create_random_purchase_order # Import here to avoid circular deps at module level if utils are complex

    supplier_with_po = create_random_supplier(db, suffix="_del_w_po")
    # Create a PO linked to this supplier
    create_random_purchase_order(db, supplier_id=supplier_with_po.id, num_items=1)

    db.refresh(supplier_with_po)
    # Ensure the relationship is loaded if it's lazy and accessed by the service
    # One way to ensure it's loaded before the service call:
    # supplier_with_po = db.query(models.inventory.Supplier).options(joinedload(models.inventory.Supplier.purchase_orders)).filter_by(id=supplier_with_po.id).one()

    with pytest.raises(HTTPException) as exc_info:
        services.supplier_service.delete_supplier(db, supplier_id=supplier_with_po.id)
    assert exc_info.value.status_code == 400
    assert "associated purchase orders" in exc_info.value.detail.lower()

def test_update_supplier_no_change(db: Session):
    supplier = create_random_supplier(db, suffix="_upd_nochange")
    # Empty update schema
    supplier_update_schema = schemas.inventory.SupplierUpdate()
    updated_supplier = services.supplier_service.update_supplier(db, supplier_db_obj=supplier, supplier_in=supplier_update_schema)
    assert updated_supplier is not None
    assert updated_supplier.name == supplier.name # Should be unchanged
    assert updated_supplier.email == supplier.email # Should be unchanged

def test_update_supplier_clear_optional_fields(db: Session):
    supplier = create_random_supplier(db, suffix="_upd_clear")
    supplier.contact_person = "Initial Contact" # Ensure it has a value
    supplier.phone = "12345"
    supplier.address = "Initial Address"
    db.commit()
    db.refresh(supplier)

    supplier_update_schema = schemas.inventory.SupplierUpdate(
        contact_person=None, phone=None, address=None
    )
    updated_supplier = services.supplier_service.update_supplier(db, supplier_db_obj=supplier, supplier_in=supplier_update_schema)
    assert updated_supplier.contact_person is None
    assert updated_supplier.phone is None
    assert updated_supplier.address is None
