import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from app import schemas, services, models
from tests.utils.product import create_random_product_category, create_random_product, random_lower_string

# ProductCategory Service Tests
def test_create_product_category_service(db: Session):
    name = f"Electronics_{random_lower_string(3)}"
    category_in = schemas.ProductCategoryCreate(name=name, description="Gadgets and devices")
    category = services.product_service.create_product_category(db, category_in)
    assert category is not None
    assert category.name == name
    assert category.description == "Gadgets and devices"

def test_create_product_category_duplicate_name(db: Session):
    name = f"Books_{random_lower_string(3)}"
    # Create the first category
    category_in_first = schemas.ProductCategoryCreate(name=name)
    services.product_service.create_product_category(db, category_in_first)

    # Try to create another with the same name
    category_in_dup = schemas.ProductCategoryCreate(name=name)
    with pytest.raises(HTTPException) as exc_info:
        services.product_service.create_product_category(db, category_in_dup)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail # Check part of the error message

def test_get_product_category_service(db: Session):
    created_cat = create_random_product_category(db, "_get_cat")
    fetched_cat = services.product_service.get_product_category(db, created_cat.id)
    assert fetched_cat is not None
    assert fetched_cat.id == created_cat.id
    assert fetched_cat.name == created_cat.name

def test_get_all_product_categories_service(db: Session):
    create_random_product_category(db, "_get_all1")
    create_random_product_category(db, "_get_all2")
    categories = services.product_service.get_all_product_categories(db, limit=10)
    assert len(categories) >= 2

def test_update_product_category_service(db: Session):
    category = create_random_product_category(db, "_upd_cat")
    update_data = schemas.ProductCategoryUpdate(name=f"Updated {category.name}", description="New desc")
    updated_cat = services.product_service.update_product_category(db, category, update_data)
    assert updated_cat.name == update_data.name
    assert updated_cat.description == "New desc"

def test_delete_product_category_empty(db: Session):
    category = create_random_product_category(db, "_del_empty_cat")
    deleted_cat = services.product_service.delete_product_category(db, category.id)
    assert deleted_cat is not None
    assert services.product_service.get_product_category(db, category.id) is None

def test_delete_product_category_not_empty(db: Session):
    category = create_random_product_category(db, "_del_ne_cat")
    create_random_product(db, category_id=category.id, name_suffix="_del_ne_prod")
    with pytest.raises(HTTPException) as exc_info:
        services.product_service.delete_product_category(db, category.id)
    assert exc_info.value.status_code == 400
    assert "contains products" in exc_info.value.detail

# Product Service Tests
def test_create_product_service(db: Session):
    category = create_random_product_category(db, "_prod_svc_cat")
    product_in = schemas.ProductCreate(
        name="Test Laptop X1", category_id=category.id, price=Decimal("1250.75"), sku="LPTPX1123"
    )
    product = services.product_service.create_product(db, product_in)
    assert product is not None
    assert product.name == "Test Laptop X1"
    assert product.sku == "LPTPX1123"
    assert product.category_id == category.id
    assert product.price == Decimal("1250.75")

def test_create_product_invalid_category(db: Session):
    product_in = schemas.ProductCreate(
        name="Test Widget", category_id=99999, price=Decimal("10.00") # Non-existent category
    )
    with pytest.raises(HTTPException) as exc_info:
        services.product_service.create_product(db, product_in)
    assert exc_info.value.status_code == 404
    assert "category with ID 99999 not found" in exc_info.value.detail

def test_create_product_duplicate_sku(db: Session):
    category = create_random_product_category(db, "_prod_dup_sku_cat")
    sku_val = f"DUPSKU{random_lower_string(4)}"
    services.product_service.create_product(db, schemas.ProductCreate(name="Prod A", category_id=category.id, price=Decimal("1.00"), sku=sku_val))

    product_in_dup = schemas.ProductCreate(name="Prod B", category_id=category.id, price=Decimal("2.00"), sku=sku_val)
    with pytest.raises(HTTPException) as exc_info:
        services.product_service.create_product(db, product_in_dup)
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail


