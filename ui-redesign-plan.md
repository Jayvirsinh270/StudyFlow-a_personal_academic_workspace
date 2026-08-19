# StudyFlow UI/UX Redesign Plan
## Flask + pywebview — Web-Grade Desktop UI

---

## Top-Level Overview

**Goal**: Replace the current CustomTkinter widget-based UI with a full web-grade HTML/CSS/JS frontend powered by Flask as the backend API and `pywebview` as the native desktop window. The Python backend (database, queries, business logic) stays 100% intact — only the presentation layer is replaced.

**Scope**: All 12 modules (Dashboard, Subjects, Assignments, Attendance, Planner, Timetable, Calendar, Pomodoro, CGPA, Documents, Settings, Notes) + Header + Sidebar.

**Approach**:
- Flask serves HTML pages and JSON API endpoints
- pywebview wraps Flask in a native desktop window (no browser needed)
- TailwindCSS + custom CSS for premium styling (glassmorphism, gradients, animations)
- Lucide Icons (CDN) for crisp SVG icon set
- Chart.js for interactive dashboard charts (replaces Matplotlib embeds)
- FullCalendar.js for the calendar module
- All existing `database/` code, `utils/` logic, and business rules are reused as-is

**Design Language**: "Academic Premium" — deep navy + electric blue gradient header, frosted glass sidebar, white/slate content cards, smooth page transitions, fluid micro-animations. Think Notion meets Linear meets a university portal.

---

## Architecture Overview

```
main.py (new)
├── starts Flask dev server on localhost:random_port
├── opens pywebview window pointing to Flask URL
└── shuts down Flask when window closes

web/
├── app.py                  ← Flask application + all API routes
├── templates/
│   ├── base.html           ← shell: sidebar + header + content slot
│   ├── dashboard.html
│   ├── subjects.html
│   ├── assignments.html
│   ├── attendance.html
│   ├── planner.html
│   ├── timetable.html
│   ├── calendar.html
│   ├── pomodoro.html
│   ├── cgpa.html
│   ├── documents.html
│   ├── settings.html
│   └── notes.html
└── static/
    ├── css/
    │   ├── main.css        ← Tailwind + custom design tokens
    │   └── animations.css  ← page transitions, micro-animations
    ├── js/
    │   ├── app.js          ← SPA router, fetch wrapper, theme toggle
    │   ├── dashboard.js
    │   ├── assignments.js
    │   ├── attendance.js
    │   ├── planner.js
    │   ├── calendar.js
    │   ├── pomodoro.js
    │   └── cgpa.js
    └── fonts/              ← Inter font (local copy for offline use)
```

The old `components/`, `modules/`, and `utils/theme.py` CustomTkinter code is kept but no longer loaded by the new `main.py`. The database layer (`database/`) is imported directly by Flask's `app.py`.

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding & Dependencies

**Intent**: Set up the new `web/` directory structure, install required packages, and verify the Flask+pywebview desktop window opens correctly with a placeholder page.

**Expected Outcomes**:
- `web/app.py` exists and runs
- `pywebview` opens a native desktop window showing "StudyFlow is loading…"
- New `main.py` starts Flask on a free port, opens pywebview, and cleanly shuts down on close
- `requirements.txt` updated with `flask`, `pywebview`, `waitress`

**Todo List**:
1. Add `flask`, `pywebview`, `waitress` to `pyproject.toml` / `requirements.txt`
2. Create `web/` directory with `app.py`, `templates/`, `static/css/`, `static/js/`, `static/fonts/`
3. Write `web/app.py` with a single `/` route returning a placeholder HTML page
4. Rewrite `main.py` to: find a free port → start Flask in a daemon thread (waitress) → open pywebview window → block until window closes → exit
5. Test: `python main.py` should open a native window with the placeholder

**Relevant Context**:
- Current `main.py` lines 50–127 (StudyFlowApp class) — replace entirely
- `database/__init__.py` — must be importable from `web/app.py`
- pywebview docs: `webview.create_window()` + `webview.start()`

**Status**: [x] done

---

### Sub-Task 2 — Design System & Base Shell (HTML/CSS)

**Intent**: Build the complete design token system, the `base.html` shell template (sidebar + header + content area), and global CSS. This defines the entire visual language for the app.

