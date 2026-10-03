"""Borrowing and reservation transaction models."""

from dataclasses import dataclass
from datetime import date


@dataclass
class BorrowTransaction:
    member_id: str
    isbn: str
    created_on: date


@dataclass
class Loan(BorrowTransaction):
    due_date: date | None = None


@dataclass
class Reservation(BorrowTransaction):
    position: int = 1
