# Overdue fine calculation business logic with Philippine Standard Time (PST) support.

from datetime import datetime, date
from decimal import Decimal
from zoneinfo import ZoneInfo  # Direct import lang dahil built-in na 'to sa Python 3.13

from database.db_manager import DatabaseManager
from database.shared import get_database


class FineManager:
    PH_TZ = ZoneInfo("Asia/Manila")

    # Initialize the component.
    def __init__(self, database: DatabaseManager | None = None, daily_rate: Decimal = Decimal("10.00")):
        self.database = database or get_database()
        self.daily_rate = daily_rate  # Flat ₱10 per day late fee

    @classmethod
    # Retrieve get ph today.
    def get_ph_today(cls) -> date:
        return datetime.now(cls.PH_TZ).date()

    @classmethod
    # Retrieve get ph now.
    def get_ph_now(cls, format_str: str = "%b %d, %Y %I:%M %p") -> str:
        return datetime.now(cls.PH_TZ).strftime(format_str)

    # Calculate calculate.
    def calculate(self, due_date: date, as_of: date | None = None) -> Decimal:
        current_date = as_of or self.get_ph_today()
        overdue_days = max((current_date - due_date).days, 0)
        return self.daily_rate * overdue_days

    # Calculate calculate for book.
    def calculate_for_book(self, price: Decimal, due_date: date, as_of: date | None = None) -> Decimal:
        return self.calculate(due_date, as_of).quantize(Decimal("0.01"))

    # Sync fines for every overdue loan with one SQL statement instead of one query per loan.
    def sync_overdue_fines(self) -> None:
        self.database.execute(
            "INSERT INTO fines (member_id, loan_id, amount, reason) "
            "SELECT loans.member_id, loans.id, "
            "ROUND(CAST(:rate AS NUMERIC) * (CAST(:ph_today AS DATE) - loans.due_date), 2), 'Overdue item' "
            "FROM loans WHERE loans.due_date < CAST(:ph_today AS DATE) AND loans.returned_on IS NULL "
            "ON CONFLICT (loan_id) WHERE loan_id IS NOT NULL DO UPDATE SET amount = EXCLUDED.amount",
            {"ph_today": self.get_ph_today(), "rate": self.daily_rate},
        )

    # List list unpaid.
    def list_unpaid(self) -> list[dict]:
        self.sync_overdue_fines()
        return self.database.fetch_all(
            "SELECT fines.*, members.name FROM fines JOIN members USING (member_id) "
            "WHERE paid = FALSE ORDER BY created_at DESC"
        )

    # Add add for loan.
    def add_for_loan(self, loan_id: int, member_id: str, due_date: date, price: Decimal, as_of: date | None = None) -> Decimal:
        amount = self.calculate_for_book(price, due_date, as_of)
        if amount > 0:
            self.database.execute(
                "INSERT INTO fines (member_id, loan_id, amount, reason) VALUES (:member_id, :loan_id, :amount, :reason)",
                {
                    "member_id": member_id,
                    "loan_id": loan_id,
                    "amount": amount,
                    "reason": f"Overdue item (Recorded on {self.get_ph_now()})"
                },
            )
        return amount

    # Handle pay.
    def pay(self, fine_id: int) -> None:
        result = self.database.execute(
            "UPDATE fines SET paid = TRUE WHERE id = :fine_id",
            {"fine_id": fine_id}
        )
        if result.rowcount == 0:
            raise ValueError("Fine not found")