**Expected Outcomes**:
- `web/static/css/main.css` defines all color tokens, typography scale, spacing, card styles, button styles, input styles, badge styles using CSS custom properties
- `web/templates/base.html` contains the full sidebar + header layout using the new design system
- Sidebar shows all 12 navigation items with Lucide icons, grouped sections, active state, and a theme toggle
- Header shows app logo, breadcrumb, live clock, search bar, notification bell, profile chip
- The content slot (`<main>`) renders child page templates inside the shell
- Dark/light mode works via a single CSS class toggle on `<html>`

**Design Tokens** (CSS variables):
```css
--color-bg-base: #0D1117        /* dark base */
--color-bg-surface: #161B22     /* card surface */
--color-bg-sidebar: #0D1117     /* sidebar */
--color-accent: #2563EB         /* primary blue */
--color-accent-glow: rgba(37,99,235,0.3)
--color-text-primary: #F0F6FC
--color-text-muted: #8B949E
--color-border: rgba(255,255,255,0.08)
--color-success: #22C55E
--color-warning: #F59E0B
--color-danger: #EF4444
```

**Todo List**:
1. Create `web/static/css/main.css` with: CSS resets, design tokens (light+dark sets), typography scale (Inter font), spacing utilities, card component, button variants (primary, ghost, danger), input styles, badge/chip styles, scrollbar styles
2. Create `web/static/css/animations.css` with: page fade-in, sidebar hover slide, card hover lift, spinner, pulse badge
3. Download Inter font subset to `web/static/fonts/` for offline use
4. Create `web/templates/base.html` with: `<html>` tag with `data-theme`, `<head>` including CSS + Lucide CDN, sidebar nav (all 12 items + icons + groups + active class + theme toggle), header (logo, breadcrumb `<span id="page-title">`, search input, clock `<span id="clock">`, notification bell, profile chip), `<main id="content">` content slot using Jinja2 `{% block content %}`
5. Write `web/static/js/app.js` with: live clock updater, theme toggle (localStorage persist), sidebar active link highlighter, fetch helper with CSRF token support

**Relevant Context**:
- Current sidebar groups: MAIN (Dashboard, Subjects, Assignments, Attendance), TOOLS (Planner, Timetable, Calendar, Focus Timer), ACADEMIC (Documents, CGPA), SETTINGS
- Current header: breadcrumb, search, clock, notifications, profile — `components/header.py`
- Lucide Icons CDN: `https://unpkg.com/lucide@latest/dist/umd/lucide.min.js`

**Status**: [x] done

---

### Sub-Task 3 — Flask API Layer

**Intent**: Create all JSON API endpoints that the frontend JavaScript will call. This is the bridge between the existing Python database layer and the new web UI.

**Expected Outcomes**:
- `/api/profile` GET → student profile JSON
- `/api/subjects` GET/POST → list + create subjects
- `/api/subjects/<id>` PUT/DELETE → update + delete
- `/api/assignments` GET/POST → list (with filters) + create
- `/api/assignments/<id>` PUT/DELETE
- `/api/attendance` GET/POST → records + mark present/absent
- `/api/attendance/summary` GET → per-subject attendance %
- `/api/timetable` GET/POST/DELETE
- `/api/calendar-events` GET/POST/DELETE
- `/api/notes` GET/POST/PUT/DELETE
- `/api/cgpa` GET/POST/DELETE → semester records
- `/api/documents` GET/POST/DELETE → file records (subject_files table)
- `/api/planner` GET/POST/DELETE → planner tasks
- `/api/settings` GET/POST → key-value settings
- `/api/dashboard/stats` GET → aggregated stats for dashboard cards
- `/api/search` GET?q= → global search results
- All routes return `{ "data": ..., "error": null }` or `{ "data": null, "error": "message" }`

**Todo List**:
1. In `web/app.py` import all existing query functions from `database/queries.py`
2. Implement each API route group (subjects, assignments, attendance, timetable, calendar, notes, cgpa, documents, planner, settings, profile, search, dashboard stats)
3. Wrap all routes in try/except returning JSON error on failure
4. Add `/api/documents/upload` POST for file uploads (saves to UserData/, records in subject_files)
5. Add `/api/documents/open/<id>` GET to open file with `os.startfile` (Windows) or `subprocess.run(['open', path])` (macOS)
6. Register a Flask error handler for 404 and 500 returning JSON

