"""Agent tool for placing authorized reservations."""

from managers.transaction_manager import TransactionManager


def reserve_book(member_id: str, isbn: str) -> int:
	"""Place a reservation for an existing member and book."""
	return TransactionManager().reserve(member_id, isbn)
