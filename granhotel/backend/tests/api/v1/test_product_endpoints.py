from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal # For comparing price in response

from app.core.config import settings
from app.schemas import ProductCategoryCreate, ProductCreate # UserRole for auth if needed
from app.models.user import UserRole # For creating users with specific roles
from tests.utils.user import create_user_in_db
from tests.utils.product import create_random_product_category, create_random_product, random_lower_string # Import random_lower_string
from tests.api.v1.test_users_endpoints import get_auth_headers # Reuse from user tests

API_V1_PROD_CATS_URL = f"{settings.API_V1_STR}/product-categories"
API_V1_PRODUCTS_URL = f"{settings.API_V1_STR}/products"

# ProductCategory API Tests
def test_create_product_category_api(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="_prodcat_admin")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role) # Use admin_user.id (UUID)

    cat_name = f"API Test Category {random_lower_string(3)}"
    cat_data = {"name": cat_name, "description": "Created via API"}
    response = client.post(f"{API_V1_PROD_CATS_URL}/", json=cat_data, headers=admin_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["name"] == cat_name
    assert "id" in content

def test_read_all_product_categories_api(client: TestClient, db: Session):
    user = create_user_in_db(db, suffix_for_email="_readcat_user")
    user_headers = get_auth_headers(user.id, user.role)
    create_random_product_category(db, "_api_rc1")
    create_random_product_category(db, "_api_rc2")
    response = client.get(f"{API_V1_PROD_CATS_URL}/", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 2

def test_read_single_product_category_api(client: TestClient, db: Session):
    user = create_user_in_db(db, suffix_for_email="_readonecat_user")
    user_headers = get_auth_headers(user.id, user.role)
    category = create_random_product_category(db, "_api_rsinglec")
    response = client.get(f"{API_V1_PROD_CATS_URL}/{category.id}", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["id"] == category.id
    assert content["name"] == category.name

def test_update_product_category_api(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, suffix_for_email="_updcat_mgr")
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    category = create_random_product_category(db, "_api_updcat")
    updated_name = f"Updated Category Name {random_lower_string(3)}"
    update_data = {"name": updated_name}
    response = client.put(f"{API_V1_PROD_CATS_URL}/{category.id}", json=update_data, headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["name"] == updated_name

def test_delete_product_category_api(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="_delcat_admin")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    category = create_random_product_category(db, "_api_delcat") # Empty category

    response = client.delete(f"{API_V1_PROD_CATS_URL}/{category.id}", headers=admin_headers)
    assert response.status_code == 200, response.text
    # Verify it's deleted
    get_response = client.get(f"{API_V1_PROD_CATS_URL}/{category.id}", headers=admin_headers)
    assert get_response.status_code == 404


# Product API Tests
def test_create_product_api(client: TestClient, db: Session):
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, suffix_for_email="_prod_mgr_crt")
    manager_headers = get_auth_headers(manager_user.id, manager_user.role)
    category = create_random_product_category(db, "_prod_api_cat_crt")

    prod_name = f"API Test Product {random_lower_string(3)}"
    # Pydantic schema for ProductCreate expects Decimal for price.
    # TestClient json encoder handles Decimal to float string conversion well.
    prod_data = {
        "name": prod_name, "price": "19.99", "category_id": category.id,
        "sku": f"API{random_lower_string(5).upper()}", "taxable": True, "is_active": True
    }
    response = client.post(f"{API_V1_PRODUCTS_URL}/", json=prod_data, headers=manager_headers)
    assert response.status_code == 201, response.text
    content = response.json()
    assert content["name"] == prod_name
    assert content["price"] == 19.99 # FastAPI/Pydantic converts Decimal to float in JSON
    assert content["category"]["id"] == category.id # Check nested category

def test_read_all_products_api_with_filter(client: TestClient, db: Session):
    user = create_user_in_db(db, suffix_for_email="_readprod_user")
    user_headers = get_auth_headers(user.id, user.role)
    category = create_random_product_category(db, "_api_filter_cat")
    create_random_product(db, category_id=category.id, name_suffix="_api_filter_p1")
    create_random_product(db, name_suffix="_api_filter_p2") # Different category

    response = client.get(f"{API_V1_PRODUCTS_URL}/?category_id={category.id}", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert isinstance(content, list)
    assert len(content) >= 1
    for prod in content:
        assert prod["category_id"] == category.id


def test_get_product_price_details_api(client: TestClient, db: Session):
    user = create_user_in_db(db, suffix_for_email="_price_det_user_api")
    user_headers = get_auth_headers(user.id, user.role)
    product = create_random_product(db, price=Decimal("100.00"), taxable=True, name_suffix="_pricedet_api")

    response = client.get(f"{API_V1_PRODUCTS_URL}/{product.id}/price-details?quantity=3", headers=user_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["product_id"] == product.id
    assert content["quantity"] == 3.0 # Service returns Decimal, FastAPI converts to float
    assert content["subtotal"] == 300.00
    # Using float comparison for tax due to potential precision nuances in JSON
    assert abs(Decimal(str(content["tax_amount"])) - Decimal("54.00")) < Decimal("0.001") # 300 * 0.18
    assert abs(Decimal(str(content["total_with_tax"])) - Decimal("354.00")) < Decimal("0.001")

def test_delete_product_api(client: TestClient, db: Session):
    admin_user = create_user_in_db(db, role=UserRole.ADMIN, suffix_for_email="_delprod_admin")
    admin_headers = get_auth_headers(admin_user.id, admin_user.role)
    product = create_random_product(db, name_suffix="_api_delprod")

    response = client.delete(f"{API_V1_PRODUCTS_URL}/{product.id}", headers=admin_headers)
    assert response.status_code == 200, response.text
    # Verify it's deleted
    get_response = client.get(f"{API_V1_PRODUCTS_URL}/{product.id}", headers=admin_headers)
    assert get_response.status_code == 404
