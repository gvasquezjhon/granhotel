from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
import uuid

from app.core.config import settings
from app.models.user import UserRole
from app.models.reservations import ReservationStatus
from app.models.pos import PaymentMethod, POSSaleStatus
from app.models.billing import FolioTransactionType
from app import schemas, models, services # Import services for setup if needed
from tests.utils.user import create_user_in_db
from tests.utils.room import create_random_room
from tests.utils.guest import create_random_guest
from tests.utils.product import create_random_product, create_random_product_category
from tests.utils.inventory import ensure_inventory_item_exists
from tests.utils.reservations import create_random_reservation
from tests.utils.pos import create_random_pos_sale
from tests.utils.billing import create_random_guest_folio, add_sample_transactions_to_folio, create_random_folio_transaction_data
from app.core.security import create_access_token # For local get_auth_headers
from tests.utils.common import random_email, random_lower_string


API_V1_REPORTS_URL = f"{settings.API_V1_STR}/reports"

# Local get_auth_headers
def get_auth_headers(user_id: uuid.UUID, role: UserRole) -> dict:
    token_data = {"user_id": str(user_id), "role": role.value}
    token = create_access_token(data_to_encode=token_data)
    return {"Authorization": f"Bearer {token}"}

# Helper to create a manager for these tests
def get_manager_headers(db: Session) -> dict:
    manager_user = create_user_in_db(db, role=UserRole.MANAGER, email=random_email("_mgr_reports_api"))
    return get_auth_headers(manager_user.id, manager_user.role)