**Relevant Context**:
- `database/queries.py` — all existing CRUD functions (reuse directly)
- `database/__init__.py` — `initialize_database`, `get_setting`, `set_setting`, `get_student_profile`, `get_subjects`
- Documents currently use `subject_files` table (not `documents` table) — confirmed by explorer agent
- File storage path: `UserData/` directory

**Status**: [x] done

---

### Sub-Task 4 — Dashboard Page

**Intent**: Build the dashboard HTML template and JS — the first page users see. It should look stunning: animated stat cards, a live CGPA ring, upcoming assignments list, today's timetable, and a weekly attendance bar chart.

**Expected Outcomes**:
- Dashboard loads at `/` and shows: 4 stat cards (subjects count, pending assignments, today's classes, overall attendance %), CGPA ring/arc visualization, "Today's Classes" timeline, "Due Soon" assignment list (next 7 days), "Recent Notes" feed
- Stat cards have icon, big number, label, and a subtle gradient glow
- CGPA shown as an SVG arc/donut with the number in the center
- Charts use Chart.js (attendance bars, CGPA trend line)
- All data fetched from `/api/dashboard/stats` on page load
- Empty states show friendly illustrations (CSS-only, no external images)

**Todo List**:
1. Create `web/templates/dashboard.html` extending `base.html` with full grid layout: top stats row (4 cards), middle row (CGPA ring + today's timetable), bottom row (assignments due soon + recent notes)
2. Create `web/static/js/dashboard.js` that: fetches `/api/dashboard/stats`, populates all stat cards, renders CGPA SVG arc, renders attendance Chart.js bar chart, renders timetable timeline, renders assignment list rows
3. Style: stat cards have top colored border (accent, success, warning, info), hover lifts with box-shadow, numbers use large bold Inter font
4. Add `/` route and `/dashboard` route in `web/app.py` that renders `dashboard.html`
5. Implement `/api/dashboard/stats` endpoint aggregating: subject count, pending assignment count, today's timetable entries, attendance per subject, latest CGPA, recent 3 notes

**Relevant Context**:
- Current `modules/dashboard/dashboard.py` — same data, replace rendering only
- Existing stat card concept: `components/widgets.py` StatCard
- Chart.js CDN: `https://cdn.jsdelivr.net/npm/chart.js`

**Status**: [x] done

---

### Sub-Task 5 — Subjects & Assignments Pages

**Intent**: Build the Subjects page (card grid with color coding) and Assignments page (filterable table with priority badges and status chips).

**Expected Outcomes**:
- Subjects: responsive grid of subject cards, each with subject color as left border/accent, subject name, code, faculty, credit hours. "Add Subject" opens a modal dialog. Cards have edit/delete actions on hover.
- Assignments: filterable list (by status: all/pending/completed, by priority: all/high/medium/low, by subject). Each row shows priority badge (colored dot), title, subject chip, due date with urgency color (red if overdue, orange if <3 days). Add/edit via modal. Mark complete inline.

**Todo List**:
1. Create `web/templates/subjects.html` + `web/static/js/subjects.js`
2. Build subject card component (color accent bar, name, code, faculty, credit, action buttons)
3. Build "Add/Edit Subject" modal with color picker (12 preset swatches matching existing palette)
4. Create `web/templates/assignments.html` + `web/static/js/assignments.js`
5. Build assignments filter bar (status tabs + priority dropdown + subject dropdown + search input)
6. Build assignment row component with priority badge, title, subject chip, due date, complete checkbox
7. Build "Add/Edit Assignment" modal with subject selector, due date picker, priority selector, description textarea
8. Add Flask routes: `GET /subjects`, `GET /assignments` rendering templates

**Relevant Context**:
- Subject color palette: 12 colors defined in `utils/theme.py` SUBJECT_COLORS
- Assignment status values: `pending`, `in_progress`, `completed` (from queries.py)
- Priority values: `high`, `medium`, `low`

**Status**: [x] done

---

### Sub-Task 6 — Attendance & Timetable Pages

**Intent**: Build the Attendance page (per-subject summary with progress bars and mark-attendance controls) and the Timetable page (weekly grid view of class schedule).

**Expected Outcomes**:
- Attendance: header stats (overall %, classes present, classes absent), per-subject rows with subject color chip, attendance %, progress bar (green/orange/red based on threshold), present/absent count, "Mark Today" button
- Timetable: 7-column weekly grid (Mon–Sun) × time rows, each class block rendered as a colored card in the correct cell. "Add Class" opens a modal. Clicking a class opens edit/delete modal.

**Todo List**:
1. Create `web/templates/attendance.html` + JS to fetch `/api/attendance/summary` and render rows with progress bars and color coding
2. Create "Mark Attendance" modal (subject selector, date, present/absent toggle)
3. Create `web/templates/timetable.html` + JS to fetch `/api/timetable` and build the grid layout with class blocks in correct day/time positions
4. Build "Add/Edit Class" modal (subject, day, start time, end time)
5. Add Flask routes: `GET /attendance`, `GET /timetable`

**Relevant Context**:
- Attendance thresholds: ≥75% green, 60-74% orange, <60% red — from `utils/theme.py`
- Timetable days: Monday–Sunday; time range typical 8:00–20:00
- Current `modules/attendance/attendance.py` and `modules/timetable/timetable.py`

**Status**: [x] done

---

### Sub-Task 7 — Planner & Calendar Pages

**Intent**: Build the Planner page (daily task view with date navigation) and Calendar page (full monthly calendar with event markers using FullCalendar.js).

**Expected Outcomes**:
- Planner: date navigation (prev/next day + date picker), list of tasks/events for selected date, add task inline, mark done, delete. Empty state for days with no tasks.
- Calendar: full FullCalendar monthly grid with event dots in type-specific colors (personal=blue, academic=indigo, exam=red, holiday=green, reminder=orange). Clicking a date opens "Add Event" modal. Clicking an event opens detail/edit modal.

**Todo List**:
1. Create `web/templates/planner.html` + JS with date navigation, daily task list fetching `/api/planner?date=YYYY-MM-DD`, inline add/complete/delete
2. Create `web/templates/calendar.html` + JS integrating FullCalendar.js (CDN), fetching `/api/calendar-events` and converting to FullCalendar event objects with type-color mapping
3. Build "Add/Edit Event" modal for calendar (title, date, type selector, description)
4. Add Flask routes: `GET /planner`, `GET /calendar`

**Relevant Context**:
- FullCalendar CDN: `https://cdn.jsdelivr.net/npm/fullcalendar@6/index.global.min.js`
- Calendar event types: `personal`, `academic`, `exam`, `holiday`, `reminder`
- Current `modules/planner/planner.py` and `modules/calendar/calendar.py`

**Status**: [x] done

---

### Sub-Task 8 — Pomodoro Timer & CGPA Pages

**Intent**: Build the Focus Timer (Pomodoro) page with a large animated circular countdown and session history, and the CGPA page with semester grade management and trend chart.

**Expected Outcomes**:
- Pomodoro: large SVG circular timer (stroke-dashoffset animation), work/break toggle, start/pause/reset controls, session counter, customizable work/break durations. Session history list below. Motivational quote that changes each session.
- CGPA: large current CGPA display with color-coded ring (green ≥3.5, orange 2.5–3.5, red <2.5), per-semester table (semester name, GPA, credit hours), trend line chart (Chart.js), add/delete semester row.

**Todo List**:
1. Create `web/templates/pomodoro.html` + `web/static/js/pomodoro.js` with SVG ring timer, start/pause/reset, work/break mode switch, `setInterval` countdown, session log stored in memory + displayed as list
2. Create `web/templates/cgpa.html` + `web/static/js/cgpa.js` fetching `/api/cgpa`, rendering large CGPA display, semester table with add/delete, Chart.js line chart of GPA per semester
3. Add Flask routes: `GET /pomodoro`, `GET /cgpa`

**Relevant Context**:
- CGPA color thresholds: ≥3.5 green, 2.5–3.49 orange, <2.5 red
- Current `modules/productivity/pomodoro.py` and `modules/cgpa/cgpa.py`
- Pomodoro default: 25 min work, 5 min short break, 15 min long break (after 4 sessions)

**Status**: [x] done

---

### Sub-Task 9 — Documents & Settings Pages

**Intent**: Build the Documents page (file manager by subject with upload/download/open) and the Settings page (profile form + theme toggle + backup/export).

**Expected Outcomes**:
- Documents: filter bar (by subject, by file type: PDF/Image/Word/Other), file grid cards with type icon + color, file name, subject chip, upload date, open/delete actions. "Upload File" button opens file picker via pywebview's file dialog API.
- Settings: profile form (name, enrollment no., department, semester), profile picture upload, theme toggle (dark/light), data export button (triggers PDF/backup), save button with success toast.

**Todo List**:
1. Create `web/templates/documents.html` + JS fetching `/api/documents`, rendering file cards with type-color icons, filter controls
2. Implement file upload: JS calls `window.pywebview.api.open_file_dialog()` → gets path → POST to `/api/documents/upload`
3. Create `web/templates/settings.html` + JS fetching `/api/profile` and `/api/settings`, form with save, theme toggle wired to `data-theme` toggle + API save
4. Add Flask routes: `GET /documents`, `GET /settings`
5. Expose pywebview JS API bridge: `open_file_dialog()` method for file picking

**Relevant Context**:
- File types tracked: PDF, image, Word, other — `database/queries.py` get_subject_files
- pywebview JS API: define a Python class with methods → pass as `js_api` to `webview.create_window()`
- Current `modules/documents/documents.py` and `modules/settings/settings.py`
- Backup: `database/backup_manager.py` — reuse existing backup logic

**Status**: [x] done

---

### Sub-Task 10 — SPA Navigation, Toasts & Polish

**Intent**: Wire all pages into a seamless Single Page Application (SPA) experience — clicking sidebar links loads content without full page reloads, adds page transitions, toast notifications, and fixes the known bugs from the old UI.

**Expected Outcomes**:
- Sidebar navigation uses `fetch()` to load page fragments into `<main>` without browser reload — smooth fade transition between pages
- Toast notification system (bottom-right) shows success/error/info messages for all CRUD operations
- Global search (Ctrl+K) opens a search overlay fetching `/api/search?q=` showing typed results with keyboard navigation
- Theme toggle persists to DB via `/api/settings` POST
- All known bugs fixed: theme persists on startup, single theme toggle, search bar is functional
- Responsive layout works down to 1100px width (min-size enforced by pywebview)

**Todo List**:
1. In `app.js`, implement SPA router: intercept all sidebar `<a>` clicks → fetch `/<page>?partial=1` → replace `<main>` innerHTML → animate fade-in → update breadcrumb + browser history (pushState)
2. Add `?partial=1` support in Flask: if partial flag, return only the `{% block content %}` body without shell
3. Build `showToast(message, type)` utility (success=green, error=red, info=blue) — CSS slide-in/out animation
4. Wire all JS CRUD operations to call `showToast` on success and error
5. Build global search overlay (Ctrl+K): full-screen dimmed modal, search input, results list with keyboard nav (arrow keys + Enter to navigate), type badges
6. Add `prefers-color-scheme` media query default for initial theme, then DB setting overrides
7. Final visual polish pass: check all pages for consistent spacing, hover states, empty states, loading spinners

**Relevant Context**:
- Known bugs list: theme not persisting (main.py line 79), two unsync'd toggles, search bar not wired, notification bell placeholder
- `database/queries.py` search-relevant functions: get_subjects, get_assignments, get_notes, get_subject_files
- pywebview sets min window size — enforce 1100×780 in `webview.create_window()`

**Status**: [x] done

---

## Design Inspiration Reference

| Element | Inspiration |
|---------|------------|
| Sidebar | Linear.app — dark, minimal, icon+label groups |
| Header | Vercel dashboard — clean breadcrumb + right-side utilities |
| Dashboard cards | Stripe dashboard — stat cards with subtle top-color borders |
| Calendar | Notion calendar — clean grid, colored event dots |
| Pomodoro timer | Forest app — large circular countdown ring |
| CGPA ring | Apple Health — colored arc on dark background |
| Color palette | GitHub dark theme + Tailwind slate |
| Typography | Inter (same as Figma, Linear, Vercel) |
| Animations | Framer Motion feel — 200ms ease-out on all transitions |

---

## New Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | Web server + API routes |
| `pywebview` | Native desktop window wrapping Flask |
| `waitress` | Production-grade WSGI server for Flask (Windows-compatible) |

CDN (loaded in `base.html`, cached after first load):
- TailwindCSS Play CDN (development) → compiled CSS for production
- Lucide Icons
- Chart.js
- FullCalendar.js
- Inter font (local copy in `web/static/fonts/`)

---

## What Is NOT Changed

- `database/` — all Python files untouched
- `utils/logger.py` — reused
- `database/backup_manager.py` — reused via Flask API endpoint
- `UserData/` — file storage path unchanged
- All business logic and data validation in `database/queries.py`
- `.gitignore`, `pyproject.toml` structure (only add new deps)
