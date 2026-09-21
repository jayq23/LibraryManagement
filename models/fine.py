"""Fine and penalty models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Fine:
    member_id: str
    amount: Decimal
    reason: str = "Overdue item"
