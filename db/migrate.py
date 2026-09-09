"""
LeakGrader Database Migration Runner (Sprint 1)
Applies db/schema.sql idempotently and tracks applied migrations in schema_migrations table.
Guarded by session-level PostgreSQL advisory lock (pg_advisory_lock) for multi-worker safe startup.
"""

import os
import sys
import re
import logging
import threading
from datetime import datetime, timezone

from db.connection import get_db_cursor, is_sqlite

logger = logging.getLogger("leakgrader.migrate")

# Session-level advisory lock key for PostgreSQL migration coordination (64-bit int)
# Ensures multi-worker Gunicorn startup executes migrations strictly once without race conditions.
MIGRATION_ADVISORY_LOCK_KEY = 7482910384729102
_SQLITE_MIGRATION_LOCK = threading.Lock()


def _acquire_advisory_lock(cur) -> bool:
    """Acquires advisory lock: PostgreSQL session-level advisory lock or SQLite thread lock."""
    if is_sqlite():
        _SQLITE_MIGRATION_LOCK.acquire()
        return True
    try:
        cur.execute("SELECT pg_advisory_lock(%s);", (MIGRATION_ADVISORY_LOCK_KEY,))
        return True
    except Exception as e:
        logger.warning(f"Advisory lock acquisition notice: {type(e).__name__}")
        return False


def _release_advisory_lock(cur):
    """Releases advisory lock safely."""
    if is_sqlite():
        if _SQLITE_MIGRATION_LOCK.locked():
            _SQLITE_MIGRATION_LOCK.release()
        return
    try:
        cur.execute("SELECT pg_advisory_unlock(%s);", (MIGRATION_ADVISORY_LOCK_KEY,))
    except Exception as e:
        logger.warning(f"Advisory lock release notice: {type(e).__name__}")


def init_migrations_table():
    with get_db_cursor(commit=True) as cur:
        if is_sqlite():
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)


def is_migration_applied(version: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations WHERE version = %s;", (version,))
        return cur.fetchone() is not None


def record_migration(version: str):
    with get_db_cursor(commit=True) as cur:
        if is_sqlite():
            cur.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (%s, %s);",
                (version, datetime.now(timezone.utc).isoformat())
            )
        else:
            cur.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (%s, NOW()) ON CONFLICT (version) DO NOTHING;",
                (version,)
            )


def _strip_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        clean_line = re.sub(r"--.*$", "", line)
        if clean_line.strip():
            lines.append(clean_line)
    return "\n".join(lines).strip()


def _adapt_statement_for_sqlite(stmt: str) -> str:
    """Adapts Postgres DDL to SQLite syntax"""
    s = _strip_comments(stmt)
    if not s:
        return ""
    if s.upper().startswith("CREATE EXTENSION"):
        return ""
    
    # Replace PG types with SQLite types
    s = s.replace("TIMESTAMPTZ", "TEXT")
    s = s.replace("JSONB", "TEXT")
    s = s.replace("INET", "TEXT")
    s = s.replace("UUID", "TEXT")
    s = s.replace("BOOLEAN", "INTEGER")
    s = s.replace("DEFAULT gen_random_uuid()", "DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-a' || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))")
    s = s.replace("DEFAULT NOW()", "DEFAULT CURRENT_TIMESTAMP")
    s = s.replace("NOW()", "CURRENT_TIMESTAMP")
    return s


def run_migrations(schema_file: str = None) -> bool:
    """
    Runs all pending schema migrations idempotently and safely in multi-worker environments.
    Acquires an advisory lock (PostgreSQL session-level advisory lock / SQLite lock)
    so concurrent Gunicorn workers do not race.
    """
    if not schema_file:
        schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")

    if not os.path.exists(schema_file):
        logger.error(f"Schema file not found at {schema_file}")
        return False

    migration_version = "001_initial_schema"

    try:
        # Fast-path check: if migration already applied, skip immediately
        try:
            init_migrations_table()
            if is_migration_applied(migration_version):
                logger.info(f"[*] Migration {migration_version} is already applied.")
                return True
        except Exception:
            pass

        with get_db_cursor(commit=True) as cur:
            lock_acquired = _acquire_advisory_lock(cur)
            try:
                # Under the lock, re-check whether another worker already completed the migration
                init_migrations_table()
                if is_migration_applied(migration_version):
                    logger.info(f"[*] Migration {migration_version} is already applied by another worker.")
                    return True

                logger.info(f"[*] Applying migration {migration_version} from {schema_file}...")

                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_sql = f.read()

                statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

                for stmt in statements:
                    if is_sqlite():
                        adapted = _adapt_statement_for_sqlite(stmt)
                        if adapted:
                            cur.execute(adapted)
                    else:
                        clean_stmt = _strip_comments(stmt)
                        if clean_stmt:
                            cur.execute(clean_stmt)

                record_migration(migration_version)
                logger.info(f"[+] Migration {migration_version} successfully applied!")
                return True
            finally:
                if lock_acquired:
                    _release_advisory_lock(cur)

    except Exception as e:
        # Database temporarily unavailable or connection failure:
        # Log clean error without exposing DATABASE_URL or credentials.
        # Do not crash the web server so public pages can continue to serve in degraded mode.
        clean_err = re.sub(r"://[^@]+@", "://***:***@", str(e))
        logger.error(f"[DB Migration Warning] Startup migration could not connect to database: {clean_err}. Web service continuing.")
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)

