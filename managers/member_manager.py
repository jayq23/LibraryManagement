"""Member business logic."""

from config import DB_URL
from database.db_manager import DatabaseManager


class MemberManager:
	def __init__(self, database: DatabaseManager | None = None):
		self.database = database or DatabaseManager(DB_URL)

	def list_members(self) -> list[dict]:
		return self.database.fetch_all("SELECT * FROM members ORDER BY name")

	def get_member(self, member_id: str) -> dict | None:
		return self.database.fetch_one("SELECT * FROM members WHERE member_id = :member_id", {"member_id": member_id})

	def add_member(self, member_id: str, name: str, email: str) -> None:
		self.database.execute(
			"INSERT INTO members (member_id, name, email) VALUES (:member_id, :name, :email)",
			{"member_id": member_id, "name": name, "email": email},
		)

	def update_member(self, member_id: str, name: str, email: str) -> None:
		self.database.execute(
			"UPDATE members SET name = :name, email = :email WHERE member_id = :member_id",
			{"member_id": member_id, "name": name, "email": email},
		)

	def delete_member(self, member_id: str) -> None:
		if self.database.fetch_one("SELECT 1 FROM loans WHERE member_id = :member_id AND returned_on IS NULL", {"member_id": member_id}):
			raise ValueError("Member has an active loan")
		self.database.execute("DELETE FROM members WHERE member_id = :member_id", {"member_id": member_id})

	def deactivate(self, member_id: str) -> None:
		self.database.execute("UPDATE members SET active = FALSE WHERE member_id = :member_id", {"member_id": member_id})
