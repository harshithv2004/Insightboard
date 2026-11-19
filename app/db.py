"""
InsightBoard — Database Connection Helper
Provides a context-managed cursor so callers never need to manually
close connections or cursors.
"""

import os
import logging
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


def get_connection():
    """Open a new MySQL connection using environment variables."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME", "insightboard"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        autocommit=True,
        connection_timeout=10,
    )


@contextmanager
def get_cursor(dictionary: bool = True):
    """
    Context manager that yields a cursor and ensures the cursor
    and connection are always closed, even on exceptions.

    Usage:
        with get_cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
    except Error as exc:
        logger.error("Database error: %s", exc)
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None and conn.is_connected():
            try:
                conn.close()
            except Exception:
                pass
