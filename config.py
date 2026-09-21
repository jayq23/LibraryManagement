"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

try:
	from dotenv import load_dotenv
except ModuleNotFoundError:
	def load_dotenv(_: Path) -> None:
		return None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "Library Management System")
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/library_management")
if DB_URL.startswith("sqlite"):
	raise RuntimeError("PostgreSQL is required. Set DB_URL to a PostgreSQL connection string in .env.")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
