"""Agent tool for checking member loans and fines."""

from config import DB_URL
from database.db_manager import DatabaseManager


def member_status(member_id: str) -> dict:
	"""Return member details, active loans, and unpaid fines."""
	database = DatabaseManager(DB_URL)
	try:
		member = database.fetch_one("SELECT * FROM members WHERE member_id = :member_id", {"member_id": member_id})
		if not member:
			raise ValueError("Member not found")
		return {
			"member": member,
			"loans": database.fetch_all("SELECT * FROM loans WHERE member_id = :member_id AND returned_on IS NULL", {"member_id": member_id}),
			"fines": database.fetch_all("SELECT * FROM fines WHERE member_id = :member_id AND paid = FALSE", {"member_id": member_id}),
		}
	finally:
		database.close()