# --- Occupancy Report API Tests ---
def test_get_daily_occupancy_report_api(client: TestClient, db: Session):
    manager_headers = get_manager_headers(db)
    test_date = date.today() + timedelta(days=50)

    room = create_random_room(db, room_number_suffix="_repapi_docc")
    guest = create_random_guest(db, suffix="_repapi_docc")
    # Manually create reservation for specific date control
    reservation = models.Reservation(
        guest_id=guest.id, room_id=room.id,
        check_in_date=test_date - timedelta(days=1),
        check_out_date=test_date + timedelta(days=2),
        status=ReservationStatus.CHECKED_IN,
        # reservation_date, total_price would be set by service or defaults
    )
    db.add(reservation)
    db.commit()

    response = client.get(f"{API_V1_REPORTS_URL}/occupancy/daily?target_date={test_date.isoformat()}", headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    # Validate against the Pydantic schema (implicitly by FastAPI)
    # For explicit validation: schemas.reports.DailyOccupancyData(**content)
    assert content["date"] == test_date.isoformat()
    assert content["occupied_rooms"] >= 1

def test_get_period_occupancy_report_api(client: TestClient, db: Session):
    manager_headers = get_manager_headers(db)
    date_from = date.today() + timedelta(days=60)
    date_to = date_from + timedelta(days=2) # 3-day period

    room = create_random_room(db, room_number_suffix="_repapi_pocc")
    guest = create_random_guest(db, suffix="_repapi_pocc")
    reservation = models.Reservation(
        guest_id=guest.id, room_id=room.id,
        check_in_date=date_from,
        check_out_date=date_to + timedelta(days=1),
        status=ReservationStatus.CONFIRMED
    )
    db.add(reservation)
    db.commit()

    response = client.get(f"{API_V1_REPORTS_URL}/occupancy/period?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}", headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["date_from"] == date_from.isoformat()
    assert content["total_room_nights_occupied"] >= 3

# --- Sales Report API Tests ---
def test_get_total_sales_report_api(client: TestClient, db: Session):
    manager_headers = get_manager_headers(db)
    date_from = date.today() - timedelta(days=10)
    date_to = date.today() - timedelta(days=8)
    cashier = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_cash_repapi_sales"))

    sale1 = create_random_pos_sale(db, cashier_user_id=cashier.id, num_items=1)
    sale1.sale_date = datetime.combine(date_from, datetime.min.time().replace(hour=10), tzinfo=timezone.utc)
    db.add(sale1); db.commit(); db.refresh(sale1)

    response = client.get(f"{API_V1_REPORTS_URL}/sales/summary-by-period?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}", headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["total_sales_after_tax"] == str(sale1.total_amount_after_tax.quantize(Decimal("0.01")))
    assert content["number_of_sales"] == 1

    response_filtered = client.get(f"{API_V1_REPORTS_URL}/sales/summary-by-period?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}&payment_method={sale1.payment_method.value}", headers=manager_headers)
    assert response_filtered.status_code == 200
    content_filtered = response_filtered.json()
    assert content_filtered["total_sales_after_tax"] == str(sale1.total_amount_after_tax.quantize(Decimal("0.01")))


# --- Inventory Report API Tests ---
def test_get_inventory_summary_report_api(client: TestClient, db: Session):
    manager_headers = get_manager_headers(db)
    product = create_random_product(db, name_suffix="_invsum_api", price=Decimal("25.00"))
    ensure_inventory_item_exists(db, product.id, initial_quantity=10)

    response = client.get(f"{API_V1_REPORTS_URL}/inventory/summary", headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert "data" in content
    assert isinstance(content["data"], list)
    found_product = False
    for item in content["data"]:
        if item["product_id"] == product.id:
            assert item["quantity_on_hand"] == 10
            found_product = True
            break
    assert found_product, "Product created for inventory summary not found in report."


# --- Financial Report API Tests ---
def test_get_folio_financial_summary_report_api(client: TestClient, db: Session):
    manager_headers = get_manager_headers(db)
    date_from = date.today() - timedelta(days=15)
    date_to = date.today() - timedelta(days=13)
    creator = create_user_in_db(db, role=UserRole.ADMIN, email=random_email("_admin_repapi_folio"))
    guest = create_random_guest(db, suffix="_repapi_folio")

    folio = create_random_guest_folio(db, guest_id=guest.id) # creator_user_id not needed by util
    charge_amount = Decimal("120.00")
    payment_amount = Decimal("80.00")

    trans_charge = models.billing.FolioTransaction(
        guest_folio_id=folio.id, transaction_date=datetime.combine(date_from, datetime.min.time().replace(hour=10), tzinfo=timezone.utc),
        description="API Test Charge", charge_amount=charge_amount, transaction_type=FolioTransactionType.ROOM_CHARGE,
        created_by_user_id=creator.id
    )
    trans_payment = models.billing.FolioTransaction(
        guest_folio_id=folio.id, transaction_date=datetime.combine(date_to, datetime.min.time().replace(hour=11), tzinfo=timezone.utc),
        description="API Test Payment", payment_amount=payment_amount, transaction_type=FolioTransactionType.PAYMENT,
        created_by_user_id=creator.id
    )
    db.add_all([trans_charge, trans_payment]); db.commit()
    services.billing_service._recalculate_and_save_folio_totals(db, folio.id)

    response = client.get(f"{API_V1_REPORTS_URL}/financials/folio-summary?date_from={date_from.isoformat()}&date_to={date_to.isoformat()}", headers=manager_headers)
    assert response.status_code == 200, response.text
    content = response.json()
    assert content["total_charges_posted"] == str(charge_amount.quantize(Decimal("0.01")))
    assert content["total_payments_received"] == str(payment_amount.quantize(Decimal("0.01")))

def test_get_reports_api_permission_denied(client: TestClient, db: Session):
    receptionist_user = create_user_in_db(db, role=UserRole.RECEPTIONIST, email=random_email("_rec_reports_perm"))
    rec_headers = get_auth_headers(receptionist_user.id, receptionist_user.role)
    test_date_str = (date.today() - timedelta(days=1)).isoformat() # Use a consistent date string

    endpoints_to_check = [
        f"{API_V1_REPORTS_URL}/occupancy/daily?target_date={test_date_str}",
        f"{API_V1_REPORTS_URL}/sales/summary-by-period?date_from={test_date_str}&date_to={test_date_str}",
        f"{API_V1_REPORTS_URL}/inventory/summary",
    ]
    for endpoint_url in endpoints_to_check:
        response = client.get(endpoint_url, headers=rec_headers)
        assert response.status_code == 403, f"Endpoint {endpoint_url} did not return 403 for receptionist."
