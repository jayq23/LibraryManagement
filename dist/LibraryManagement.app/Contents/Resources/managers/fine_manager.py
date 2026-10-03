"""Overdue fine calculation business logic with Philippine Standard Time (PST) support."""

from datetime import datetime, date
from decimal import Decimal
from zoneinfo import ZoneInfo  # Direct import lang dahil built-in na 'to sa Python 3.13

from config import DB_URL
from database.db_manager import DatabaseManager


class FineManager:
    PH_TZ = ZoneInfo("Asia/Manila")

    def __init__(self, database: DatabaseManager | None = None, daily_rate: Decimal = Decimal("0.01")):
        self.database = database or DatabaseManager(DB_URL)
        self.daily_rate = daily_rate  # 1% daily interest

    @classmethod
    def get_ph_today(cls) -> date:
        """Kukunin ang kasalukuyang petsa sa Philippine Timezone (UTC+8)."""
        return datetime.now(cls.PH_TZ).date()

    @classmethod
    def get_ph_now(cls, format_str: str = "%b %d, %Y %I:%M %p") -> str:
        """Kukunin ang kasalukuyang oras sa PH format (Halimbawa: 'Sep 25, 2026 11:00 AM')."""
        return datetime.now(cls.PH_TZ).strftime(format_str)

    def calculate(self, due_date: date, as_of: date | None = None) -> Decimal:
        """Kina-kalkula ang flat fine base sa PH date kung walang binigay na as_of date."""
        current_date = as_of or self.get_ph_today()
        overdue_days = max((current_date - due_date).days, 0)
        return self.daily_rate * overdue_days

    def calculate_for_book(self, price: Decimal, due_date: date, as_of: date | None = None) -> Decimal:
        """Kina-kalkula ang 1% daily fine base sa presyo ng libro at PH date."""
        current_date = as_of or self.get_ph_today()
        overdue_days = max((current_date - due_date).days, 0)
        return (price * self.daily_rate * overdue_days).quantize(Decimal("0.01"))

    def sync_overdue_fines(self) -> None:
        """I-a-update ang mga overdue fines gamit ang kasalukuyang petsa sa Pilipinas."""
        ph_today = self.get_ph_today()
        loans = self.database.fetch_all(
            "SELECT loans.id, loans.member_id, loans.due_date, books.price FROM loans "
            "JOIN books USING (isbn) WHERE loans.due_date < :ph_today AND loans.returned_on IS NULL",
            {"ph_today": ph_today}
        )
        for loan in loans:
            amount = self.calculate_for_book(Decimal(str(loan["price"])), loan["due_date"], as_of=ph_today)
            if amount > 0:
                self.database.execute(
                    "INSERT INTO fines (member_id, loan_id, amount, reason) VALUES (:member_id, :loan_id, :amount, :reason) "
                    "ON CONFLICT (loan_id) WHERE loan_id IS NOT NULL DO UPDATE SET amount = EXCLUDED.amount",
                    {
                        "member_id": loan["member_id"], 
                        "loan_id": loan["id"], 
                        "amount": amount, 
                        "reason": f"Overdue interest (1% daily as of {self.get_ph_now()})"
                    },
                )

    def list_unpaid(self) -> list[dict]:
        self.sync_overdue_fines()
        return self.database.fetch_all(
            "SELECT fines.*, members.name FROM fines JOIN members USING (member_id) "
            "WHERE paid = FALSE ORDER BY created_at DESC"
        )

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

    def pay(self, fine_id: int) -> None:
        self.database.execute(
            "UPDATE fines SET paid = TRUE WHERE id = :fine_id", 
            {"fine_id": fine_id}
        )