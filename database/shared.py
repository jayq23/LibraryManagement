# Single shared database manager for the whole app.
#
# Every manager used to build its own DatabaseManager (and its own connection
# pool) each time it was created. Creating them over and over made every screen
# refresh slower and slowly used up PostgreSQL connections. All managers now
# call get_database() so the app only ever opens one engine and one pool.

from config import DB_URL
from database.db_manager import DatabaseManager

_database: DatabaseManager | None = None


def get_database() -> DatabaseManager:
    global _database
    if _database is None:
        _database = DatabaseManager(DB_URL)
    return _database
