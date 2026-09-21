"""Agent tool for searching the catalog."""

from managers.search_manager import SearchManager


def search_books(query: str) -> list[dict]:
	"""Return books matching a title, author, or ISBN."""
	return SearchManager().search_books(query)
