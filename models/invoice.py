# Fine payment and receipt model.

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Invoice:
    invoice_id: str
    member_id: str
    amount: Decimal
    paid: bool = False

    # Retrieve get formatted amount.
    def get_formatted_amount(self) -> str:
        return f"₱{self.amount:.2f}"

    # Retrieve get status label.
    def get_status_label(self) -> str:
        return "PAID" if self.paid else "UNPAID"