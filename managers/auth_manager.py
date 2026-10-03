"""Authentication, sessions, and role-based access."""

import hashlib
import hmac
import secrets

from config import DB_URL
from database.db_manager import DatabaseManager
from models.user import User


class AuthManager:
	_HASH_PREFIX = "pbkdf2_sha256"
	_HASH_ITERATIONS = 600_000

	def __init__(self, database: DatabaseManager | None = None):
		self.database = database or DatabaseManager(DB_URL)

	@staticmethod
	def _hash(password: str) -> str:
		salt = secrets.token_hex(16)
		digest = hashlib.pbkdf2_hmac(
			"sha256",
			password.encode("utf-8"),
			salt.encode("ascii"),
			AuthManager._HASH_ITERATIONS,
		).hex()
		return f"{AuthManager._HASH_PREFIX}${AuthManager._HASH_ITERATIONS}${salt}${digest}"

	@classmethod
	def _verify(cls, stored_hash: str, password: str) -> tuple[bool, bool]:
		if stored_hash.startswith(f"{cls._HASH_PREFIX}$"):
			try:
				prefix, iterations, salt, expected = stored_hash.split("$", 3)
				if prefix != cls._HASH_PREFIX:
					return False, False
				actual = hashlib.pbkdf2_hmac(
					"sha256",
					password.encode("utf-8"),
					salt.encode("ascii"),
					int(iterations),
				).hex()
				return hmac.compare_digest(actual, expected), False
			except (ValueError, TypeError):
				return False, False

		legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
		return hmac.compare_digest(stored_hash, legacy_hash), True

	def authenticate(self, username: str, password: str) -> User | None:
		record = self.database.fetch_one(
			"SELECT username, role, password_hash FROM users WHERE username = :username",
			{"username": username.strip()},
		)
		if not record:
			return None
		valid, legacy = self._verify(record["password_hash"], password)
		if not valid:
			return None
		if legacy:
			self.database.execute(
				"UPDATE users SET password_hash = :password_hash WHERE username = :username",
				{"username": record["username"], "password_hash": self._hash(password)},
			)
		return User(record["username"], record["role"])

	def create_user(self, username: str, password: str, role: str = "librarian") -> User:
		if not username.strip() or not password:
			raise ValueError("Username and password are required")
		self.database.execute(
			"INSERT INTO users (username, password_hash, role) VALUES (:username, :password_hash, :role)",
			{"username": username.strip(), "password_hash": self._hash(password), "role": role},
		)
		return User(username.strip(), role)
