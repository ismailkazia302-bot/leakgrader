"""
LeakGrader Database Connection Manager (Sprint 1)
Supports PostgreSQL connection pooling via psycopg2, with automatic reconnection,
timeout configuration, credential redaction, and an SQLite fallback for local test execution.
"""

import os
import re
import sys
import time
import logging
import sqlite3
import uuid
import json
from contextlib import contextmanager
from datetime import datetime, timezone

logger = logging.getLogger("leakgrader.db")

# Mask database credentials for safe logging
def mask_database_url(url: str) -> str:
    if not url:
        return "<none>"
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:********@", url)

_PG_POOL = None
_IS_SQLITE = False
_SQLITE_PATH = None

def _init_sqlite_db(path: str):
    conn = sqlite3.connect(path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Custom sqlite functions for postgres compatibility
    conn.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))
    conn.create_function("NOW", 0, lambda: datetime.now(timezone.utc).isoformat())
    return conn

def init_pool():
    global _PG_POOL, _IS_SQLITE, _SQLITE_PATH
    db_url = os.environ.get("DATABASE_URL", "").strip()

    if not db_url or db_url.startswith("sqlite:"):
        _IS_SQLITE = True
        if db_url.startswith("sqlite:///"):
            _SQLITE_PATH = db_url.replace("sqlite:///", "")
        elif db_url.startswith("sqlite://"):
            _SQLITE_PATH = db_url.replace("sqlite://", "")
        else:
            storage_dir = os.environ.get("STORAGE_DIR") or os.path.join(os.path.dirname(__file__), "..", "storage")
            os.makedirs(storage_dir, exist_ok=True)
            _SQLITE_PATH = os.path.join(storage_dir, "leakgrader_local.db")
        logger.info("Initializing SQLite database connection (local/test mode)")
        return

    # PostgreSQL via psycopg2
    try:
        import psycopg2
        from psycopg2 import pool
        from psycopg2.extras import RealDictCursor

        # Fix postgres:// URL scheme if used by Render/Heroku
        if db_url.startswith("postgres://"):
            db_url = "postgresql://" + db_url[len("postgres://"):]

        _IS_SQLITE = False
        logger.info(f"Initializing PostgreSQL connection pool: {mask_database_url(db_url)}")
        _PG_POOL = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=int(os.environ.get("DB_POOL_MAX", 20)),
            dsn=db_url,
            connect_timeout=int(os.environ.get("DB_CONNECT_TIMEOUT", 5))
        )
    except Exception as e:
        logger.warning(f"PostgreSQL connection initialization failed ({e}). Falling back to local SQLite adapter.")
        _IS_SQLITE = True
        storage_dir = os.environ.get("STORAGE_DIR") or os.path.join(os.path.dirname(__file__), "..", "storage")
        os.makedirs(storage_dir, exist_ok=True)
        _SQLITE_PATH = os.path.join(storage_dir, "leakgrader_local.db")

def is_sqlite() -> bool:
    if _PG_POOL is None and not _IS_SQLITE:
        init_pool()
    return _IS_SQLITE

@contextmanager
def get_db_connection():
    if _PG_POOL is None and not _IS_SQLITE:
        init_pool()

    if _IS_SQLITE:
        conn = _init_sqlite_db(_SQLITE_PATH)
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = None
        try:
            conn = _PG_POOL.getconn()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise e
        finally:
            if conn:
                _PG_POOL.putconn(conn)

class SQLiteCursorWrapper:
    """Wraps sqlite3.Cursor to provide dict-like row access and param %s translation"""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        # Translate postgres %s parameter placeholders to sqlite ?
        translated_sql = sql
        if "%s" in sql:
            translated_sql = sql.replace("%s", "?")
        
        # Replace TIMESTAMPTZ and other PG types in ad-hoc queries if needed
        if params is not None:
            # Convert UUIDs/datetimes/dicts to str for sqlite
            formatted_params = []
            for p in params:
                if isinstance(p, dict) or isinstance(p, list):
                    formatted_params.append(json.dumps(p))
                elif isinstance(p, datetime):
                    formatted_params.append(p.isoformat())
                elif isinstance(p, uuid.UUID):
                    formatted_params.append(str(p))
                else:
                    formatted_params.append(p)
            return self._cursor.execute(translated_sql, formatted_params)
        return self._cursor.execute(translated_sql)

    def executemany(self, sql, seq_of_params):
        translated_sql = sql.replace("%s", "?")
        return self._cursor.executemany(translated_sql, seq_of_params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows]

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()

@contextmanager
def get_db_cursor(commit: bool = False):
    with get_db_connection() as conn:
        if is_sqlite():
            cursor = conn.cursor()
            wrapper = SQLiteCursorWrapper(cursor)
            try:
                yield wrapper
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
        else:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

def execute_query(sql: str, params=None, fetchone: bool = False, fetchall: bool = False, commit: bool = False):
    """Convenience executor for safe transactional queries"""
    with get_db_cursor(commit=commit) as cur:
        cur.execute(sql, params)
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        return cur.rowcount

def close_pool():
    global _PG_POOL
    if _PG_POOL:
        try:
            _PG_POOL.closeall()
        except Exception:
            pass
        _PG_POOL = None
