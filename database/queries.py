"""
Database Queries
Contains all CRUD operations for StudyFlow database
"""

import json
from database.database import db_manager
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ==================== STUDENT PROFILE ====================

def create_student_profile(name: str, enrollment_number: str = None, 
                          department: str = None, semester: int = None,
                          profile_picture_path: str = None) -> int:
    """Create a new student profile"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO student_profile (name, enrollment_number, department, semester, profile_picture_path)
        VALUES (?, ?, ?, ?, ?)
    """, (name, enrollment_number, department, semester, profile_picture_path))
    
    conn.commit()
    return cursor.lastrowid


def get_student_profile() -> Optional[Dict]:
    """Get the student profile"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM student_profile LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def update_student_profile(profile_id: int, name: str = None, 
                          enrollment_number: str = None, department: str = None,
                          semester: int = None, profile_picture_path: str = None) -> bool:
    """Update student profile"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if name:
        updates.append("name = ?")
        values.append(name)
    if enrollment_number:
        updates.append("enrollment_number = ?")
        values.append(enrollment_number)
    if department:
        updates.append("department = ?")
        values.append(department)
    if semester:
        updates.append("semester = ?")
        values.append(semester)
    if profile_picture_path:
        updates.append("profile_picture_path = ?")
        values.append(profile_picture_path)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(profile_id)
        
        query = f"UPDATE student_profile SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


# ==================== SUBJECTS ====================

