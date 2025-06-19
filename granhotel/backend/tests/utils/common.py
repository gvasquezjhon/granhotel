import random
import string

def random_lower_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def random_digits(length: int = 8) -> str:
    return "".join(random.choices(string.digits, k=length))

def random_email(prefix: str = "user") -> str:
    # Ensure the prefix itself doesn't make the local part too long if it's dynamic
    # For testing, simple concatenation is usually fine.
    return f"{prefix}_{random_lower_string(5)}@{random_lower_string(5)}.com"
