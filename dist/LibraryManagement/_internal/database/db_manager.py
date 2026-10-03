"""Database connection and query service."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result


class DatabaseManager:
    """Small SQLAlchemy service used by the managers and scripts."""

    def __init__(self, database_url: str, engine: Engine | None = None):
        self.database_url = database_url
        self.engine = engine or create_engine(database_url, pool_pre_ping=True)

    def execute(self, query: str, parameters: Mapping[str, Any] | None = None) -> Result[Any]:
        """Execute a statement in a committed transaction."""
        with self.engine.begin() as connection:
            return connection.execute(text(query), parameters or {})

    def fetch_all(self, query: str, parameters: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        with self.engine.begin() as connection:
            result = connection.execute(text(query), parameters or {})
            return [dict(row) for row in result.mappings().all()]

    def fetch_one(self, query: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        with self.engine.begin() as connection:
            result = connection.execute(text(query), parameters or {})
            row = result.mappings().first()
            return dict(row) if row else None

    def close(self) -> None:
        self.engine.dispose()
