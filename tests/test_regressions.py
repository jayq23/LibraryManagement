"""Regression tests for corrected business rules."""

from datetime import date, timedelta
from decimal import Decimal

from managers.auth_manager import AuthManager
from managers.fine_manager import FineManager
from managers.report_manager import ReportManager
from models.invoice import Invoice


class QueryCapture:
    def __init__(self):
        self.query = ""

    def fetch_all(self, query, parameters=None):
        self.query = query
        return []


def test_password_hash_is_salted_and_verifiable():
    first = AuthManager._hash("secret")
    second = AuthManager._hash("secret")

    assert first != second
    assert AuthManager._verify(first, "secret") == (True, False)
    assert AuthManager._verify(first, "wrong") == (False, False)


def test_legacy_sha256_hash_is_supported_for_upgrade():
    import hashlib

    legacy = hashlib.sha256(b"secret").hexdigest()

    assert AuthManager._verify(legacy, "secret") == (True, True)
    assert AuthManager._verify(legacy, "wrong") == (False, True)


def test_fine_manager_uses_flat_daily_rate():
    manager = FineManager(database=object())
    due_date = date(2026, 9, 28)

    assert manager.calculate(due_date, as_of=date(2026, 10, 1)) == Decimal("30.00")
    assert manager.calculate_for_book(Decimal("1000.00"), due_date, as_of=date(2026, 10, 1)) == Decimal("30.00")
    assert manager.calculate(due_date + timedelta(days=1), as_of=date(2026, 10, 1)) == Decimal("20.00")


def test_monthly_activity_aggregates_before_joining():
    database = QueryCapture()
    ReportManager(database=database).monthly_activity()

    assert "loan_counts AS" in database.query
    assert "fine_totals AS" in database.query
    assert "LEFT JOIN loan_counts" in database.query
    assert "LEFT JOIN fine_totals" in database.query
    assert "LEFT JOIN loans ON" not in database.query
    assert "LEFT JOIN fines ON" not in database.query


def test_invoice_formats_amount_as_pesos():
    invoice = Invoice("TEST-00001", "M001", Decimal("12.50"))

    assert invoice.get_formatted_amount() == "₱12.50"
    assert invoice.get_status_label() == "UNPAID"
