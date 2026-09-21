"""Fine payment and receipt model."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Invoice:
    invoice_id: str
    member_id: str
    amount: Decimal
    paid: bool = False