def add_subject(name: str, subject_code: str = None, faculty_name: str = None,
                semester: int = None, credit: float = None, color: str = None) -> int:
    """Add a new subject"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO subjects (name, subject_code, faculty_name, semester, credit, color)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, subject_code, faculty_name, semester, credit, color))
    
    conn.commit()
    return cursor.lastrowid


def get_subjects() -> List[Dict]:
    """Get all subjects"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM subjects ORDER BY name")
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_subject_by_id(subject_id: int) -> Optional[Dict]:
    """Get a subject by ID"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    row = cursor.fetchone()
    
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def update_subject(subject_id: int, name: str = None, subject_code: str = None,
                  faculty_name: str = None, semester: int = None, 
                  credit: float = None, color: str = None) -> bool:
    """Update a subject"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if name:
        updates.append("name = ?")
        values.append(name)
    if subject_code:
        updates.append("subject_code = ?")
        values.append(subject_code)
    if faculty_name:
        updates.append("faculty_name = ?")
        values.append(faculty_name)
    if semester:
        updates.append("semester = ?")
        values.append(semester)
    if credit:
        updates.append("credit = ?")
        values.append(credit)
    if color:
        updates.append("color = ?")
        values.append(color)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(subject_id)
        
        query = f"UPDATE subjects SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_subject(subject_id: int) -> bool:
    """Delete a subject (cascade deletes related records)"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== NOTES ====================

def create_note(subject_id: int, title: str, content: str = "") -> int:
    """Create a new note"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO notes (subject_id, title, content)
        VALUES (?, ?, ?)
    """, (subject_id, title, content))
    
    conn.commit()
    return cursor.lastrowid


def get_notes(subject_id: int = None, sort_by: str = "updated_at") -> List[Dict]:
    """Get notes, optionally filtered by subject and sorted by the requested field."""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if subject_id:
        cursor.execute("SELECT * FROM notes WHERE subject_id = ?", (subject_id,))
    else:
        cursor.execute("SELECT * FROM notes")
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    notes = [dict(zip(columns, row)) for row in rows]

    def sort_key(note: Dict):
        pinned = 1 if note.get('is_pinned') else 0
        base_value = note.get(sort_by) or note.get('updated_at') or ""
        if isinstance(base_value, str):
            return (not pinned, base_value.lower())
        return (not pinned, base_value)

    return sorted(notes, key=sort_key)


def get_note_by_id(note_id: int) -> Optional[Dict]:
    """Get a note by ID"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def duplicate_note(note_id: int, title: str = None) -> int:
    """Create a duplicate of an existing note."""
    original_note = get_note_by_id(note_id)
    if not original_note:
        return None

    copy_title = title or f"{original_note.get('title', 'Untitled')} (Copy)"
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO notes (subject_id, title, content, is_pinned)
        VALUES (?, ?, ?, ?)
        """,
        (original_note['subject_id'], copy_title, original_note.get('content', ''), original_note.get('is_pinned', 0))
    )
    conn.commit()
    return cursor.lastrowid


def update_note(note_id: int, title: str = None, content: str = None, is_pinned: bool = None) -> bool:
    """Update a note"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if title is not None:
        updates.append("title = ?")
        values.append(title)
    if content is not None:
        updates.append("content = ?")
        values.append(content)
    if is_pinned is not None:
        updates.append("is_pinned = ?")
        values.append(1 if is_pinned else 0)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(note_id)
        
        query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_note(note_id: int) -> bool:
    """Delete a note"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== SUBJECT FILES ====================

def add_subject_file(subject_id: int, file_name: str, file_path: str, 
                    file_type: str = None, file_size: int = None) -> int:
    """Add a file to a subject"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO subject_files (subject_id, file_name, file_path, file_type, file_size)
        VALUES (?, ?, ?, ?, ?)
    """, (subject_id, file_name, file_path, file_type, file_size))
    
    conn.commit()
    return cursor.lastrowid


def get_subject_files(subject_id: int = None) -> List[Dict]:
    """Get files, optionally filtered by subject"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if subject_id:
        cursor.execute("SELECT * FROM subject_files WHERE subject_id = ? ORDER BY uploaded_at DESC", (subject_id,))
    else:
        cursor.execute("SELECT * FROM subject_files ORDER BY uploaded_at DESC")
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def update_subject_file(file_id: int, file_name: str = None, file_path: str = None,
                       file_type: str = None, file_size: str = None) -> bool:
    """Update a subject file record."""
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    updates = []
    values = []

    if file_name is not None:
        updates.append("file_name = ?")
        values.append(file_name)
    if file_path is not None:
        updates.append("file_path = ?")
        values.append(file_path)
    if file_type is not None:
        updates.append("file_type = ?")
        values.append(file_type)
    if file_size is not None:
        updates.append("file_size = ?")
        values.append(file_size)

    if updates:
        values.append(file_id)
        query = f"UPDATE subject_files SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_subject_file(file_id: int) -> bool:
    """Delete a subject file"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM subject_files WHERE id = ?", (file_id,))
    conn.commit()
    return cursor.rowcount > 0


def add_document(subject_id: int, file_name: str, file_path: str,
                file_type: str = None, file_size: int = None) -> int:
    """Compatibility wrapper for document uploads using the subject_files table."""
    return add_subject_file(subject_id, file_name, file_path, file_type, file_size)


def get_documents(subject_id: int = None) -> List[Dict]:
    """Compatibility wrapper for retrieving documents stored as subject files."""
    return get_subject_files(subject_id)


def delete_document(file_id: int) -> bool:
    """Compatibility wrapper for deleting a document record."""
    return delete_subject_file(file_id)


# ==================== ATTENDANCE ====================

def update_attendance(subject_id: int, total_lectures: int = None,
                     present_lectures: int = None, absent_lectures: int = None) -> int:
    """Update or create attendance record for a subject"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Check if attendance record exists
    cursor.execute("SELECT id FROM attendance WHERE subject_id = ?", (subject_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing record
        updates = []
        values = []
        
        if total_lectures is not None:
            updates.append("total_lectures = ?")
            values.append(total_lectures)
        if present_lectures is not None:
            updates.append("present_lectures = ?")
            values.append(present_lectures)
        if absent_lectures is not None:
            updates.append("absent_lectures = ?")
            values.append(absent_lectures)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(subject_id)
            
            query = f"UPDATE attendance SET {', '.join(updates)} WHERE subject_id = ?"
            cursor.execute(query, values)
            conn.commit()
            return existing[0]
    else:
        # Create new record
        cursor.execute("""
            INSERT INTO attendance (subject_id, total_lectures, present_lectures, absent_lectures)
            VALUES (?, ?, ?, ?)
        """, (subject_id, total_lectures or 0, present_lectures or 0, absent_lectures or 0))
        conn.commit()
        return cursor.lastrowid


def get_attendance(subject_id: int) -> Optional[Dict]:
    """Get attendance for a subject"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM attendance WHERE subject_id = ?", (subject_id,))
    row = cursor.fetchone()
    
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def calculate_attendance_percentage(subject_id: int) -> float:
    """Calculate attendance percentage for a subject"""
    attendance = get_attendance(subject_id)
    if attendance and attendance['total_lectures'] > 0:
        return (attendance['present_lectures'] / attendance['total_lectures']) * 100
    return 0.0


# ==================== ASSIGNMENTS ====================

def add_assignment(subject_id: int, title: str, description: str = None,
                  due_date: str = None, priority: str = "medium", 
                  status: str = "pending") -> int:
    """Add a new assignment"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO assignments (subject_id, title, description, due_date, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (subject_id, title, description, due_date, priority, status))
    
    conn.commit()
    return cursor.lastrowid


def get_assignments(subject_id: int = None, status: str = None) -> List[Dict]:
    """Get assignments, optionally filtered by subject or status"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if subject_id and status:
        cursor.execute("""
            SELECT * FROM assignments WHERE subject_id = ? AND status = ? 
            ORDER BY due_date ASC
        """, (subject_id, status))
    elif subject_id:
        cursor.execute("""
            SELECT * FROM assignments WHERE subject_id = ? ORDER BY due_date ASC
        """, (subject_id,))
    elif status:
        cursor.execute("""
            SELECT * FROM assignments WHERE status = ? ORDER BY due_date ASC
        """, (status,))
    else:
        cursor.execute("SELECT * FROM assignments ORDER BY due_date ASC")
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def update_assignment(assignment_id: int, title: str = None, description: str = None,
                    due_date: str = None, priority: str = None, status: str = None) -> bool:
    """Update an assignment"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if title:
        updates.append("title = ?")
        values.append(title)
    if description:
        updates.append("description = ?")
        values.append(description)
    if due_date:
        updates.append("due_date = ?")
        values.append(due_date)
    if priority:
        updates.append("priority = ?")
        values.append(priority)
    if status:
        updates.append("status = ?")
        values.append(status)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(assignment_id)
        
        query = f"UPDATE assignments SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_assignment(assignment_id: int) -> bool:
    """Delete an assignment"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== TIMETABLE ====================

def add_timetable_entry(day: str, time_slot: str, subject_id: int = None,
                       faculty_name: str = None, classroom: str = None,
                       remarks: str = None) -> int:
    """Add a timetable entry"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO timetable (day, time_slot, subject_id, faculty_name, classroom, remarks)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (day, time_slot, subject_id, faculty_name, classroom, remarks))
    
    conn.commit()
    return cursor.lastrowid


def get_timetable() -> List[Dict]:
    """Get all timetable entries"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, s.name as subject_name 
        FROM timetable t
        LEFT JOIN subjects s ON t.subject_id = s.id
        ORDER BY 
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,
            time_slot
    """)
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_timetable_by_day(day: str) -> List[Dict]:
    """Get timetable entries for a specific day"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.*, s.name as subject_name 
        FROM timetable t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE t.day = ?
        ORDER BY time_slot
    """, (day,))
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def update_timetable_entry(entry_id: int, day: str = None, time_slot: str = None,
                          subject_id: int = None, faculty_name: str = None,
                          classroom: str = None, remarks: str = None) -> bool:
    """Update a timetable entry"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if day:
        updates.append("day = ?")
        values.append(day)
    if time_slot:
        updates.append("time_slot = ?")
        values.append(time_slot)
    if subject_id:
        updates.append("subject_id = ?")
        values.append(subject_id)
    if faculty_name:
        updates.append("faculty_name = ?")
        values.append(faculty_name)
    if classroom:
        updates.append("classroom = ?")
        values.append(classroom)
    if remarks:
        updates.append("remarks = ?")
        values.append(remarks)
    
    if updates:
        values.append(entry_id)
        query = f"UPDATE timetable SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_timetable_entry(entry_id: int) -> bool:
    """Delete a timetable entry"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM timetable WHERE id = ?", (entry_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== CGPA RECORDS ====================

def add_cgpa_record(semester: int, gpa: float, credits: float = None) -> int:
    """Add a CGPA record"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO cgpa_records (semester, gpa, credits)
        VALUES (?, ?, ?)
    """, (semester, gpa, credits))
    
    conn.commit()
    return cursor.lastrowid


