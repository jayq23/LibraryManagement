# Shared receipt helpers for the reservation and borrow panels.

from decimal import Decimal, InvalidOperation

from managers.book_manager import BookManager
from models.invoice import Invoice
from utils.receipt_modal import ReceiptModal


# Retrieve get book price (one small query instead of loading every book).
def get_book_price(isbn: str) -> Decimal:
    try:
        return Decimal(str(BookManager().get_price(isbn) or "0.00"))
    except InvalidOperation:
        return Decimal("0.00")


# Show show receipt.
def show_receipt(master, title: str, prefix: str, number: int, member_id: str,
                 amount: Decimal, paid: bool = True) -> None:
    invoice = Invoice(
        invoice_id=f"{prefix}-{int(number):05d}",
        member_id=member_id,
        amount=amount,
        paid=paid,
    )
    ReceiptModal(master=master, transaction_title=title, invoice=invoice)