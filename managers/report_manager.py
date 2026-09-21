"""Summary and report generation."""

from config import DB_URL
from database.db_manager import DatabaseManager


class ReportManager:
	def __init__(self, database: DatabaseManager | None = None):
		self.database = database or DatabaseManager(DB_URL)

	def summary(self) -> dict[str, int]:
		return {
			"total_books": self.database.fetch_one("SELECT COALESCE(SUM(total_copies), 0) AS value FROM books")["value"],
			"active_loans": self.database.fetch_one("SELECT COUNT(*) AS value FROM loans WHERE returned_on IS NULL")["value"],
			"overdue": self.database.fetch_one("SELECT COUNT(*) AS value FROM loans WHERE returned_on IS NULL AND due_date < CURRENT_DATE")["value"],
			"members": self.database.fetch_one("SELECT COUNT(*) AS value FROM members WHERE active = TRUE")["value"],
		}

	def monthly_activity(self) -> list[dict]:
		"""Return the latest twelve months of loans and collected fine amounts."""
		return self.database.fetch_all(
			"WITH months AS ("
			" SELECT date_trunc('month', CURRENT_DATE) - (n * INTERVAL '1 month') AS month_start"
			" FROM generate_series(11, 0, -1) AS series(n)"
			") SELECT to_char(months.month_start, 'Mon YYYY') AS label,"
			" COUNT(loans.id)::INTEGER AS loans,"
			" COALESCE(SUM(CASE WHEN fines.paid THEN fines.amount ELSE 0 END), 0)::NUMERIC AS fines"
			" FROM months LEFT JOIN loans ON date_trunc('month', loans.borrowed_on) = months.month_start"
			" LEFT JOIN fines ON date_trunc('month', fines.created_at) = months.month_start"
			" GROUP BY months.month_start ORDER BY months.month_start"
		)
