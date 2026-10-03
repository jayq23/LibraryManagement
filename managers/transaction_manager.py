"""Borrow, return, reservation, and due-date business logic."""

from datetime import date, timedelta

from sqlalchemy import text

from config import DB_URL
from database.db_manager import DatabaseManager


class TransactionManager:
    def __init__(self, database: DatabaseManager | None = None, loan_days: int = 14, fine_per_day: float = 10.0):
        self.database = database or DatabaseManager(DB_URL)
        self.loan_days = loan_days
        self.fine_per_day = fine_per_day  # ₱10 per day late, adjust as needed

    def borrow(self, member_id: str, isbn: str, due_date: date | None = None) -> int:
        due = due_date or date.today() + timedelta(days=self.loan_days)
        if due < date.today():
            raise ValueError("Due date cannot be in the past")
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

    def return_book(self, loan_id: int) -> dict:
        """Marks a loan as returned. If the book is returned past its due date,
        computes a late fine (₱ per day late) and inserts an unpaid fine record.
        Returns a dict with days_late and fine_amount so the GUI can show a receipt."""
        with self.database.engine.begin() as connection:
            loan = connection.execute(
                text("SELECT isbn, due_date, member_id, returned_on FROM loans WHERE id = :loan_id FOR UPDATE"),
                {"loan_id": loan_id},
            ).mappings().first()
            if not loan:
                raise ValueError("Loan not found")
            if loan["returned_on"] is not None:
                raise ValueError("Loan is already returned")

            connection.execute(text("UPDATE loans SET returned_on = CURRENT_DATE WHERE id = :loan_id"), {"loan_id": loan_id})
            connection.execute(text("UPDATE books SET available_copies = available_copies + 1 WHERE isbn = :isbn"), {"isbn": loan["isbn"]})

            days_late = (date.today() - loan["due_date"]).days
            fine_amount = 0.0

            if days_late > 0:
                fine_amount = round(days_late * self.fine_per_day, 2)
                connection.execute(
                    text(
                        "INSERT INTO fines (member_id, loan_id, amount, reason, paid, created_at) "
                        "VALUES (:member_id, :loan_id, :amount, :reason, FALSE, CURRENT_TIMESTAMP) "
                        "ON CONFLICT (loan_id) WHERE loan_id IS NOT NULL DO UPDATE SET "
                        "amount = EXCLUDED.amount, reason = EXCLUDED.reason, paid = FALSE"
                    ),
                    {
                        "member_id": loan["member_id"],
                        "loan_id": loan_id,
                        "amount": fine_amount,
                        "reason": "Overdue item",
                    },
                )

            return {
                "member_id": loan["member_id"],
                "isbn": loan["isbn"],
                "days_late": days_late,
                "fine_amount": fine_amount,
            }

    def active_loans(self) -> list[dict]:
        return self.database.fetch_all(
            "SELECT loans.*, members.name, books.title FROM loans JOIN members USING (member_id) JOIN books USING (isbn) "
            "WHERE returned_on IS NULL ORDER BY due_date"
        )

    def reserve(self, member_id: str, isbn: str) -> int:
        with self.database.engine.begin() as connection:
            member = connection.execute(
                text("SELECT active FROM members WHERE member_id = :member_id FOR UPDATE"),
                {"member_id": member_id},
            ).mappings().first()
            if not member or not member["active"]:
                raise ValueError("Active member not found")

            book = connection.execute(
                text("SELECT isbn FROM books WHERE isbn = :isbn FOR UPDATE"),
                {"isbn": isbn},
            ).mappings().first()
            if not book:
                raise ValueError("Book not found")

            existing = connection.execute(
                text(
                    "SELECT id FROM reservations "
                    "WHERE member_id = :member_id AND isbn = :isbn AND status = 'active' "
                    "FOR UPDATE"
                ),
                {"member_id": member_id, "isbn": isbn},
            ).first()
            if existing:
                raise ValueError("Member already has an active reservation for this book")

            result = connection.execute(
                text("INSERT INTO reservations (member_id, isbn) VALUES (:member_id, :isbn) RETURNING id"),
                {"member_id": member_id, "isbn": isbn},
            )
            return int(result.scalar_one())

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
        result = self.database.execute(
            "UPDATE reservations SET status = 'cancelled' WHERE id = :reservation_id AND status = 'active'",
            {"reservation_id": reservation_id},
        )
        if result.rowcount == 0:
            raise ValueError("Active reservation not found")

    def collect_reservation(self, reservation_id: int) -> int:
        with self.database.engine.begin() as connection:
            reservation = connection.execute(
                text(
                    "SELECT member_id, isbn FROM reservations "
                    "WHERE id = :reservation_id AND status = 'active' FOR UPDATE"
                ),
                {"reservation_id": reservation_id},
            ).mappings().first()
            if not reservation:
                raise ValueError("Active reservation not found")

            member = connection.execute(
                text("SELECT active FROM members WHERE member_id = :member_id FOR UPDATE"),
                {"member_id": reservation["member_id"]},
            ).mappings().first()
            if not member or not member["active"]:
                raise ValueError("Active member not found")

            book = connection.execute(
                text("SELECT available_copies FROM books WHERE isbn = :isbn FOR UPDATE"),
                {"isbn": reservation["isbn"]},
            ).mappings().first()
            if not book:
                raise ValueError("Book not found")
            if book["available_copies"] < 1:
                raise ValueError("Book is not available")

            due_date = date.today() + timedelta(days=self.loan_days)
            loan = connection.execute(
                text(
                    "INSERT INTO loans (member_id, isbn, due_date) "
                    "VALUES (:member_id, :isbn, :due_date) RETURNING id"
                ),
                {
                    "member_id": reservation["member_id"],
                    "isbn": reservation["isbn"],
                    "due_date": due_date,
                },
            )
            connection.execute(
                text("UPDATE books SET available_copies = available_copies - 1 WHERE isbn = :isbn"),
                {"isbn": reservation["isbn"]},
            )
            connection.execute(
                text("UPDATE reservations SET status = 'collected' WHERE id = :reservation_id"),
                {"reservation_id": reservation_id},
            )
            return int(loan.scalar_one())

    def unpaid_fines(self) -> list[dict]:
        """Returns all unpaid fine records with member and book info, for a Fines view or receipt lookup."""
        return self.database.fetch_all(
            "SELECT fines.*, members.name, books.title FROM fines "
            "JOIN members USING (member_id) "
            "JOIN loans ON fines.loan_id = loans.id "
            "JOIN books ON loans.isbn = books.isbn "
            "WHERE fines.paid = FALSE ORDER BY fines.created_at DESC"
        )

    def pay_fine(self, fine_id: int) -> None:
        result = self.database.execute(
            "UPDATE fines SET paid = TRUE WHERE id = :fine_id",
            {"fine_id": fine_id},
        )
        if result.rowcount == 0:
            raise ValueError("Fine not found")

    def pay_fines_for_member(self, member_id: str, amount) -> int:
        with self.database.engine.begin() as connection:
            fines = connection.execute(
                text(
                    "SELECT id, amount FROM fines "
                    "WHERE member_id = :member_id AND paid = FALSE "
                    "ORDER BY created_at, id FOR UPDATE"
                ),
                {"member_id": member_id},
            ).mappings().all()
            if not fines:
                raise ValueError("No unpaid fines found for member")

            total = sum((f["amount"] for f in fines), 0)
            if amount < total:
                raise ValueError(f"Payment is less than the outstanding balance of {total}")

            connection.execute(
                text("UPDATE fines SET paid = TRUE WHERE member_id = :member_id AND paid = FALSE"),
                {"member_id": member_id},
            )
            return len(fines)