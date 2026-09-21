"""Borrow, return, reservation, and due-date business logic."""

from datetime import date, timedelta

from sqlalchemy import text

from config import DB_URL
from database.db_manager import DatabaseManager


class TransactionManager:
	def __init__(self, database: DatabaseManager | None = None, loan_days: int = 14):
		self.database = database or DatabaseManager(DB_URL)
		self.loan_days = loan_days

	def borrow(self, member_id: str, isbn: str, due_date: date | None = None) -> int:
		due = due_date or date.today() + timedelta(days=self.loan_days)
		with self.database.engine.begin() as connection:
			member = connection.execute(text("SELECT active FROM members WHERE member_id = :member_id FOR UPDATE"), {"member_id": member_id}).mappings().first()
			book = connection.execute(text("SELECT available_copies FROM books WHERE isbn = :isbn FOR UPDATE"), {"isbn": isbn}).mappings().first()
			if not member or not member["active"]:
				raise ValueError("Active member not found")
			if not book:
				raise ValueError("Book not found")
			if book["available_copies"] < 1:
				raise ValueError("Book is not available")
			result = connection.execute(
				text("INSERT INTO loans (member_id, isbn, due_date) VALUES (:member_id, :isbn, :due_date) RETURNING id"),
				{"member_id": member_id, "isbn": isbn, "due_date": due},
			)
			connection.execute(text("UPDATE books SET available_copies = available_copies - 1 WHERE isbn = :isbn"), {"isbn": isbn})
			return int(result.scalar_one())

	def return_book(self, loan_id: int) -> None:
		with self.database.engine.begin() as connection:
			loan = connection.execute(text("SELECT isbn, returned_on FROM loans WHERE id = :loan_id FOR UPDATE"), {"loan_id": loan_id}).mappings().first()
			if not loan:
				raise ValueError("Loan not found")
			if loan["returned_on"] is not None:
				raise ValueError("Loan is already returned")
			connection.execute(text("UPDATE loans SET returned_on = CURRENT_DATE WHERE id = :loan_id"), {"loan_id": loan_id})
			connection.execute(text("UPDATE books SET available_copies = available_copies + 1 WHERE isbn = :isbn"), {"isbn": loan["isbn"]})

	def active_loans(self) -> list[dict]:
		return self.database.fetch_all(
			"SELECT loans.*, members.name, books.title FROM loans JOIN members USING (member_id) JOIN books USING (isbn) "
			"WHERE returned_on IS NULL ORDER BY due_date"
		)

	def reserve(self, member_id: str, isbn: str) -> int:
		record = self.database.fetch_one(
			"INSERT INTO reservations (member_id, isbn) VALUES (:member_id, :isbn) RETURNING id",
			{"member_id": member_id, "isbn": isbn},
		)
		return int(record["id"])

	def active_reservations(self) -> list[dict]:
		return self.list_reservations("active")

	def list_reservations(self, status: str | None = None) -> list[dict]:
		status_clause = "AND reservations.status = :status" if status else ""
		return self.database.fetch_all(
			"SELECT reservations.*, members.name, books.title, books.isbn "
			"FROM reservations JOIN members USING (member_id) JOIN books USING (isbn) "
			f"WHERE TRUE {status_clause} ORDER BY reservations.created_on DESC",
			{"status": status} if status else {},
		)

	def cancel_reservation(self, reservation_id: int) -> None:
		self.database.execute(
			"UPDATE reservations SET status = 'cancelled' WHERE id = :reservation_id AND status = 'active'",
			{"reservation_id": reservation_id},
		)

	def collect_reservation(self, reservation_id: int) -> None:
		self.database.execute(
			"UPDATE reservations SET status = 'collected' WHERE id = :reservation_id AND status = 'active'",
			{"reservation_id": reservation_id},
		)
