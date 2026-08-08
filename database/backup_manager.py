"""
StudyFlow Backup & Export Manager
Provides full database JSON export/import and CSV report exports.
"""

import json
import csv
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
from database import db_manager, get_subjects, get_attendance, get_cgpa_records


def export_full_backup(filepath: str) -> Tuple[bool, str]:
    """Export all database tables into a single JSON backup file."""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Get list of all user tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        backup_data = {
            "version": "1.0",
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tables": {}
        }

        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            backup_data["tables"][table] = [dict(zip(columns, row)) for row in rows]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        return True, f"Backup created successfully at {filepath}"
    except Exception as e:
        return False, f"Failed to create backup: {str(e)}"


def import_full_backup(filepath: str) -> Tuple[bool, str]:
    """Import and restore database tables from a JSON backup file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        if "tables" not in backup_data:
            return False, "Invalid backup file format."

        conn = db_manager.get_connection()
        cursor = conn.cursor()

        tables = backup_data["tables"]

        # Restore in order (clear existing data, then insert)
        for table, rows in tables.items():
            cursor.execute(f"DELETE FROM {table}")
            if rows:
                columns = list(rows[0].keys())
                placeholders = ", ".join(["?"] * len(columns))
                sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                
                for row in rows:
                    cursor.execute(sql, [row[col] for col in columns])

        conn.commit()
        return True, "Database restored successfully!"
    except Exception as e:
        return False, f"Failed to restore database: {str(e)}"


def export_attendance_csv(filepath: str) -> Tuple[bool, str]:
    """Export attendance summary report to CSV."""
    try:
        subjects = get_subjects() or []
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.name, a.total_lectures, a.present_lectures, a.absent_lectures,
                   CASE WHEN a.total_lectures > 0 
                        THEN ROUND((CAST(a.present_lectures AS FLOAT) / a.total_lectures) * 100, 2)
                        ELSE 0 END as percentage
            FROM subjects s
            LEFT JOIN attendance a ON s.id = a.subject_id
            ORDER BY s.name
        """)
        rows = cursor.fetchall()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Subject Name", "Total Lectures", "Present", "Absent", "Attendance %"])
            for row in rows:
                writer.writerow(row)

        return True, f"Attendance report exported to {filepath}"
    except Exception as e:
        return False, f"Failed to export attendance report: {str(e)}"
