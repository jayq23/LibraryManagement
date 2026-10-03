"""Shared receipt helpers for the reservation and borrow panels."""

from decimal import Decimal, InvalidOperation

from managers.book_manager import BookManager
from models.invoice import Invoice
from utils.receipt_modal import ReceiptModal


def get_book_price(isbn: str) -> Decimal:
    """Returns the book's price, or 0.00 if the book is missing or the price is empty/invalid."""
    for book in BookManager().list_books():
        if book["isbn"] == isbn:
            try:
                return Decimal(str(book.get("price") or "0.00"))
            except InvalidOperation:
                return Decimal("0.00")
    return Decimal("0.00")


def show_receipt(master, title: str, prefix: str, number: int, member_id: str,
                 amount: Decimal, paid: bool = True) -> None:
    """Builds an Invoice and opens the receipt modal.

    Example: show_receipt(self, "Book Reservation Slip", "RES", reservation_id, member_id, price)
    """
    invoice = Invoice(
        invoice_id=f"{prefix}-{int(number):05d}",
        member_id=member_id,
        amount=amount,
        paid=paid,
    )
    ReceiptModal(master=master, transaction_title=title, invoice=invoice)