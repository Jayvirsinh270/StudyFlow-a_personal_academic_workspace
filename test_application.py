"""
StudyFlow Application Test Script
Tests database reliability, UI navigation, and file handling
"""

import os
import sys
import sqlite3

# Make console output safe on Windows terminals that use legacy code pages.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import initialize_database, db_manager
from utils.file_manager import file_manager
from database import (
    create_student_profile, get_student_profile, update_student_profile,
    add_subject, get_subjects, update_subject, delete_subject,
    create_note, get_notes, update_note, delete_note, duplicate_note,
    add_subject_file, get_subject_files, delete_subject_file, update_subject_file,
    update_attendance, get_attendance, calculate_attendance_percentage,
    add_assignment, get_assignments, update_assignment, delete_assignment,
    add_timetable_entry, get_timetable, update_timetable_entry, delete_timetable_entry,
    add_cgpa_record, get_cgpa_records, update_cgpa_record, delete_cgpa_record, calculate_cgpa,
    get_setting, set_setting
)


def test_onboarding_visibility_logic():
    """Onboarding should appear for first-time users and stay hidden once set up."""
    from main import should_show_onboarding

    assert should_show_onboarding(None, [], False) is True
    assert should_show_onboarding({"name": "Student"}, [], False) is True
    assert should_show_onboarding({"name": "Student"}, [{"id": 1}], False) is False
    assert should_show_onboarding({"name": "Student"}, [], True) is False


def test_document_metadata_updates():
    """Document records should be updatable so file rename workflows work."""
    subject_id = add_subject(name="Docs Subject", semester=1)
    file_id = add_subject_file(subject_id, "draft.txt", "/tmp/draft.txt", "TXT", "1 KB")

    updated = update_subject_file(file_id, file_name="draft-renamed.txt", file_path="/tmp/draft-renamed.txt")
    assert updated is True

    refreshed = get_subject_files(subject_id)
    record = next(item for item in refreshed if item["id"] == file_id)
    assert record["file_name"] == "draft-renamed.txt"
    assert record["file_path"] == "/tmp/draft-renamed.txt"

    delete_subject_file(file_id)
    delete_subject(subject_id)


def test_document_subject_selection_resolution():
    """Upload destination should resolve to the selected subject or a sensible fallback."""
    from modules.documents.documents import resolve_upload_subject_id

    subjects = [{"id": 1, "name": "Math"}, {"id": 2, "name": "Physics"}]

    assert resolve_upload_subject_id(subjects, "Physics") == 2
    assert resolve_upload_subject_id(subjects, "Unknown") == 1
    assert resolve_upload_subject_id([], "Physics") is None


def test_note_preview_generation():
    """Note previews should turn raw content into a short, readable summary."""
    from modules.subjects.workspace import build_note_preview

    assert build_note_preview("Lecture summary") == "Lecture summary"
    assert build_note_preview("Line one\nLine two") == "Line one"
    assert build_note_preview("\n   \n") == "No content yet"


def test_day_plan_summary_formatting():
    """Planner summary should combine classes and events into a useful day overview."""
    from modules.calendar.calendar import build_day_plan_summary

    day_events = [{"title": "Assignment due", "event_type": "academic"}]
    timetable_entries = [{"day": "Monday", "time_slot": "8:00-9:00"}]

    summary = build_day_plan_summary(day_events, timetable_entries, "Monday")

    assert "1 event" in summary
    assert "1 class" in summary
    assert summary.endswith("Keep the day focused and manageable.") is False


def test_assignment_due_state_helpers():
    """Assignment cards should get clear due-state labels for urgent work."""
    from modules.assignments.assignments import get_due_state_label

    assert get_due_state_label("2026-07-26") == "Due today"
    assert get_due_state_label("2026-07-27") == "Due tomorrow"
    assert get_due_state_label("2026-08-02") == "Due soon"
    assert get_due_state_label(None) == "No due date"


def test_settings_preference_parsing():
    """Settings preferences should resolve common boolean values reliably."""
    from modules.settings.settings import parse_preference_value

    assert parse_preference_value(None, False) is False
    assert parse_preference_value("true", False) is True
    assert parse_preference_value("false", True) is False
    assert parse_preference_value("1", False) is True


def test_dashboard_section_visibility_logic():
    """Dashboard sections should honor stored preference values."""
    from modules.dashboard.dashboard import should_show_dashboard_section

    assert should_show_dashboard_section(None, True) is True
    assert should_show_dashboard_section("false", True) is False
    assert should_show_dashboard_section("1", False) is True


