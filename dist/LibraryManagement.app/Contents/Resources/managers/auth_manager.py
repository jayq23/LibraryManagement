"""Authentication, sessions, and role-based access."""

import hashlib
import hmac

from config import DB_URL
from database.db_manager import DatabaseManager
from models.user import User


class AuthManager:
	def __init__(self, database: DatabaseManager | None = None):
		self.database = database or DatabaseManager(DB_URL)

	@staticmethod
	def _hash(password: str) -> str:
		return hashlib.sha256(password.encode("utf-8")).hexdigest()

	def authenticate(self, username: str, password: str) -> User | None:
		record = self.database.fetch_one(
			"SELECT username, role, password_hash FROM users WHERE username = :username",
			{"username": username.strip()},
		)
		if not record or not hmac.compare_digest(record["password_hash"], self._hash(password)):
			return None
		return User(record["username"], record["role"])

	def create_user(self, username: str, password: str, role: str = "librarian") -> User:
		if not username.strip() or not password:
			raise ValueError("Username and password are required")
		self.database.execute(
			"INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role)",
			{"username": username.strip(), "password_hash": self._hash(password), "role": role},
		)
		return User(username.strip(), role)
