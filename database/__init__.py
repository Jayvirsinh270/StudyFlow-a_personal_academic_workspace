"""
Database Package
Contains database connection, setup, and query functions
"""

from database.database import db_manager
from database.db_setup import initialize_database, create_tables
from database.queries import (
    # Student Profile
    create_student_profile,
    get_student_profile,
    update_student_profile,
    # Subjects
    add_subject,
    get_subjects,
    get_subject_by_id,
    update_subject,
    delete_subject,
    # Notes
    create_note,
    get_notes,
    get_note_by_id,
    duplicate_note,
    update_note,
    delete_note,
    # Subject Files
    add_subject_file,
    get_subject_files,
    update_subject_file,
    delete_subject_file,
    # Attendance
    update_attendance,
    get_attendance,
    calculate_attendance_percentage,
    # Assignments
    add_assignment,
    get_assignments,
    update_assignment,
    delete_assignment,
    # Timetable
    add_timetable_entry,
    get_timetable,
    get_timetable_by_day,
    update_timetable_entry,
    delete_timetable_entry,
    # CGPA
    add_cgpa_record,
    get_cgpa_records,
    calculate_cgpa,
    update_cgpa_record,
    delete_cgpa_record,
    # Calendar Events
    add_calendar_event,
    get_calendar_events,
    update_calendar_event,
    delete_calendar_event,
    # Study Tasks
    add_study_task,
    get_study_tasks,
    update_study_task,
    delete_study_task,
    # Documents
    add_document,
    get_documents,
    delete_document,
    # Settings
    get_setting,
    set_setting
)

__all__ = [
    'db_manager',
    'initialize_database',
    'create_tables',
    'create_student_profile',
    'get_student_profile',
    'update_student_profile',
    'add_subject',
    'get_subjects',
    'get_subject_by_id',
    'update_subject',
    'delete_subject',
    'create_note',
    'get_notes',
    'get_note_by_id',
    'duplicate_note',
    'update_note',
    'delete_note',
    'add_subject_file',
    'get_subject_files',
    'update_subject_file',
    'delete_subject_file',
    'update_attendance',
    'get_attendance',
    'calculate_attendance_percentage',
    'add_assignment',
    'get_assignments',
    'update_assignment',
    'delete_assignment',
    'add_timetable_entry',
    'get_timetable',
    'get_timetable_by_day',
    'update_timetable_entry',
    'delete_timetable_entry',
    'add_cgpa_record',
    'get_cgpa_records',
    'calculate_cgpa',
    'update_cgpa_record',
    'delete_cgpa_record',
    'add_calendar_event',
    'get_calendar_events',
    'update_calendar_event',
    'delete_calendar_event',
    'add_study_task',
    'get_study_tasks',
    'update_study_task',
    'delete_study_task',
    'add_document',
    'get_documents',
    'delete_document',
    'get_setting',
    'set_setting'
]
