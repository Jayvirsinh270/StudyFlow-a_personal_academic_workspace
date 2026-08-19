"""
StudyFlow Web Application
Flask backend serving the HTML/CSS/JS frontend
All database logic is imported directly from the existing database layer
"""

import os
import sys
import json
import shutil
from datetime import datetime, date, timedelta
from flask import Flask, render_template, jsonify, request, send_from_directory

# Ensure project root is on path so database imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    initialize_database,
    get_student_profile, create_student_profile, update_student_profile,
    get_subjects, get_subject_by_id, add_subject, update_subject, delete_subject,
    get_assignments, add_assignment, update_assignment, delete_assignment,
    get_attendance, update_attendance, calculate_attendance_percentage,
    get_timetable, get_timetable_by_day, add_timetable_entry, update_timetable_entry, delete_timetable_entry,
    get_notes, get_note_by_id, create_note, update_note, delete_note, duplicate_note,
    get_subject_files, add_subject_file, delete_subject_file, update_subject_file,
    get_cgpa_records, add_cgpa_record, update_cgpa_record, delete_cgpa_record, calculate_cgpa,
    get_calendar_events, add_calendar_event, update_calendar_event, delete_calendar_event,
    get_study_tasks, add_study_task, update_study_task, delete_study_task,
    get_setting, set_setting
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "studyflow-secret-2024"

# ─── helpers ──────────────────────────────────────────────────────────────────

def ok(data):
    return jsonify({"data": data, "error": None})

def err(message, status=400):
    return jsonify({"data": None, "error": message}), status

def today_str():
    return date.today().isoformat()

# ─── page routes ──────────────────────────────────────────────────────────────

def render_page(template, page):
    """Render full page or just the content block for SPA partial loads."""
    partial = request.args.get("partial") == "1"
    if partial:
        # Render only the block content (no shell)
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), "templates")
        ))
        tmpl = env.get_template(template)
        # Extract content block only
        full = tmpl.render(page=page)
        # For partial: return inner content wrapped in page-content div
        return f'<div class="page-content page-enter">{_extract_block(template, page)}</div>'
    return render_template(template, page=page)

def _extract_block(template_name, page):
    """Render a template and extract the content block body."""
    from jinja2 import Environment, FileSystemLoader, meta
    tmpl_path = os.path.join(os.path.dirname(__file__), "templates", template_name)
    with open(tmpl_path, "r", encoding="utf-8") as f:
        src = f.read()
    # Extract between {% block content %} ... {% endblock %}
    import re
    match = re.search(r'\{%[-\s]*block content[-\s]*%\}(.*?)\{%[-\s]*endblock[-\s]*%\}', src, re.DOTALL)
    if match:
        block_body = match.group(1)
        # Also extract scripts block
        scripts_match = re.search(r'\{%[-\s]*block scripts[-\s]*%\}(.*?)\{%[-\s]*endblock[-\s]*%\}', src, re.DOTALL)
        scripts = scripts_match.group(1) if scripts_match else ""
        return block_body + scripts
    return src

@app.route("/")
@app.route("/dashboard")
def dashboard():
    return render_page("dashboard.html", "dashboard")

@app.route("/subjects")
def subjects():
    return render_page("subjects.html", "subjects")

@app.route("/assignments")
def assignments_page():
    return render_page("assignments.html", "assignments")

@app.route("/attendance")
def attendance_page():
    return render_page("attendance.html", "attendance")

@app.route("/timetable")
def timetable_page():
    return render_page("timetable.html", "timetable")

@app.route("/planner")
def planner_page():
    return render_page("planner.html", "planner")

@app.route("/calendar")
def calendar_page():
    return render_page("calendar.html", "calendar")

@app.route("/pomodoro")
def pomodoro_page():
    return render_page("pomodoro.html", "pomodoro")

@app.route("/cgpa")
def cgpa_page():
    return render_page("cgpa.html", "cgpa")

@app.route("/documents")
def documents_page():
    return render_page("documents.html", "documents")

@app.route("/notes")
def notes_page():
    return render_page("notes.html", "notes")

@app.route("/settings")
def settings_page():
    return render_page("settings.html", "settings")

