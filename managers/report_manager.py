"""Summary and report generation."""

from config import DB_URL
from database.db_manager import DatabaseManager


class ReportManager:
    def __init__(self, database: DatabaseManager | None = None):
        self.database = database or DatabaseManager(DB_URL)

    def summary(self) -> dict[str, int | float]:
        return {
            "total_books": self.database.fetch_one("SELECT COALESCE(SUM(total_copies), 0) AS value FROM books")["value"],
            "active_loans": self.database.fetch_one("SELECT COUNT(*) AS value FROM loans WHERE returned_on IS NULL")["value"],
            "overdue": self.database.fetch_one("SELECT COUNT(*) AS value FROM loans WHERE returned_on IS NULL AND due_date < CURRENT_DATE")["value"],
            "members": self.database.fetch_one("SELECT COUNT(*) AS value FROM members WHERE active = TRUE")["value"],
            "unpaid_fines": self.database.fetch_one("SELECT COALESCE(SUM(amount), 0) AS value FROM fines WHERE paid = FALSE")["value"],
        }

    def monthly_activity(self) -> list[dict]:
        """Return the latest twelve months of loans and collected fine amounts."""
        return self.database.fetch_all(
            "WITH months AS ("
            " SELECT date_trunc('month', CURRENT_DATE) - (n * INTERVAL '1 month') AS month_start"
            " FROM generate_series(11, 0, -1) AS series(n)"
            "), loan_counts AS ("
            " SELECT date_trunc('month', borrowed_on) AS month_start, COUNT(*)::INTEGER AS loans"
            " FROM loans GROUP BY date_trunc('month', borrowed_on)"
            "), fine_totals AS ("
            " SELECT date_trunc('month', created_at) AS month_start,"
            " COALESCE(SUM(amount) FILTER (WHERE paid), 0)::NUMERIC AS fines"
            " FROM fines GROUP BY date_trunc('month', created_at)"
            ") SELECT to_char(months.month_start, 'Mon YYYY') AS label,"
            " COALESCE(loan_counts.loans, 0) AS loans,"
            " COALESCE(fine_totals.fines, 0)::NUMERIC AS fines"
            " FROM months"
            " LEFT JOIN loan_counts ON loan_counts.month_start = months.month_start"
            " LEFT JOIN fine_totals ON fine_totals.month_start = months.month_start"
            " ORDER BY months.month_start"
        )