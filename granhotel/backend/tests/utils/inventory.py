from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from datetime import date, timedelta
import random

from app import models, schemas, services
from app.models.inventory import PurchaseOrderStatus
from tests.utils.product import create_random_product
from tests.utils.common import random_lower_string

# Supplier Utilities
def create_random_supplier(db: Session, suffix: str = "") -> models.inventory.Supplier:
    name = f"Test Supplier {suffix}{random_lower_string(4)}"
    email_prefix = f"supplier_{suffix}{random_lower_string(4)}"
    # Ensure email is unique for test runs
    supplier_email = f"{email_prefix}_{random_lower_string(3)}@example.com" # Add more randomness

    # Check if supplier with this name or email already exists to avoid test flakiness
    existing_by_name = db.query(models.inventory.Supplier).filter(models.inventory.Supplier.name == name).first()
    if existing_by_name:
        name = f"{name}_{random_lower_string(2)}"

    existing_by_email = db.query(models.inventory.Supplier).filter(models.inventory.Supplier.email == supplier_email).first()
    if existing_by_email:
        supplier_email = f"{random_lower_string(3)}_{supplier_email}"


    supplier_in_schema = schemas.inventory.SupplierCreate(
        name=name,
        email=supplier_email,
        contact_person=f"Contact {suffix} {random_lower_string(3)}",
        phone=f"555-01{random.randint(10,99)}"
    )
    return services.supplier_service.create_supplier(db=db, supplier_in=supplier_in_schema)

# InventoryItem Utilities
def ensure_inventory_item_exists(
    db: Session,
    product_id: int,
    initial_quantity: int = 0,
    low_stock_threshold: int = 5 # Default to non-zero to test low_stock_items better
) -> models.inventory.InventoryItem:
    '''Gets or creates an inventory item for a product using the service.'''
    return services.inventory_service.create_inventory_item_if_not_exists(
        db,
        product_id=product_id,
        initial_quantity=initial_quantity,
        low_stock_threshold=low_stock_threshold
    )

# PurchaseOrder Utilities
def create_random_po_items_data(
    db: Session,
    num_items: int = 1,
    product_name_suffix_base: str = "po_item"
) -> List[schemas.inventory.PurchaseOrderItemCreate]:
    items_data = []
    for i in range(num_items):
        product_suffix = f"_{product_name_suffix_base}_{i}_{random_lower_string(2)}"
        product = create_random_product(db, name_suffix=product_suffix)
        item_in = schemas.inventory.PurchaseOrderItemCreate(
            product_id=product.id,
            quantity_ordered=random.randint(5, 20),
            unit_price_paid=product.price
        )
        items_data.append(item_in)
    return items_data

def create_random_purchase_order(
    db: Session,
    supplier_id: Optional[int] = None,
    num_items: int = 1,
    status: PurchaseOrderStatus = PurchaseOrderStatus.ORDERED,
    po_notes_suffix: str = ""
) -> models.inventory.PurchaseOrder:
    if supplier_id is None:
        supplier = create_random_supplier(db, suffix=f"_po_util{random_lower_string(2)}")
        supplier_id = supplier.id

    po_item_name_suffix = random_lower_string(3)
    items_create_data = create_random_po_items_data(db, num_items=num_items, product_name_suffix_base=f"po_{po_item_name_suffix}")

    po_in_schema = schemas.inventory.PurchaseOrderCreate(
        supplier_id=supplier_id,
        items=items_create_data,
        order_date=date.today() - timedelta(days=random.randint(1, 5)),
        expected_delivery_date=date.today() + timedelta(days=random.randint(5,10)),
        status=status,
        notes=f"Test PO {po_notes_suffix} created by utility {random_lower_string(3)}."
    )
    return services.purchase_order_service.create_purchase_order(db=db, po_in=po_in_schema)
