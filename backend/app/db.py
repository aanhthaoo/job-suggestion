"""Database connection helper (psycopg2)."""
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_URL = "postgresql://postgres:postgres@localhost:5432/jobportal"


def get_dsn() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_URL)


def connect(retries: int = 30, delay: float = 2.0):
    """Connect to Postgres, retrying while it boots."""
    last_err = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(get_dsn())
            conn.autocommit = False
            return conn
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(delay)
    raise RuntimeError(f"Could not connect to Postgres: {last_err}")


__all__ = ["connect", "get_dsn", "RealDictCursor"]
