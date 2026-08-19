"""
Database Connection Manager
Handles SQLite database connection and path management
"""

import sqlite3
import threading
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database connections for StudyFlow.

    Each OS thread gets its own connection via threading.local() so that
    Flask's thread-pool workers never share a single sqlite3.Connection
    object (which would raise "SQLite objects created in a thread can only
    be used in that same thread").
    """

    def __init__(self):
        self.db_path = self._get_db_path()
        self._local = threading.local()   # thread-local storage

    def _get_db_path(self) -> str:
        current_dir = Path(__file__).parent.parent
        user_data_dir = current_dir / "UserData"
        user_data_dir.mkdir(exist_ok=True)
        return str(user_data_dir / "studyflow.db")

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        """Create or backfill database columns required by the current app version."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
        if cursor.fetchone() is not None:
            cursor.execute("PRAGMA table_info(notes)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'is_pinned' not in columns:
                cursor.execute("ALTER TABLE notes ADD COLUMN is_pinned INTEGER DEFAULT 0")
        conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Return this thread's connection, creating it if necessary."""
        conn = getattr(self._local, 'connection', None)
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            self._ensure_schema(conn)
            self._local.connection = conn
        else:
            # Verify the connection is still alive
            try:
                conn.execute("SELECT 1")
            except sqlite3.ProgrammingError:
                conn = sqlite3.connect(self.db_path)
                conn.execute("PRAGMA foreign_keys = ON")
                self._ensure_schema(conn)
                self._local.connection = conn
        return conn

    def close_connection(self):
        """Close this thread's connection."""
        conn = getattr(self._local, 'connection', None)
        if conn:
            conn.close()
            self._local.connection = None

    # Keep context-manager support (used by backup_manager and tests)
    def __enter__(self):
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Do NOT close on exit — the thread-local connection is reused across
        # calls within the same request/thread.  Let close_connection() be
        # called explicitly when a thread is truly done.
        pass


# Global database manager instance
db_manager = DatabaseManager()
