# Library Management System

The application uses PostgreSQL for users, members, books, loans, reservations, and fines.

## Development

1. Install dependencies with `python3 -m pip install -r requirements.txt`.
2. Create a PostgreSQL database named `library_management`.
3. Set `DB_URL` in `.env`, for example `postgresql+psycopg2://postgres:postgres@localhost:5432/library_management`.
4. Create tables and development records with `python3 -m database.seed_data`.
5. Launch the application with `python3 main.py`.

The seeded development account is `admin` with password `admin`. Change this password before production use.
