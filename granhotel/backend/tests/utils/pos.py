from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, timedelta, datetime
import random
import uuid

from app import models, schemas, services
from app.models.pos import PaymentMethod, POSSaleStatus
from app.models.user import UserRole
from tests.utils.user import create_user_in_db # Assumed to exist
from tests.utils.product import create_random_product # Assumed to exist
from tests.utils.guest import create_random_guest # Assumed to exist
from tests.utils.common import random_lower_string, random_digits # Assumed to exist
from tests.utils.inventory import ensure_inventory_item_exists # Assumed to exist


def create_pos_sale_items_data_for_api(db: Session, num_items: int = 1) -> List[Dict[str, Any]]:
    '''Generates a list of item data suitable for POSSaleCreate schema (for API JSON).'''
    items_data_api = []
    for i in range(num_items):
        product_suffix = f"_pos_item_api_{i}_{random_lower_string(3)}"
        product = create_random_product(db, name_suffix=product_suffix)

        initial_stock_qty = random.randint(20,50) + i*5
        ensure_inventory_item_exists(db, product_id=product.id, initial_quantity=initial_stock_qty)

        items_data_api.append({
            "product_id": product.id,
            "quantity": random.randint(1, min(3, initial_stock_qty))
        })
    return items_data_api


def create_random_pos_sale(
    db: Session,
    cashier_user_id: uuid.UUID,
    guest_id: Optional[uuid.UUID] = None,
    num_items: int = 1,
    payment_method: PaymentMethod = PaymentMethod.CASH,
    # status: POSSaleStatus = POSSaleStatus.COMPLETED # Service will set default status
    use_specific_product_id: Optional[int] = None # Allow specifying a product for targeted tests
) -> models.pos.POSSale:
    '''
    Creates a POS Sale with items using the pos_service.create_pos_sale.
    Ensures products have inventory before trying to sell them.
    '''
    sale_items_create_schema_list = []
    for i in range(num_items):
        if use_specific_product_id and i == 0: # Use specific product only for the first item if provided
            product_id_for_item = use_specific_product_id
            product = services.product_service.get_product(db, product_id_for_item)
            if not product:
                raise ValueError(f"Specific product ID {product_id_for_item} not found for POS sale util.")
        else:
            product_name_suffix = f"_possale_util_prod_{i}_{random_lower_string(3)}"
            product = create_random_product(db, name_suffix=product_name_suffix)
            product_id_for_item = product.id

        stock_quantity_to_ensure = random.randint(10, 20) + i*2
        # Ensure inventory item exists and has enough stock
        inv_item = ensure_inventory_item_exists(db, product_id_for_item, initial_quantity=stock_quantity_to_ensure)
        # If ensure_inventory_item_exists doesn't guarantee initial_quantity is the current stock (e.g. if item already existed)
        # then we might need to fetch current stock or rely on create_pos_sale to fail if stock is insufficient.
        # For simplicity, assume ensure_inventory_item_exists sets up enough stock or `create_random_product` does via its own inventory setup.
        # The create_pos_sale service itself checks for sufficient stock.

        quantity_to_sell = random.randint(1, min(2, inv_item.quantity_on_hand if inv_item.quantity_on_hand > 0 else 1) )
        # Ensure we don't try to sell more than available, or default to 1 if stock is 0 (to test failure path if needed)

        sale_items_create_schema_list.append(schemas.pos.POSSaleItemCreate(
            product_id=product_id_for_item,
            quantity=quantity_to_sell
        ))

    final_guest_id = guest_id
    if payment_method == PaymentMethod.ROOM_CHARGE and guest_id is None:
        guest_for_charge = create_random_guest(db, suffix="_pos_room_charge_util")
        final_guest_id = guest_for_charge.id


    pos_sale_create_schema = schemas.pos.POSSaleCreate(
        guest_id=final_guest_id,
        payment_method=payment_method,
        items=sale_items_create_schema_list,
        notes=f"Test POS Sale created by utility {random_lower_string(4)}"
    )

    return services.pos_service.create_pos_sale(
        db=db, sale_in=pos_sale_create_schema, cashier_user_id=cashier_user_id
    )
