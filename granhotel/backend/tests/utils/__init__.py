# This file makes 'utils' a Python package within tests.
from .common import random_lower_string, random_digits, random_email #noqa

# Assuming other util files and their key functions might exist:
try:
    from .user import create_user_in_db #noqa
except ImportError: # pragma: no cover
    pass # pragma: no cover

try:
    from .room import create_random_room #noqa
except ImportError: # pragma: no cover
    pass # pragma: no cover

try:
    from .guest import create_random_guest #noqa
except ImportError: # pragma: no cover
    pass # pragma: no cover

try:
    from .product import create_random_product_category, create_random_product #noqa
except ImportError: # pragma: no cover
    pass # pragma: no cover

try:
    from .reservation import create_random_reservation_data, create_random_reservation #noqa
except ImportError: # pragma: no cover
    pass # pragma: no cover

from .inventory import ( #noqa
    create_random_supplier,
    ensure_inventory_item_exists,
    create_random_po_items_data,
    create_random_purchase_order
)
