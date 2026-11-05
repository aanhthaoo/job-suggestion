"""Database connection helper (psycopg2)."""
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_URL = "postgresql://postgres:postgres@localhost:5432/jobportal"


def get_dsn() -> str:
    """DATABASE_URL, else built from the project .env (local dev outside Docker)."""
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    from dotenv import dotenv_values
    from .paths import ROOT
    env = dotenv_values(ROOT / ".env")
    user = env.get("DB_USER", "postgres")
    pw = env.get("DB_PASSWORD", "postgres")
    name = env.get("DB_NAME", "jobportal")
    return f"postgresql://{user}:{pw}@localhost:5432/{name}"


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
