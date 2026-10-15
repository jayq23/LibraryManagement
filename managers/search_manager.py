# Search and filtering business logic.

from managers.book_manager import BookManager


class SearchManager:
	# Initialize the component.
	def __init__(self, book_manager: BookManager | None = None):
		self.book_manager = book_manager or BookManager()

	# Search search books.
	def search_books(self, query: str = "") -> list[dict]:
		return self.book_manager.search(query)
