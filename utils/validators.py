# Input validation helpers.

import re


# Validate an email address.
def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


# Validate an ISBN.
def is_valid_isbn(value: str) -> bool:
    normalized = value.replace("-", "").replace(" ", "")
    return len(normalized) in (10, 13) and normalized[:-1].isdigit()