# ─── API: profile ─────────────────────────────────────────────────────────────

@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    try:
        profile = get_student_profile()
        return ok(profile or {})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/profile", methods=["POST"])
def api_save_profile():
    try:
        data = request.get_json() or {}
        profile = get_student_profile()
        name = data.get("name", "")
        enrollment = data.get("enrollment_number", "")
        department = data.get("department", "")
        semester = data.get("semester")
        if semester:
            try:
                semester = int(semester)
            except Exception:
                semester = None
        if profile:
            update_student_profile(
                profile["id"], name=name or None,
                enrollment_number=enrollment or None,
                department=department or None,
                semester=semester
            )
        else:
            create_student_profile(name, enrollment, department, semester)
        return ok(get_student_profile())
    except Exception as e:
        return err(str(e), 500)

# ─── API: subjects ─────────────────────────────────────────────────────────────

@app.route("/api/subjects", methods=["GET"])
def api_subjects():
    try:
        return ok(get_subjects())
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/subjects", methods=["POST"])
def api_add_subject():
    try:
        d = request.get_json() or {}
        sid = add_subject(
            d.get("name", ""), d.get("subject_code"),
            d.get("faculty_name"), d.get("semester"), d.get("credit"), d.get("color")
        )
        return ok(get_subject_by_id(sid))
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/subjects/<int:sid>", methods=["PUT"])
def api_update_subject(sid):
    try:
        d = request.get_json() or {}
        update_subject(sid, **{k: v for k, v in d.items() if k in
            ["name","subject_code","faculty_name","semester","credit","color"]})
        return ok(get_subject_by_id(sid))
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/subjects/<int:sid>", methods=["DELETE"])
def api_delete_subject(sid):
    try:
        delete_subject(sid)
        return ok({"deleted": sid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/subjects/<int:sid>/detail", methods=["GET"])
def api_subject_detail(sid):
    """Return everything about a single subject in one call."""
    try:
        subj = get_subject_by_id(sid)
        if not subj:
            return err("Subject not found", 404)

        # Assignments for this subject
        assignments = get_assignments(subject_id=sid)
        pending   = [a for a in assignments if a.get("status") == "pending"]
        completed = [a for a in assignments if a.get("status") == "completed"]

        # Attendance
        att = get_attendance(sid) or {}
        present = att.get("present_lectures", 0) or 0
        total   = att.get("total_lectures",   0) or 0
        pct     = round((present / total * 100) if total > 0 else 0, 1)

        # Timetable slots for this subject
        tt_rows = get_timetable()
        tt_slots = [r for r in tt_rows if r.get("subject_id") == sid]

        # Notes for this subject
        notes = get_notes(subject_id=sid) if True else []

        # Files for this subject
        files = get_subject_files(subject_id=sid) if True else []

        return ok({
            "subject": subj,
            "assignments": {
                "all": assignments,
                "pending_count": len(pending),
                "completed_count": len(completed),
                "total": len(assignments),
            },
            "attendance": {
                "present": present,
                "total": total,
                "absent": total - present,
                "percentage": pct,
            },
            "timetable": tt_slots,
            "notes": notes,
            "files": files,
        })
    except Exception as e:
        return err(str(e), 500)

# ─── API: assignments ─────────────────────────────────────────────────────────

@app.route("/api/assignments", methods=["GET"])
def api_assignments():
    try:
        subject_id = request.args.get("subject_id", type=int)
        status = request.args.get("status")
        rows = get_assignments(subject_id=subject_id, status=status if status != "all" else None)
        # enrich with subject name
        subjects_map = {s["id"]: s for s in get_subjects()}
        for r in rows:
            r["subject_name"] = subjects_map.get(r.get("subject_id"), {}).get("name", "")
            r["subject_color"] = subjects_map.get(r.get("subject_id"), {}).get("color", "#6366F1")
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/assignments", methods=["POST"])
def api_add_assignment():
    try:
        d = request.get_json() or {}
        aid = add_assignment(
            d.get("subject_id"), d.get("title", ""),
            d.get("description"), d.get("due_date"),
            d.get("priority", "medium"), d.get("status", "pending")
        )
        rows = get_assignments()
        subjects_map = {s["id"]: s for s in get_subjects()}
        for r in rows:
            if r["id"] == aid:
                r["subject_name"] = subjects_map.get(r.get("subject_id"), {}).get("name", "")
                r["subject_color"] = subjects_map.get(r.get("subject_id"), {}).get("color", "#6366F1")
                return ok(r)
        return ok({"id": aid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/assignments/<int:aid>", methods=["PUT"])
def api_update_assignment(aid):
    try:
        d = request.get_json() or {}
        update_assignment(aid, **{k: v for k, v in d.items() if k in
            ["title","description","due_date","priority","status"]})
        return ok({"updated": aid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/assignments/<int:aid>", methods=["DELETE"])
def api_delete_assignment(aid):
    try:
        delete_assignment(aid)
        return ok({"deleted": aid})
    except Exception as e:
        return err(str(e), 500)

# ─── API: attendance ──────────────────────────────────────────────────────────

@app.route("/api/attendance/summary", methods=["GET"])
def api_attendance_summary():
    try:
        subjects = get_subjects()
        result = []
        total_present = total_lectures = 0
        for s in subjects:
            att = get_attendance(s["id"]) or {}
            present = att.get("present_lectures", 0) or 0
            total = att.get("total_lectures", 0) or 0
            absent = att.get("absent_lectures", 0) or 0
            pct = round((present / total * 100) if total > 0 else 0, 1)
            total_present += present
            total_lectures += total
            result.append({
                "subject_id": s["id"],
                "subject_name": s["name"],
                "subject_color": s.get("color", "#6366F1"),
                "present": present,
                "absent": absent,
                "total": total,
                "percentage": pct
            })
        overall = round((total_present / total_lectures * 100) if total_lectures > 0 else 0, 1)
        return ok({"subjects": result, "overall": overall,
                   "total_present": total_present, "total_lectures": total_lectures})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/attendance/<int:sid>", methods=["PUT"])
def api_update_attendance(sid):
    try:
        d = request.get_json() or {}
        update_attendance(
            sid,
            total_lectures=d.get("total_lectures"),
            present_lectures=d.get("present_lectures"),
            absent_lectures=d.get("absent_lectures")
        )
        att = get_attendance(sid) or {}
        return ok(att)
    except Exception as e:
        return err(str(e), 500)

# ─── API: timetable ───────────────────────────────────────────────────────────

@app.route("/api/timetable", methods=["GET"])
def api_timetable():
    try:
        day = request.args.get("day")
        rows = get_timetable_by_day(day) if day else get_timetable()
        subjects_map = {s["id"]: s for s in get_subjects()}
        for r in rows:
            subj = subjects_map.get(r.get("subject_id"), {})
            r["subject_color"] = subj.get("color", "#6366F1")
            if not r.get("subject_name"):
                r["subject_name"] = subj.get("name", "")
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/timetable", methods=["POST"])
def api_add_timetable():
    try:
        d = request.get_json() or {}
        tid = add_timetable_entry(
            d.get("day", ""), d.get("time_slot", ""),
            d.get("subject_id"), d.get("faculty_name"),
            d.get("classroom"), d.get("remarks")
        )
        return ok({"id": tid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/timetable/<int:tid>", methods=["PUT"])
def api_update_timetable(tid):
    try:
        d = request.get_json() or {}
        update_timetable_entry(tid, **{k: v for k, v in d.items() if k in
            ["day","time_slot","subject_id","faculty_name","classroom","remarks"]})
        return ok({"updated": tid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/timetable/<int:tid>", methods=["DELETE"])
def api_delete_timetable(tid):
    try:
        delete_timetable_entry(tid)
        return ok({"deleted": tid})
    except Exception as e:
        return err(str(e), 500)

# ─── API: notes ───────────────────────────────────────────────────────────────

@app.route("/api/notes", methods=["GET"])
def api_notes():
    try:
        subject_id = request.args.get("subject_id", type=int)
        rows = get_notes(subject_id=subject_id)
        subjects_map = {s["id"]: s for s in get_subjects()}
        for r in rows:
            subj = subjects_map.get(r.get("subject_id"), {})
            r["subject_name"] = subj.get("name", "")
            r["subject_color"] = subj.get("color", "#6366F1")
        return ok(rows)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/notes", methods=["POST"])
def api_add_note():
    try:
        d = request.get_json() or {}
        nid = create_note(d.get("subject_id"), d.get("title", "Untitled"), d.get("content", ""))
        return ok(get_note_by_id(nid))
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/notes/<int:nid>", methods=["PUT"])
def api_update_note(nid):
    try:
        d = request.get_json() or {}
        update_note(nid,
            title=d.get("title"),
            content=d.get("content"),
            is_pinned=d.get("is_pinned")
        )
        return ok(get_note_by_id(nid))
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/notes/<int:nid>", methods=["DELETE"])
def api_delete_note(nid):
    try:
        delete_note(nid)
        return ok({"deleted": nid})
    except Exception as e:
        return err(str(e), 500)

# ─── API: CGPA ────────────────────────────────────────────────────────────────

@app.route("/api/cgpa", methods=["GET"])
def api_cgpa():
    try:
        records = get_cgpa_records()
        cgpa = calculate_cgpa()
        return ok({"records": records, "cgpa": round(cgpa, 2)})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/cgpa", methods=["POST"])
def api_add_cgpa():
    try:
        d = request.get_json() or {}
        rid = add_cgpa_record(d.get("semester"), d.get("gpa"), d.get("credits"))
        return ok({"id": rid, "cgpa": round(calculate_cgpa(), 2)})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/cgpa/<int:rid>", methods=["DELETE"])
def api_delete_cgpa(rid):
    try:
        delete_cgpa_record(rid)
        return ok({"deleted": rid, "cgpa": round(calculate_cgpa(), 2)})
    except Exception as e:
        return err(str(e), 500)

# ─── API: calendar events ─────────────────────────────────────────────────────

@app.route("/api/calendar-events", methods=["GET"])
def api_calendar_events():
    try:
        events = get_calendar_events()
        # convert to FullCalendar format
        fc_events = []
        type_colors = {
            "personal": "#3B82F6",
            "academic": "#6366F1",
            "exam": "#EF4444",
            "holiday": "#22C55E",
            "reminder": "#F59E0B"
        }
        for e in events:
            fc_events.append({
                "id": e["id"],
                "title": e["title"],
                "start": e["event_date"],
                "backgroundColor": type_colors.get(e.get("event_type", "personal"), "#3B82F6"),
                "borderColor": type_colors.get(e.get("event_type", "personal"), "#3B82F6"),
                "extendedProps": {
                    "type": e.get("event_type"),
                    "description": e.get("description")
                }
            })
        return ok(fc_events)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/calendar-events", methods=["POST"])
def api_add_calendar_event():
    try:
        d = request.get_json() or {}
        eid = add_calendar_event(d.get("title", ""), d.get("event_date", ""), d.get("event_type", "personal"), d.get("description"))
        return ok({"id": eid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/calendar-events/<int:eid>", methods=["PUT"])
def api_update_calendar_event(eid):
    try:
        d = request.get_json() or {}
        update_calendar_event(eid, **{k: v for k, v in d.items() if k in
            ["title","event_date","event_type","description"]})
        return ok({"updated": eid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/calendar-events/<int:eid>", methods=["DELETE"])
def api_delete_calendar_event(eid):
    try:
        delete_calendar_event(eid)
        return ok({"deleted": eid})
    except Exception as e:
        return err(str(e), 500)

# ─── API: planner (study tasks) ───────────────────────────────────────────────

@app.route("/api/planner", methods=["GET"])
def api_planner():
    try:
        date_filter = request.args.get("date")
        tasks = get_study_tasks()
        if date_filter:
            tasks = [t for t in tasks if t.get("due_date", "")[:10] == date_filter]
        return ok(tasks)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/planner", methods=["POST"])
def api_add_planner_task():
    try:
        d = request.get_json() or {}
        tid = add_study_task(d.get("title",""), d.get("task_type","daily"),
                             d.get("description"), d.get("due_date"), d.get("status","pending"))
        return ok({"id": tid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/planner/<int:tid>", methods=["PUT"])
def api_update_planner_task(tid):
    try:
        d = request.get_json() or {}
        update_study_task(tid, **{k: v for k, v in d.items() if k in
            ["title","task_type","description","due_date","status"]})
        return ok({"updated": tid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/planner/<int:tid>", methods=["DELETE"])
def api_delete_planner_task(tid):
    try:
        delete_study_task(tid)
        return ok({"deleted": tid})
    except Exception as e:
        return err(str(e), 500)

# ─── API: documents ───────────────────────────────────────────────────────────

@app.route("/api/documents", methods=["GET"])
def api_documents():
    try:
        subject_id = request.args.get("subject_id", type=int)
        files = get_subject_files(subject_id=subject_id)
        subjects_map = {s["id"]: s for s in get_subjects()}
        for f in files:
            subj = subjects_map.get(f.get("subject_id"), {})
            f["subject_name"] = subj.get("name", "")
            f["subject_color"] = subj.get("color", "#6366F1")
        return ok(files)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/documents/upload", methods=["POST"])
def api_upload_document():
    """Accept either a multipart file upload or a local file path (pywebview)."""
    try:
        user_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "UserData"
        )
        os.makedirs(user_data_dir, exist_ok=True)

        subject_id = request.form.get("subject_id", type=int)

        # ── Path-based upload (pywebview native dialog) ──────────────────────
        local_path = request.form.get("local_path", "").strip()
        if local_path:
            if not os.path.isfile(local_path):
                return err("File not found on disk")
            file_name = os.path.basename(local_path)
            dest = os.path.join(user_data_dir, file_name)
            if os.path.abspath(local_path) != os.path.abspath(dest):
                shutil.copy2(local_path, dest)
            ext = os.path.splitext(file_name)[1].lower()
            file_type = _ext_to_type(ext)
            size = os.path.getsize(dest)
            fid = add_subject_file(subject_id, file_name, dest, file_type, size)
            return ok({"id": fid, "file_name": file_name, "file_path": dest})

        # ── Multipart upload (browser <input type="file">) ───────────────────
        if "file" not in request.files:
            return err("No file provided")
        file = request.files["file"]
        if not file.filename:
            return err("Empty filename")
        dest = os.path.join(user_data_dir, file.filename)
        file.save(dest)
        ext = os.path.splitext(file.filename)[1].lower()
        file_type = _ext_to_type(ext)
        size = os.path.getsize(dest)
        fid = add_subject_file(subject_id, file.filename, dest, file_type, size)
        return ok({"id": fid, "file_name": file.filename, "file_path": dest})
    except Exception as e:
        return err(str(e), 500)


def _ext_to_type(ext: str) -> str:
    return {
        ".pdf": "PDF",
        ".jpg": "Image", ".jpeg": "Image", ".png": "Image",
        ".gif": "Image", ".webp": "Image", ".bmp": "Image",
        ".doc": "Word", ".docx": "Word",
        ".ppt": "PPT", ".pptx": "PPT",
        ".xls": "Excel", ".xlsx": "Excel",
        ".txt": "Text", ".md": "Text",
        ".mp4": "Video", ".mp3": "Audio",
        ".zip": "Archive", ".rar": "Archive",
    }.get(ext, "Other")

@app.route("/api/documents/<int:fid>", methods=["DELETE"])
def api_delete_document(fid):
    try:
        delete_subject_file(fid)
        return ok({"deleted": fid})
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/documents/open/<int:fid>", methods=["POST"])
def api_open_document(fid):
    try:
        files = get_subject_files()
        f = next((x for x in files if x["id"] == fid), None)
        if not f:
            return err("File not found", 404)
        path = f.get("file_path", "")
        if os.path.exists(path):
            os.startfile(path)
            return ok({"opened": path})
        return err("File not found on disk", 404)
    except Exception as e:
        return err(str(e), 500)

# ─── API: settings ────────────────────────────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    try:
        return ok({
            "theme_mode": get_setting("theme_mode") or "dark"
        })
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    try:
        d = request.get_json() or {}
        for key, value in d.items():
            set_setting(key, value)
        return ok({"saved": True})
    except Exception as e:
        return err(str(e), 500)

# ─── API: dashboard stats ─────────────────────────────────────────────────────

@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    try:
        subjects = get_subjects()
        all_assignments = get_assignments()
        pending_assignments = [a for a in all_assignments if a.get("status") == "pending"]

        # today's timetable
        today_day = date.today().strftime("%A")
        today_classes = get_timetable_by_day(today_day)
        subjects_map = {s["id"]: s for s in subjects}
        for c in today_classes:
            subj = subjects_map.get(c.get("subject_id"), {})
            c["subject_color"] = subj.get("color", "#6366F1")
            if not c.get("subject_name"):
                c["subject_name"] = subj.get("name", "Unknown")

        # attendance summary
        total_present = total_lectures = 0
        for s in subjects:
            att = get_attendance(s["id"]) or {}
            total_present += att.get("present_lectures", 0) or 0
            total_lectures += att.get("total_lectures", 0) or 0
        overall_attendance = round((total_present / total_lectures * 100) if total_lectures > 0 else 0, 1)

        # CGPA
        cgpa = round(calculate_cgpa(), 2)
        cgpa_records = get_cgpa_records()

        # due soon (next 7 days)
        today = date.today()
        due_soon = []
        for a in all_assignments:
            if a.get("status") in ("pending", "in_progress") and a.get("due_date"):
                try:
                    due = datetime.strptime(a["due_date"][:10], "%Y-%m-%d").date()
                    days_left = (due - today).days
                    if -1 <= days_left <= 7:
                        a["days_left"] = days_left
                        a["subject_name"] = subjects_map.get(a.get("subject_id"), {}).get("name", "")
                        a["subject_color"] = subjects_map.get(a.get("subject_id"), {}).get("color", "#6366F1")
                        due_soon.append(a)
                except Exception:
                    pass
        due_soon.sort(key=lambda x: x.get("due_date", ""))

        # recent notes
        all_notes = get_notes()
        for n in all_notes:
            subj = subjects_map.get(n.get("subject_id"), {})
            n["subject_name"] = subj.get("name", "")
            n["subject_color"] = subj.get("color", "#6366F1")
        recent_notes = all_notes[:4]

        return ok({
            "subject_count": len(subjects),
            "pending_count": len(pending_assignments),
            "today_class_count": len(today_classes),
            "overall_attendance": overall_attendance,
            "cgpa": cgpa,
            "cgpa_records": cgpa_records,
            "today_classes": today_classes,
            "due_soon": due_soon[:6],
            "recent_notes": recent_notes
        })
    except Exception as e:
        return err(str(e), 500)

# ─── API: global search ───────────────────────────────────────────────────────

@app.route("/api/search", methods=["GET"])
def api_search():
    try:
        q = (request.args.get("q") or "").strip().lower()
        if not q:
            return ok([])
        results = []
        for s in get_subjects():
            if q in s.get("name", "").lower() or q in (s.get("subject_code") or "").lower():
                results.append({"type": "subject", "id": s["id"], "title": s["name"],
                                 "subtitle": s.get("subject_code", ""), "url": "/subjects"})
        for a in get_assignments():
            if q in a.get("title", "").lower():
                results.append({"type": "assignment", "id": a["id"], "title": a["title"],
                                 "subtitle": a.get("due_date", ""), "url": "/assignments"})
        for n in get_notes():
            if q in n.get("title", "").lower() or q in (n.get("content") or "").lower():
                results.append({"type": "note", "id": n["id"], "title": n["title"],
                                 "subtitle": "", "url": "/notes"})
        for f in get_subject_files():
            if q in f.get("file_name", "").lower():
                results.append({"type": "file", "id": f["id"], "title": f["file_name"],
                                 "subtitle": f.get("file_type", ""), "url": "/documents"})
        return ok(results[:12])
    except Exception as e:
        return err(str(e), 500)

# ─── error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"data": None, "error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"data": None, "error": str(e)}), 500


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, port=5000)
