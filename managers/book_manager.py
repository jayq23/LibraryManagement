# Book catalog business logic.

from database.db_manager import DatabaseManager
from database.shared import get_database


class BookManager:
	# Initialize the component.
	def __init__(self, database: DatabaseManager | None = None):
		self.database = database or get_database()

	# List list books.
	def list_books(self) -> list[dict]:
		return self.database.fetch_all(
			"SELECT books.*, categories.name AS category_name FROM books "
			"LEFT JOIN categories ON categories.id = books.category_id ORDER BY books.title"
		)

	# Get the price of a single book.
	def get_price(self, isbn: str):
		row = self.database.fetch_one("SELECT price FROM books WHERE isbn = :isbn", {"isbn": isbn})
		return row["price"] if row else None

	# Search search.
	def search(self, query: str = "") -> list[dict]:
		return self.database.fetch_all(
			"SELECT * FROM books WHERE title ILIKE :query OR author ILIKE :query OR isbn ILIKE :query ORDER BY title",
			{"query": f"%{query.strip()}%"},
		)

	# Add a book to the catalog.
	def add_book(self, isbn: str, title: str, author: str, shelf_location: str = "", copies: int = 1, category_id: int | None = None, price: float = 0) -> None:
		if copies < 1:
			raise ValueError("Copies must be positive")
		if price < 0:
			raise ValueError("Price cannot be negative")
		self.database.execute(
			"INSERT INTO books (isbn, title, author, shelf_location, category_id, price, available_copies, total_copies) "
			"VALUES (:isbn, :title, :author, :shelf, :category_id, :price, :copies, :copies)",
			{"isbn": isbn, "title": title, "author": author, "shelf": shelf_location, "category_id": category_id, "price": price, "copies": copies},
		)

	# Update update book.
	def update_book(self, isbn: str, title: str, author: str, shelf_location: str, copies: int) -> None:
		if copies < 1:
			raise ValueError("Copies must be positive")
		book = self.database.fetch_one("SELECT total_copies, available_copies FROM books WHERE isbn = :isbn", {"isbn": isbn})
		if not book:
			raise ValueError("Book not found")
		borrowed = book["total_copies"] - book["available_copies"]
		if copies < borrowed:
			raise ValueError("Copies cannot be lower than copies currently on loan")
		self.database.execute(
			"UPDATE books SET title = :title, author = :author, shelf_location = :shelf, "
			"total_copies = :copies, available_copies = :copies - :borrowed WHERE isbn = :isbn",
			{"isbn": isbn, "title": title, "author": author, "shelf": shelf_location, "copies": copies, "borrowed": borrowed},
		)

	# Delete a book from the catalog.
	def delete_book(self, isbn: str) -> None:
		if self.database.fetch_one("SELECT 1 FROM loans WHERE isbn = :isbn AND returned_on IS NULL", {"isbn": isbn}):
			raise ValueError("Book has an active loan")
		self.database.execute("DELETE FROM books WHERE isbn = :isbn", {"isbn": isbn})

	# Handle availability.
	def availability(self, isbn: str) -> int:
		book = self.database.fetch_one("SELECT available_copies FROM books WHERE isbn = :isbn", {"isbn": isbn})
		if not book:
			raise ValueError("Book not found")
		return book["available_copies"]

	# Add copies to inventory.
	def add_copies(self, isbn: str, quantity: int) -> None:
		if quantity < 1:
			raise ValueError("Quantity must be positive")
		updated = self.database.execute(
			"UPDATE books SET total_copies = total_copies + :quantity, "
			"available_copies = available_copies + :quantity WHERE isbn = :isbn",
			{"isbn": isbn, "quantity": quantity},
		)
		if updated.rowcount == 0:
			raise ValueError("Book not found")