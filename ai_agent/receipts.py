# Receipts requested by AI tools.

import threading
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ReceiptRequest:
    title: str
    prefix: str
    number: int
    member_id: str
    amount: Decimal


_lock = threading.Lock()
_pending: list[ReceiptRequest] = []


# Handle queue receipt.
def queue_receipt(title: str, prefix: str, number: int, member_id: str, amount: Decimal) -> None:
    with _lock:
        _pending.append(ReceiptRequest(title, prefix, int(number), member_id, amount))


# Handle pop receipts.
def pop_receipts() -> list[ReceiptRequest]:
    with _lock:
        items = list(_pending)
        _pending.clear()
    return items