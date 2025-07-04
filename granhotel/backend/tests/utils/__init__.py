# This file makes 'utils' a Python package within tests.
from .common import random_lower_string, random_digits, random_email #noqa

# Assuming other util files and their key functions might exist:
# Using try-except for robustness, in case some util modules are not yet created or refactored.
try:
    from .user import create_user_in_db #noqa
except ImportError: # pragma: no cover
    pass

try:
    from .room import create_random_room #noqa
except ImportError: # pragma: no cover
    pass

try:
    from .guest import create_random_guest #noqa
except ImportError: # pragma: no cover
    pass

try:
    from .product import create_random_product_category, create_random_product #noqa
except ImportError: # pragma: no cover
    pass

try:
    from .reservation import create_random_reservation_data, create_random_reservation #noqa
except ImportError: # pragma: no cover
    pass

try:
    from .inventory import ( #noqa
        create_random_supplier,
        ensure_inventory_item_exists,
        create_random_po_items_data,
        create_random_purchase_order
    )
except ImportError: # pragma: no cover
    pass

try:
    from .housekeeping import ( #noqa
        create_random_housekeeper,
        create_random_housekeeping_log_data,
        create_random_housekeeping_log
    )
except ImportError: # pragma: no cover
    pass

try:
    from .pos import ( #noqa
        create_pos_sale_items_data_for_api,
        create_random_pos_sale
    )
except ImportError: # pragma: no cover
    pass

from .billing import ( #noqa
    create_random_folio_transaction_data,
    create_random_guest_folio,
    add_sample_transactions_to_folio
)