def test_get_product_service(db: Session):
    created_prod = create_random_product(db, name_suffix="_get_prod")
    fetched_prod = services.product_service.get_product(db, created_prod.id)
    assert fetched_prod is not None
    assert fetched_prod.id == created_prod.id
    assert fetched_prod.category is not None # Check eager loading

def test_get_products_service_filtering(db: Session):
    cat1 = create_random_product_category(db, "_filter_cat1")
    cat2 = create_random_product_category(db, "_filter_cat2")

    create_random_product(db, category_id=cat1.id, name_suffix="_p1_cat1", is_active=True, taxable=True)
    create_random_product(db, category_id=cat2.id, name_suffix="_p2_cat2", is_active=False, taxable=True)
    create_random_product(db, category_id=cat1.id, name_suffix="_p3_cat1", is_active=True, taxable=False)

    assert len(services.product_service.get_products(db, category_id=cat1.id)) >= 2
    assert len(services.product_service.get_products(db, is_active=False)) >= 1
    assert len(services.product_service.get_products(db, taxable=False)) >= 1
    assert len(services.product_service.get_products(db, name="P1_CAT1")) >= 1 # Assuming name_suffix is part of name

def test_update_product_service(db: Session):
    product = create_random_product(db, name_suffix="_upd_prod")
    cat_new = create_random_product_category(db, "_upd_prod_newcat")
    new_name = f"Updated {product.name}"
    new_price = product.price + Decimal("10.00")
    update_data = schemas.ProductUpdate(name=new_name, price=new_price, category_id=cat_new.id, is_active=False)

    updated_prod = services.product_service.update_product(db, product, update_data)
    assert updated_prod.name == new_name
    assert updated_prod.price == new_price
    assert updated_prod.category_id == cat_new.id
    assert updated_prod.is_active is False

def test_delete_product_service(db: Session):
    product = create_random_product(db, name_suffix="_del_prod")
    prod_id = product.id
    deleted_prod = services.product_service.delete_product(db, prod_id)
    assert deleted_prod is not None
    assert deleted_prod.id == prod_id
    assert services.product_service.get_product(db, prod_id) is None


def test_calculate_product_price_with_tax(db: Session):
    # Mock product model instance for this test, as service doesn't require DB hit
    # This test is more of a pure utility function test
    product_taxable = models.Product(id=1, name="Taxable Item", price=Decimal("100.00"), taxable=True, category_id=1)
    price_details_taxable = services.product_service.calculate_product_price_with_tax(product_taxable, quantity=2)
    assert price_details_taxable["subtotal"] == Decimal("200.00")
    assert price_details_taxable["tax_amount"] == Decimal("36.00") # 200 * 0.18
    assert price_details_taxable["total_with_tax"] == Decimal("236.00")

    product_nontaxable = models.Product(id=2, name="Non-Taxable Item", price=Decimal("50.00"), taxable=False, category_id=1)
    price_details_nontaxable = services.product_service.calculate_product_price_with_tax(product_nontaxable, quantity=3)
    assert price_details_nontaxable["subtotal"] == Decimal("150.00")
    assert price_details_nontaxable["tax_amount"] == Decimal("0.00")
    assert price_details_nontaxable["total_with_tax"] == Decimal("150.00")

def test_get_product_price_details_service(db: Session):
    product = create_random_product(db, price=Decimal("10.00"), taxable=False, name_suffix="_getpricedet")
    details = services.product_service.get_product_price_details(db, product.id, quantity=5)
    assert details is not None
    assert details["product_id"] == product.id
    assert details["total_with_tax"] == Decimal("50.00") # 10 * 5, no tax

    with pytest.raises(HTTPException) as exc_info: # Test non-existent product
        services.product_service.get_product_price_details(db, 99999, 1)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info_qty: # Test invalid quantity
        services.product_service.get_product_price_details(db, product.id, 0)
    assert exc_info_qty.value.status_code == 400
