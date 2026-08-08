Still not working properly
Issue	Where	Impact
open_file() uses os.startfile()	utils/file_manager.py	Windows-only API — clicking "Open" on any document will crash on Mac/Linux
Theme preference doesn't persist	main.py line 47	App always forces dark mode on launch, ignoring whatever the user picked last session
Two theme toggles, out of sync	components/sidebar.py + modules/settings/settings.py	Flipping one doesn't update the other's switch position; neither writes to the DB even though get_setting/set_setting already exist for this
Search bar does nothing	components/header.py	No command/bind on search_entry — it's decorative
Notification bell does nothing	components/header.py	Same — placeholder button, no logic
Test suite can't fail	test_application.py	Still uses return True/False instead of assert, so pytest can't catch real bugs (flagged earlier, not yet fixed)
Dead/orphaned DB code	database/queries.py	documents table + add_document/get_documents/delete_document are fully unused — the Documents page actually uses a different table (subject_files). Confusing to maintain two overlapping schemas
Another orphaned table	database/queries.py	study_tasks table + full CRUD exist but no UI anywhere uses them
Packaging keeps drifting	project root	__pycache__/.pytest_cache keep regenerating with no .gitignore to keep them out of your zip/repo
Features worth adding
Persist + sync theme setting — save to the settings table on toggle, read it in main.py on startup instead of hardcoding "dark". Fixes the bug above and is a real feature (remembering preference).
Dedicated Attendance page — right now attendance only exists inside each Subject's workspace. A single page showing all subjects' attendance %, with "mark today present/absent for all classes" in one click, would match what you originally described wanting.
Real Study Tasks / To-Do view — the DB layer is already built (add_study_task, get_study_tasks, etc.); just needs a UI, probably folded into the Calendar view I just built or a new "Tasks" tab.
Decide the fate of the documents table — either build a general "upload a document not tied to a subject" area using it, or delete the dead table + functions so the schema isn't confusing later.
Working global search — wire the header search bar to actually search subjects/notes/assignments, or remove it so it doesn't look broken.
Cross-platform "open file" — swap os.startfile for a platform check (subprocess.run(["open", path]) on macOS, ["xdg-open", path] on Linux, os.startfile on Windows).
Assignment/exam reminders — you already have Calendar + Assignments with due dates; a "due soon" banner on the Dashboard would tie them together nicely and is a natural next feature.
Backup/export — since everything lives in one local SQLite file + UserData/Files, a simple "export my data" button (zip the UserData folder) would protect students from losing everything on a reinstall.