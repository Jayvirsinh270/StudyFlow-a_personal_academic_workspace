"""
Database Connection Manager
Handles SQLite database connection and path management
"""

import sqlite3
import os
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database connection for StudyFlow"""
    
    def __init__(self):
        """Initialize database manager"""
        self.db_path = self._get_db_path()
        self.connection = None
        
    def _get_db_path(self) -> str:
        """Get the database file path"""
        # Get the UserData directory
        current_dir = Path(__file__).parent.parent
        user_data_dir = current_dir / "UserData"
        
        # Ensure UserData directory exists
        user_data_dir.mkdir(exist_ok=True)
        
        # Return database path
        return str(user_data_dir / "studyflow.db")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection, create if not exists"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
        else:
            # Check if connection is still open
            try:
                self.connection.execute("SELECT 1")
            except sqlite3.ProgrammingError:
                # Connection was closed, create new one
                self.connection = sqlite3.connect(self.db_path)
                self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connection = self.get_connection()
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.connection:
            self.connection.close()
            self.connection = None


# Global database manager instance
db_manager = DatabaseManager()
