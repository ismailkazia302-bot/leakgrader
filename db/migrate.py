"""
LeakGrader Database Migration Runner (Sprint 1)
Applies db/schema.sql idempotently and tracks applied migrations in schema_migrations table.
"""

import os
import sys
import re
import logging
from datetime import datetime, timezone

from db.connection import get_db_cursor, is_sqlite

logger = logging.getLogger("leakgrader.migrate")

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
    """Runs all pending schema migrations idempotently"""
    if not schema_file:
        schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")

    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found at {schema_file}")

    init_migrations_table()

    migration_version = "001_initial_schema"
    if is_migration_applied(migration_version):
        print(f"[*] Migration {migration_version} is already applied.")
        return True

    print(f"[*] Applying migration {migration_version} from {schema_file}...")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split SQL into individual statements
    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]

    with get_db_cursor(commit=True) as cur:
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
    print(f"[+] Migration {migration_version} successfully applied!")
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
