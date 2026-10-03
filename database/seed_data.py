"""Database initialization entry point."""

import os

from config import DB_URL
from database.db_manager import DatabaseManager
from database.db_setup import create_schema
from managers.auth_manager import AuthManager


def seed(database_url: str = DB_URL) -> None:
    """Create the schema and ensure the administrator account exists."""
    create_schema(database_url)
    database = DatabaseManager(database_url)
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin").strip()
        existing_admin = database.fetch_one(
            "SELECT username FROM users WHERE username = :username",
            {"username": admin_username},
        )
        if existing_admin:
            return

        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            raise RuntimeError("Set ADMIN_PASSWORD in .env before creating the admin account")

        database.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role) "
            "ON CONFLICT (username) DO NOTHING",
            {
                "username": admin_username,
                "password_hash": AuthManager._hash(admin_password),
                "role": "admin",
            },
        )
    finally:
        database.close()


if __name__ == "__main__":
    seed()
