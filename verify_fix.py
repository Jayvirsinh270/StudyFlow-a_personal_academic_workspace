import sys, threading, time, socket, urllib.request, json, re
sys.path.insert(0,'.')
from database import initialize_database
initialize_database()

def find_free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

port = find_free_port()
from waitress import serve
from web.app import app
t = threading.Thread(target=lambda: serve(app, host='127.0.0.1', port=port, threads=2), daemon=True)
t.start()
time.sleep(1.5)

# Verify ALL JS files are loaded in base.html
with urllib.request.urlopen(f'http://127.0.0.1:{port}/dashboard', timeout=5) as r:
    html = r.read().decode()

js_files = ['app.js','dashboard.js','subjects.js','assignments.js','attendance.js',
            'timetable.js','planner.js','calendar.js','pomodoro.js','cgpa.js',
            'documents.js','notes.js','settings.js']

print('--- JS files in base.html shell ---')
all_ok = True
for js in js_files:
    present = js in html
    if not present: all_ok = False
    print(f"  {'OK' if present else 'MISSING'} {js}")

print()

# Verify partials do NOT contain script tags (they're stripped/removed)
pages = ['subjects','assignments','attendance','timetable','planner','calendar',
         'pomodoro','cgpa','documents','notes','settings','dashboard']
print('--- Partial pages (should have NO <script> tags) ---')
for page in pages:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/{page}?partial=1', timeout=5) as r:
        partial = r.read().decode()
    script_tags = re.findall(r'<script[^>]*>', partial)
    ok = len(script_tags) == 0
    if not ok: all_ok = False
    print(f"  {'OK' if ok else 'FAIL: has '+str(script_tags)} /{ page}?partial=1")

print()
print('ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED')