def get_cgpa_records() -> List[Dict]:
    """Get all CGPA records"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cgpa_records ORDER BY semester")
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def calculate_cgpa() -> float:
    """Calculate overall CGPA from semester records"""
    records = get_cgpa_records()
    if not records:
        return 0.0
    
    total_credits = sum(r['credits'] or 0 for r in records)
    if total_credits == 0:
        return 0.0
    
    weighted_sum = sum((r['gpa'] or 0) * (r['credits'] or 0) for r in records)
    return weighted_sum / total_credits


def update_cgpa_record(record_id: int, semester: int = None, gpa: float = None,
                      credits: float = None) -> bool:
    """Update a CGPA record"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if semester:
        updates.append("semester = ?")
        values.append(semester)
    if gpa:
        updates.append("gpa = ?")
        values.append(gpa)
    if credits:
        updates.append("credits = ?")
        values.append(credits)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(record_id)
        
        query = f"UPDATE cgpa_records SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_cgpa_record(record_id: int) -> bool:
    """Delete a CGPA record"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM cgpa_records WHERE id = ?", (record_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== CALENDAR EVENTS ====================

def add_calendar_event(title: str, event_date: str, event_type: str = "personal",
                      description: str = None) -> int:
    """Add a calendar event"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO calendar_events (title, event_date, event_type, description)
        VALUES (?, ?, ?, ?)
    """, (title, event_date, event_type, description))
    
    conn.commit()
    return cursor.lastrowid


def get_calendar_events() -> List[Dict]:
    """Get all calendar events"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM calendar_events ORDER BY event_date")
    rows = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def update_calendar_event(event_id: int, title: str = None, event_date: str = None,
                         event_type: str = None, description: str = None) -> bool:
    """Update a calendar event"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if title:
        updates.append("title = ?")
        values.append(title)
    if event_date:
        updates.append("event_date = ?")
        values.append(event_date)
    if event_type:
        updates.append("event_type = ?")
        values.append(event_type)
    if description:
        updates.append("description = ?")
        values.append(description)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(event_id)
        
        query = f"UPDATE calendar_events SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_calendar_event(event_id: int) -> bool:
    """Delete a calendar event"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== STUDY TASKS ====================

