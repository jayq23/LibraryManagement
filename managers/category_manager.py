"""Category and genre business logic."""

from config import DB_URL
from database.db_manager import DatabaseManager


class CategoryManager:
	def __init__(self, database: DatabaseManager | None = None):
		self.database = database or DatabaseManager(DB_URL)

	def list_categories(self) -> list[dict]:
		return self.database.fetch_all(
			"SELECT categories.*, COUNT(books.isbn)::INTEGER AS book_count "
			"FROM categories LEFT JOIN books ON books.category_id = categories.id "
			"GROUP BY categories.id ORDER BY categories.name"
		)

	def books_in_category(self, category_id: int) -> list[dict]:
		return self.database.fetch_all(
			"SELECT title, author, isbn, available_copies FROM books "
			"WHERE category_id = :category_id ORDER BY title",
			{"category_id": category_id},
		)

	def add_category(self, name: str, description: str = "") -> None:
		if not name.strip():
			raise ValueError("Category name is required")
		self.database.execute(
			"INSERT INTO categories (name, description) VALUES (:name, :description)",
			{"name": name.strip(), "description": description.strip()},
		)

	def delete_category(self, category_id: int) -> None:
		self.database.execute("UPDATE books SET category_id = NULL WHERE category_id = :category_id", {"category_id": category_id})
		self.database.execute("DELETE FROM categories WHERE id = :category_id", {"category_id": category_id})