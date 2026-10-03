"""Development data insertion entry point."""

import hashlib
from datetime import date, timedelta

from config import DB_URL
from database.db_manager import DatabaseManager
from database.db_setup import create_schema


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def seed(database_url: str = DB_URL) -> None:
    """Create the schema and insert safe, repeatable development records."""
    create_schema(database_url)
    database = DatabaseManager(database_url)
    try:
        database.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role) "
            "ON CONFLICT (username) DO NOTHING",
            {"username": "admin", "password_hash": _hash_password("admin"), "role": "admin"},
        )
        for category in (("Software", "Programming and software development"), ("Data", "Data systems and databases"), ("Design", "Design and architecture")):
            database.execute(
                "INSERT INTO categories (name, description) VALUES (:name, :description) ON CONFLICT (name) DO NOTHING",
                {"name": category[0], "description": category[1]},
            )
        members = (
            ("M001", "Demo Member", "member@example.com"),
            ("M002", "Ava Johnson", "ava.johnson@example.com"),
            ("M003", "Noah Williams", "noah.williams@example.com"),
            ("M004", "Mia Chen", "mia.chen@example.com"),
        )
        for member in members:
            database.execute(
                "INSERT INTO members (member_id, name, email) VALUES (:member_id, :name, :email) "
                "ON CONFLICT (member_id) DO NOTHING",
                {"member_id": member[0], "name": member[1], "email": member[2]},
            )
        books = (
            ("9780132350884", "Clean Code", "Robert C. Martin", "A-01", 3, 45.00),
            ("9781491950357", "Designing Data-Intensive Applications", "Martin Kleppmann", "B-02", 2, 55.00),
            ("9780262046305", "Artificial Intelligence: A Modern Approach", "Stuart Russell", "C-01", 2, 70.00),
            ("9780596007126", "Head First Design Patterns", "Eric Freeman", "A-03", 2, 40.00),
            ("9780134685991", "Effective Java", "Joshua Bloch", "A-04", 2, 50.00),
            ("9781492078005", "Designing Web APIs", "Brenda Jin", "D-01", 1, 35.00),
        )
        for book in books:
            database.execute(
                "INSERT INTO books (isbn, title, author, shelf_location, available_copies, total_copies) "
                "VALUES (:isbn, :title, :author, :shelf, :copies, :copies) "
                "ON CONFLICT (isbn) DO NOTHING",
                {"isbn": book[0], "title": book[1], "author": book[2], "shelf": book[3], "copies": book[4], "price": book[5]},
            )
            database.execute(
                "UPDATE books SET total_copies = :copies, available_copies = GREATEST(:copies - "
                "(SELECT COUNT(*) FROM loans WHERE loans.isbn = books.isbn AND returned_on IS NULL), 0) "
                "WHERE isbn = :isbn",
                {"isbn": book[0], "copies": book[4]},
            )
            database.execute("UPDATE books SET price = :price WHERE isbn = :isbn", {"isbn": book[0], "price": book[5]})
        database.execute("UPDATE books SET category_id = (SELECT id FROM categories WHERE name = 'Software') WHERE isbn IN ('9780132350884', '9780596007126', '9780134685991')")
        database.execute("UPDATE books SET category_id = (SELECT id FROM categories WHERE name = 'Data') WHERE isbn IN ('9781491950357', '9781492078005')")
        database.execute("UPDATE books SET category_id = (SELECT id FROM categories WHERE name = 'Design') WHERE isbn = '9780262046305'")
        first_loan = database.fetch_one(
            "INSERT INTO loans (member_id, isbn, borrowed_on, due_date) "
            "SELECT 'M002', '9780132350884', CURRENT_DATE - 3, CURRENT_DATE + 11 "
            "WHERE NOT EXISTS (SELECT 1 FROM loans WHERE member_id = 'M002' AND isbn = '9780132350884' AND returned_on IS NULL) "
            "RETURNING id"
        )
        overdue_loan = database.fetch_one(
            "INSERT INTO loans (member_id, isbn, borrowed_on, due_date) "
            "SELECT 'M003', '9781491950357', CURRENT_DATE - 21, CURRENT_DATE - 7 "
            "WHERE NOT EXISTS (SELECT 1 FROM loans WHERE member_id = 'M003' AND isbn = '9781491950357' AND returned_on IS NULL) "
            "RETURNING id"
        )
        database.execute(
            "UPDATE books SET available_copies = GREATEST(total_copies - "
            "(SELECT COUNT(*) FROM loans WHERE loans.isbn = books.isbn AND returned_on IS NULL), 0) "
            "WHERE isbn IN (:clean_code, :data_apps)",
            {"clean_code": "9780132350884", "data_apps": "9781491950357"},
        )
        database.execute(
            "INSERT INTO reservations (member_id, isbn) SELECT 'M004', '9780134685991' "
            "WHERE NOT EXISTS (SELECT 1 FROM reservations WHERE member_id = 'M004' AND isbn = '9780134685991' AND status = 'active')"
        )
        database.execute(
            "INSERT INTO fines (member_id, loan_id, amount, reason) "
            "SELECT 'M003', id, 3.50, 'Overdue item' FROM loans "
            "WHERE member_id = 'M003' AND isbn = '9781491950357' AND returned_on IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM fines WHERE member_id = 'M003' AND reason = 'Overdue item')"
        )
    finally:
        database.close()


if __name__ == "__main__":
    seed()
