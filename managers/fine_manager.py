"""Overdue fine calculation business logic."""

from datetime import date
from decimal import Decimal

from config import DB_URL
from database.db_manager import DatabaseManager


class FineManager:
	def __init__(self, database: DatabaseManager | None = None, daily_rate: Decimal = Decimal("0.01")):
		self.database = database or DatabaseManager(DB_URL)
		self.daily_rate = daily_rate

	def calculate(self, due_date: date, as_of: date | None = None) -> Decimal:
		overdue_days = max(((as_of or date.today()) - due_date).days, 0)
		return self.daily_rate * overdue_days

	def calculate_for_book(self, price: Decimal, due_date: date, as_of: date | None = None) -> Decimal:
		"""Charge one percent of the book price for each overdue day."""
		return (price * self.daily_rate * max(((as_of or date.today()) - due_date).days, 0)).quantize(Decimal("0.01"))

	def sync_overdue_fines(self) -> None:
		loans = self.database.fetch_all(
			"SELECT loans.id, loans.member_id, loans.due_date, books.price FROM loans "
			"JOIN books USING (isbn) WHERE loans.due_date < CURRENT_DATE"
		)
		for loan in loans:
			amount = self.calculate_for_book(Decimal(str(loan["price"])), loan["due_date"])
			if amount:
				self.database.execute(
					"INSERT INTO fines (member_id, loan_id, amount, reason) VALUES (:member_id, :loan_id, :amount, :reason) "
					"ON CONFLICT (loan_id) WHERE loan_id IS NOT NULL DO UPDATE SET amount = EXCLUDED.amount",
					{"member_id": loan["member_id"], "loan_id": loan["id"], "amount": amount, "reason": "Overdue interest (1% daily)"},
				)

	def list_unpaid(self) -> list[dict]:
		self.sync_overdue_fines()
		return self.database.fetch_all(
			"SELECT fines.*, members.name FROM fines JOIN members USING (member_id) "
			"WHERE paid = FALSE ORDER BY created_at"
		)

	def add_for_loan(self, loan_id: int, member_id: str, due_date: date, as_of: date | None = None) -> Decimal:
		amount = self.calculate(due_date, as_of)
		if amount:
			self.database.execute(
				"INSERT INTO fines (member_id, loan_id, amount, reason) VALUES (:member_id, :loan_id, :amount, :reason)",
				{"member_id": member_id, "loan_id": loan_id, "amount": amount, "reason": "Overdue item"},
			)
		return amount

	def pay(self, fine_id: int) -> None:
		self.database.execute("UPDATE fines SET paid = TRUE WHERE id = :fine_id", {"fine_id": fine_id})
