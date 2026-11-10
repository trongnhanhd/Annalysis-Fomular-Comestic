import pytest


@pytest.fixture(autouse=True)
def _hermetic_storage(monkeypatch):
    # Unit tests use SQLite unless a test opts in explicitly; PostgreSQL is verified by scripts/verify_postgres_v452.py.
    monkeypatch.delenv('V45_DATABASE_URL', raising=False)
