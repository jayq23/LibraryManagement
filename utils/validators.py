"""Input validation helpers."""

import re


def is_valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def is_valid_isbn(value: str) -> bool:
    normalized = value.replace("-", "").replace(" ", "")
    return len(normalized) in (10, 13) and normalized[:-1].isdigit()
