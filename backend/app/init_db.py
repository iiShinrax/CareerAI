"""
Creates all tables from models.py in the configured database.

Run this once to stand up your schema:

    cd careerai-backend
    python -m app.init_db

This is the fast path for an MVP timeline. If you later need schema
migrations (changing a table after you already have real data in it),
switch to Alembic — but for now, editing models.py and re-running this
is enough.
"""

from .database import engine, Base
from . import models  # noqa: F401  (import registers the models with Base)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    init_db()