def test_planner_focus_summary_integration():
    """Planner summaries should combine classes and calendar events for the same day."""
    from modules.timetable.timetable import build_planner_focus_summary

    summary = build_planner_focus_summary([{"day": "Monday"}], [{"title": "Review"}])
    assert "1 class" in summary
    assert "1 event" in summary


def test_database_connection():
    """Test database connection and initialization"""
    print("Testing database connection...")
    try:
        initialize_database()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✓ Database connected. Found {len(tables)} tables.")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_student_profile():
    """Test student profile CRUD operations"""
    print("\nTesting student profile...")
    try:
        # Create profile
        create_student_profile(
            name="Test Student",
            enrollment_number="TEST123",
            department="Computer Science",
            semester=3
        )
        print("✓ Profile created")
        
        # Read profile
        profile = get_student_profile()
        if profile is None:
            print("✗ Profile is None after creation")
            return False
        print(f"✓ Profile read: {profile.get('name', 'N/A')}")
        
        # Update profile
        update_student_profile(
            profile_id=profile['id'],
            name="Updated Student",
            semester=4
        )
        updated = get_student_profile()
        if updated['name'] != "Updated Student":
            print(f"✗ Profile update failed: expected 'Updated Student', got '{updated['name']}'")
            return False
        print("✓ Profile updated successfully")
        
        return True
    except Exception as e:
        print(f"✗ Student profile test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_subjects():
    """Test subject CRUD operations"""
    print("\nTesting subjects...")
    try:
        # Create subject
        subject_id = add_subject(
            name="Data Structures",
            subject_code="CS201",
            faculty_name="Dr. Smith",
            semester=3,
            credit=4,
            color="#4F8EF7"
        )
        print("✓ Subject created")
        
        # Read subjects
        subjects = get_subjects()
        assert len(subjects) > 0
        print(f"✓ Found {len(subjects)} subjects")
        
        # Update subject
        update_subject(
            subject_id=subject_id,
            name="Advanced Data Structures"
        )
        updated = get_subjects()
        assert any(s['name'] == "Advanced Data Structures" for s in updated)
        print("✓ Subject updated successfully")
        
        # Delete subject
        delete_subject(subject_id)
        subjects_after = get_subjects()
        assert not any(s['id'] == subject_id for s in subjects_after)
        print("✓ Subject deleted successfully")
        
        return True
    except Exception as e:
        print(f"✗ Subjects test failed: {e}")
        return False


def test_notes():
    """Test notes CRUD operations"""
    print("\nTesting notes...")
    try:
        # Create a subject first
        subject_id = add_subject(name="Test Subject", semester=1)
        
        # Create note
        note_id = create_note(
            subject_id=subject_id,
            title="Test Note",
            content="This is a test note content."
        )
        print("✓ Note created")
        
        # Read notes
        notes = get_notes(subject_id)
        assert len(notes) > 0
        print(f"✓ Found {len(notes)} notes")
        
        # Update note
        update_note(
            note_id=note_id,
            title="Updated Note",
            content="Updated content."
        )
        print("✓ Note updated successfully")
        
        # Delete note
        delete_note(note_id)
        notes_after = get_notes(subject_id)
        assert not any(n['id'] == note_id for n in notes_after)
        print("✓ Note deleted successfully")
        
        # Cleanup
        delete_subject(subject_id)
        
        return True
    except Exception as e:
        print(f"✗ Notes test failed: {e}")
        return False


def test_note_pin_and_duplicate():
    """Test note duplication, pinning, and sort support"""
    print("\nTesting notes advanced features...")
    try:
        subject_id = add_subject(name="Notes Subject", semester=1)
        note_id = create_note(subject_id=subject_id, title="Draft Note", content="Draft content")

        duplicate_id = duplicate_note(note_id, title="Copy of Draft Note")
        assert duplicate_id is not None
        duplicate_note_data = get_note_by_id(duplicate_id)
        assert duplicate_note_data is not None
        assert duplicate_note_data['title'] == "Copy of Draft Note"
        assert duplicate_note_data['content'] == "Draft content"

        updated = update_note(note_id, is_pinned=True)
        assert updated is True
        pinned_note = get_note_by_id(note_id)
        assert pinned_note['is_pinned'] == 1

        notes = get_notes(subject_id, sort_by="title")
        assert len(notes) >= 2
        assert notes[0]['title'] <= notes[-1]['title']

        delete_note(note_id)
        delete_note(duplicate_id)
        delete_subject(subject_id)
        print("✓ Note duplication, pinning, and sorting work")
        return True
    except Exception as e:
        print(f"✗ Notes advanced features test failed: {e}")
        return False


def test_file_manager_sorting_and_icons():
    """Test file sort order and file type icon mapping."""
    print("\nTesting file manager helpers...")
    try:
        files = [
            {"file_name": "zeta.pdf", "file_type": "PDF", "file_size": "2 KB"},
            {"file_name": "alpha.py", "file_type": "PY", "file_size": "1 KB"},
            {"file_name": "middle.docx", "file_type": "DOCX", "file_size": "3 KB"},
        ]

        sorted_files = file_manager.sort_files(files, sort_by="name")
        assert [f["file_name"] for f in sorted_files] == ["alpha.py", "middle.docx", "zeta.pdf"]

        assert file_manager.get_file_type_icon("notes.py") == "🐍"
        assert file_manager.get_file_type_icon("report.pdf") == "📄"
        print("✓ File sorting and icons work")
        return True
    except Exception as e:
        print(f"✗ File manager helper test failed: {e}")
        return False


def test_timetable_highlighting_helpers():
    """Test timetable highlighting helpers for current day and current class."""
    print("\nTesting timetable helpers...")
    try:
        today = datetime.now().strftime("%A")
        from modules.timetable.timetable import Timetable
        timetable = Timetable.__new__(Timetable)
        timetable.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        timetable.time_slots = ["8:00-9:00"]
        timetable.subjects_data = [{"id": 1, "name": "Math", "color": "#4F8EF7"}]
        entry = {"subject_id": 1, "day": today, "time_slot": "8:00-9:00"}
        color = timetable._get_subject_color(entry)
        assert color == "#4F8EF7"
        assert timetable._is_current_day(today) is True
        assert timetable._is_current_class(entry) is True
        print("✓ Timetable highlighting helpers work")
        return True
    except Exception as e:
        print(f"✗ Timetable helper test failed: {e}")
        return False


def test_attendance_visual_helpers():
    """Test attendance percentage and warning-state helpers."""
    print("\nTesting attendance helpers...")
    try:
        from modules.subjects.workspace import SubjectWorkspace
        workspace = SubjectWorkspace.__new__(SubjectWorkspace)
        workspace.subject_id = 1
        percentage = 72.0
        assert workspace._get_attendance_color(percentage) == "#FFC107"
        assert workspace._is_attendance_warning(percentage) is True
        assert workspace._format_percentage(percentage) == "72.0%"
        print("✓ Attendance visual helpers work")
        return True
    except Exception as e:
        print(f"✗ Attendance helper test failed: {e}")
        return False


def test_attendance():
    """Test attendance operations"""
    print("\nTesting attendance...")
    try:
        # Create a subject first
        subject_id = add_subject(name="Test Subject", semester=1)
        
        # Update attendance
        update_attendance(
            subject_id=subject_id,
            total_lectures=10,
            present_lectures=8
        )
        print("✓ Attendance updated")
        
        # Read attendance
        attendance = get_attendance(subject_id)
        assert attendance is not None
        assert attendance['total_lectures'] == 10
        assert attendance['present_lectures'] == 8
        print("✓ Attendance read successfully")
        
        # Calculate percentage
        percentage = calculate_attendance_percentage(subject_id)
        assert percentage == 80.0
        print(f"✓ Attendance percentage calculated: {percentage}%")
        
        # Cleanup
        delete_subject(subject_id)
        
        return True
    except Exception as e:
        print(f"✗ Attendance test failed: {e}")
        return False


def test_settings_round_trip():
    """Test settings serialization for structured values like study streak data."""
    print("\nTesting settings...")
    payload = {
        "current_streak": 2,
        "last_study_date": "2026-07-25",
        "longest_streak": 3,
    }
    set_setting("study_streak", payload)
    stored = get_setting("study_streak")
    assert isinstance(stored, dict), "Stored value is not a dict"
    assert stored["current_streak"] == 2, "Current streak mismatch"
    assert stored["longest_streak"] == 3, "Longest streak mismatch"
    print("✓ Settings round trip works")


def test_assignments():
    """Test assignment CRUD operations"""
    print("\nTesting assignments...")
    # Create a subject first
    subject_id = add_subject(name="Test Subject", semester=1)
    
    # Create assignment
    assignment_id = add_assignment(
        subject_id=subject_id,
        title="Test Assignment",
        description="Test description",
        due_date="2024-12-31",
        priority="high",
        status="pending"
    )
    print("✓ Assignment created")
    
    # Read assignments
    assignments = get_assignments(subject_id)
    assert len(assignments) > 0, "No assignments found"
    print(f"✓ Found {len(assignments)} assignments")
    
    # Update assignment
    update_assignment(
        assignment_id=assignment_id,
        status="completed"
    )
    print("✓ Assignment updated successfully")
    
    # Delete assignment
    delete_assignment(assignment_id)
    assignments_after = get_assignments(subject_id)
    assert not any(a['id'] == assignment_id for a in assignments_after), "Assignment deletion failed"
    print("✓ Assignment deleted successfully")
    
    # Cleanup
    delete_subject(subject_id)


def test_timetable():
    """Test timetable CRUD operations"""
    print("\nTesting timetable...")
    # Create a subject first
    subject_id = add_subject(name="Test Subject", semester=1)
    
    # Create timetable entry
    entry_id = add_timetable_entry(
        day="Monday",
        time_slot="9:00-10:00",
        subject_id=subject_id,
        classroom="Room 101"
    )
    print("✓ Timetable entry created")
    
    # Read timetable
    timetable = get_timetable()
    assert len(timetable) > 0, "No timetable entries found"
    print(f"✓ Found {len(timetable)} timetable entries")
    
    # Update entry
    update_timetable_entry(
        entry_id=entry_id,
        classroom="Room 102"
    )
    print("✓ Timetable entry updated successfully")
    
    # Delete entry
    delete_timetable_entry(entry_id)
    timetable_after = get_timetable()
    assert not any(e['id'] == entry_id for e in timetable_after), "Timetable entry deletion failed"
    print("✓ Timetable entry deleted successfully")
    
    # Cleanup
    delete_subject(subject_id)


def test_cgpa():
    """Test CGPA CRUD operations"""
    print("\nTesting CGPA...")
    # Create CGPA record
    record_id = add_cgpa_record(
        semester=1,
        gpa=3.5,
        credits=20
    )
    print("✓ CGPA record created")
    
    # Read records
    records = get_cgpa_records()
    assert len(records) > 0, "No CGPA records found"
    print(f"✓ Found {len(records)} CGPA records")
    
    # Calculate CGPA
    cgpa = calculate_cgpa()
    assert cgpa == 3.5, f"CGPA calculation failed: expected 3.5, got {cgpa}"
    print(f"✓ CGPA calculated: {cgpa}")
    
    # Update record
    update_cgpa_record(
        record_id=record_id,
        gpa=3.8
    )
    print("✓ CGPA record updated successfully")
    
    # Delete record
    delete_cgpa_record(record_id)
    records_after = get_cgpa_records()
    assert not any(r['id'] == record_id for r in records_after), "CGPA record deletion failed"
    print("✓ CGPA record deleted successfully")


def test_backup_and_export():
    """Test full JSON database backup export/import and CSV export."""
    from database.backup_manager import export_full_backup, import_full_backup, export_attendance_csv
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as json_tmp:
        json_path = json_tmp.name
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as csv_tmp:
        csv_path = csv_tmp.name
        
    try:
        ok, msg = export_full_backup(json_path)
        assert ok is True, f"Backup export failed: {msg}"
        print("✓ JSON database export succeeded")

        ok, msg = import_full_backup(json_path)
        assert ok is True, f"Backup import failed: {msg}"
        print("✓ JSON database import succeeded")

        ok, msg = export_attendance_csv(csv_path)
        assert ok is True, f"CSV export failed: {msg}"
        print("✓ CSV attendance export succeeded")
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)
        if os.path.exists(csv_path):
            os.remove(csv_path)


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("StudyFlow Application Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Student Profile", test_student_profile),
        ("Subjects", test_subjects),
        ("Notes", test_notes),
        ("Attendance", test_attendance),
        ("Assignments", test_assignments),
        ("Timetable", test_timetable),
        ("CGPA", test_cgpa),
        ("Backup and Export", test_backup_and_export),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, True))
        except AssertionError as e:
            print(f"✗ {name} test failed: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"✗ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
