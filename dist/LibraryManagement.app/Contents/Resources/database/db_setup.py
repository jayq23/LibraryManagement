"""PostgreSQL schema creation entry point."""

from config import DB_URL
from database.db_manager import DatabaseManager


SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS users (
        username VARCHAR(100) PRIMARY KEY,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(30) NOT NULL DEFAULT 'librarian',
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS members (
        member_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(150) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS books (
        isbn VARCHAR(20) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(150) NOT NULL,
        publisher VARCHAR(150) NOT NULL DEFAULT '',
        shelf_location VARCHAR(100) NOT NULL DEFAULT '',
        category_id BIGINT,
        price NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (price >= 0),
        available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
        total_copies INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= available_copies)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS categories (
        id BIGSERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description VARCHAR(255) NOT NULL DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS loans (
        id BIGSERIAL PRIMARY KEY,
        member_id VARCHAR(50) NOT NULL REFERENCES members(member_id),
        isbn VARCHAR(20) NOT NULL REFERENCES books(isbn),
        borrowed_on DATE NOT NULL DEFAULT CURRENT_DATE,
        due_date DATE NOT NULL,
        returned_on DATE,
        CHECK (returned_on IS NULL OR returned_on >= borrowed_on)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reservations (
        id BIGSERIAL PRIMARY KEY,
        member_id VARCHAR(50) NOT NULL REFERENCES members(member_id),
        isbn VARCHAR(20) NOT NULL REFERENCES books(isbn),
        created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) NOT NULL DEFAULT 'active'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fines (
        id BIGSERIAL PRIMARY KEY,
        member_id VARCHAR(50) NOT NULL REFERENCES members(member_id),
        loan_id BIGINT REFERENCES loans(id),
        amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
        reason VARCHAR(255) NOT NULL,
        paid BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
)

MIGRATIONS = (
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS publisher VARCHAR(150) NOT NULL DEFAULT ''",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS category_id BIGINT",
    "ALTER TABLE books ADD COLUMN IF NOT EXISTS price NUMERIC(10, 2) NOT NULL DEFAULT 0",
    "CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_one_fine_per_loan ON fines(loan_id) WHERE loan_id IS NOT NULL",
)


def create_schema(database_url: str = DB_URL) -> None:
    """Create all application tables if they do not already exist."""
    database = DatabaseManager(database_url)
    try:
        for statement in SCHEMA:
            database.execute(statement)
        for statement in MIGRATIONS:
            database.execute(statement)
    finally:
        database.close()


if __name__ == "__main__":
    create_schema()
