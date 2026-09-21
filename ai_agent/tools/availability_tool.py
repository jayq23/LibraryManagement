"""Agent tool for checking book availability."""

from managers.book_manager import BookManager


def check_availability(isbn: str) -> int:
	"""Return the number of available copies for an ISBN."""
	return BookManager().availability(isbn)
