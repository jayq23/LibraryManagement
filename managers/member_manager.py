"""Member business logic."""

from config import DB_URL
from database.db_manager import DatabaseManager


class MemberManager:
    def __init__(self, database: DatabaseManager | None = None):
        self.database = database or DatabaseManager(DB_URL)

    @staticmethod
    def _normalize_id(member_id: str | None) -> str:
        return (member_id or "").strip().upper()

    def list_members(self) -> list[dict]:
        # ORDER BY member_id DESC so M005 -> M001
        rows = self.database.fetch_all(
            "SELECT member_id, name, email, active FROM members ORDER BY member_id DESC"
        )
        return [
            {
                "member_id": row["member_id"],
                "name": row["name"],
                "email": row["email"],
                "active": bool(row["active"]),
            }
            for row in rows
        ]

    def get_member(self, member_id: str):
        return self.database.fetch_one(
            "SELECT * FROM members WHERE member_id = :member_id",
            {"member_id": self._normalize_id(member_id)},
        )

    def next_member_id(self) -> str:
        """Returns the next free ID (e.g. M007) directly via PostgreSQL regex query."""
        row = self.database.fetch_one(
            "SELECT MAX(CAST(SUBSTRING(member_id FROM 2) AS INTEGER)) as max_num "
            "FROM members WHERE member_id ~ '^M[0-9]+$'"
        )
        max_num = row["max_num"] if row and row["max_num"] is not None else 0
        return f"M{max_num + 1:03d}"

    def add_member(self, member_id: str | None, name: str, email: str) -> str:
        """Adds a member and returns the member ID. Pass None or '' to auto-generate the ID."""
        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name or not email:
            raise ValueError("Name and email are required.")

        member_id = self._normalize_id(member_id) or self.next_member_id()

        if self.get_member(member_id):
            raise ValueError(f"A member with ID '{member_id}' already exists.")
        if self.database.fetch_one(
            "SELECT 1 FROM members WHERE LOWER(email) = :email", {"email": email}
        ):
            raise ValueError(f"A member with email '{email}' already exists.")

        self.database.execute(
            "INSERT INTO members (member_id, name, email, active) "
            "VALUES (:member_id, :name, :email, TRUE)",
            {"member_id": member_id, "name": name, "email": email},
        )
        return member_id

    def update_member(self, member_id: str, name: str, email: str) -> None:
        member_id = self._normalize_id(member_id)
        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not name or not email:
            raise ValueError("Name and email are required.")
        if not self.get_member(member_id):
            raise ValueError(f"Member '{member_id}' was not found.")
        if self.database.fetch_one(
            "SELECT 1 FROM members WHERE LOWER(email) = :email AND member_id != :member_id",
            {"email": email, "member_id": member_id},
        ):
            raise ValueError(f"Email '{email}' is already used by another member.")

        self.database.execute(
            "UPDATE members SET name = :name, email = :email WHERE member_id = :member_id",
            {"member_id": member_id, "name": name, "email": email},
        )

    def delete_member(self, member_id: str) -> None:
        """Hard delete. Only allowed for members with no loan history; otherwise deactivate."""
        member_id = self._normalize_id(member_id)
        if not self.get_member(member_id):
            raise ValueError(f"Member '{member_id}' was not found.")
        if self.database.fetch_one(
            "SELECT 1 FROM loans WHERE member_id = :member_id AND returned_on IS NULL",
            {"member_id": member_id},
        ):
            raise ValueError("Member has an active loan")
        if self.database.fetch_one(
            "SELECT 1 FROM loans WHERE member_id = :member_id",
            {"member_id": member_id},
        ):
            raise ValueError("Member has loan history. Deactivate the member instead of deleting.")

        self.database.execute(
            "DELETE FROM members WHERE member_id = :member_id",
            {"member_id": member_id},
        )

    def deactivate(self, member_id: str) -> None:
        self._set_active(member_id, False)

    def reactivate(self, member_id: str) -> None:
        self._set_active(member_id, True)

    def _set_active(self, member_id: str, active: bool) -> None:
        member_id = self._normalize_id(member_id)
        if not self.get_member(member_id):
            raise ValueError(f"Member '{member_id}' was not found.")
        self.database.execute(
            "UPDATE members SET active = :active WHERE member_id = :member_id",
            {"active": active, "member_id": member_id},
        )