def add_study_task(title: str, task_type: str = "daily", description: str = None,
                  due_date: str = None, status: str = "pending") -> int:
    """Add a study task"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO study_tasks (title, task_type, description, due_date, status)
        VALUES (?, ?, ?, ?, ?)
    """, (title, task_type, description, due_date, status))
    
    conn.commit()
    return cursor.lastrowid


def get_study_tasks(task_type: str = None, status: str = None) -> List[Dict]:
    """Get study tasks, optionally filtered"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    if task_type and status:
        cursor.execute("""
            SELECT * FROM study_tasks WHERE task_type = ? AND status = ? 
            ORDER BY due_date ASC
        """, (task_type, status))
    elif task_type:
        cursor.execute("""
            SELECT * FROM study_tasks WHERE task_type = ? ORDER BY due_date ASC
        """, (task_type,))
    elif status:
        cursor.execute("""
            SELECT * FROM study_tasks WHERE status = ? ORDER BY due_date ASC
        """, (status,))
    else:
        cursor.execute("SELECT * FROM study_tasks ORDER BY due_date ASC")
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def update_study_task(task_id: int, title: str = None, task_type: str = None,
                    description: str = None, due_date: str = None, status: str = None) -> bool:
    """Update a study task"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if title:
        updates.append("title = ?")
        values.append(title)
    if task_type:
        updates.append("task_type = ?")
        values.append(task_type)
    if description:
        updates.append("description = ?")
        values.append(description)
    if due_date:
        updates.append("due_date = ?")
        values.append(due_date)
    if status:
        updates.append("status = ?")
        values.append(status)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(task_id)
        
        query = f"UPDATE study_tasks SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        return True
    return False


def delete_study_task(task_id: int) -> bool:
    """Delete a study task"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM study_tasks WHERE id = ?", (task_id,))
    conn.commit()
    return cursor.rowcount > 0


# ==================== SETTINGS ====================

def get_setting(setting_key: str) -> Optional[str]:
    """Get a setting value"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = ?", (setting_key,))
    row = cursor.fetchone()
    
    if row:
        return row[0]
    return None


def set_setting(setting_key: str, setting_value: str) -> bool:
    """Set a setting value, serializing non-string values to JSON before saving."""
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    serialized_value = setting_value
    if not isinstance(setting_value, str):
        serialized_value = json.dumps(setting_value)

    cursor.execute("""
        INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
    """, (setting_key, serialized_value, serialized_value))
    
    conn.commit()
    return True
