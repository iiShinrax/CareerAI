"""
Database connection setup.

Reads the connection string from the DATABASE_URL environment variable, e.g.:

    postgresql+psycopg2://careerai_user:password@localhost:5432/careerai

For local dev without Postgres installed yet, you can temporarily point this
at SQLite by setting:

    DATABASE_URL=sqlite:///./careerai.db

Everything else (models, queries) works the same either way while you're
building — swap to real Postgres before deployment/integration week.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./careerai.db",  # safe local default; override in .env for Postgres
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
