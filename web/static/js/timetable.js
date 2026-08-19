/* ── timetable.js ── */
const TT_DAYS  = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const TT_TIMES = ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00','16:00','17:00','18:00'];

let ttAllEntries  = [];
let ttAllSubjects = [];
let ttViewingId   = null;

async function loadTimetable() {
  if (!document.getElementById('timetable-grid')) return; // not on this page
  try {
    [ttAllEntries, ttAllSubjects] = await Promise.all([
      api('GET', '/api/timetable'),
      api('GET', '/api/subjects'),
    ]);
    ttAllEntries   = ttAllEntries   || [];
    ttAllSubjects  = ttAllSubjects  || [];
    const sel = document.getElementById('tt-subject');
    if (sel) {
      sel.innerHTML = '<option value="">— No Subject —</option>' +
        ttAllSubjects.map(s => `<option value="${s.id}">${escHtml(s.name)}</option>`).join('');
    }
    renderTimetable();
  } catch(e) {
    console.error('loadTimetable error:', e);
    showToast('Failed to load timetable: ' + e.message, 'error');
  }
}

function renderTimetable() {
  // getDay(): 0=Sun,1=Mon…6=Sat  →  (day+6)%7 maps to Mon=0…Sun=6 (same as TT_DAYS order)
  const todayName = TT_DAYS[(new Date().getDay() + 6) % 7];
  const grid = document.getElementById('timetable-grid');
  if (!grid) return;

  let html = `<div class="timetable-grid" style="grid-template-columns:72px repeat(${TT_DAYS.length},1fr)">`;

  // Day headers
  html += `<div class="tt-header-cell" style="background:var(--bg-surface)"></div>`;
  TT_DAYS.forEach(d => {
    const isToday = d === todayName;
    html += `<div class="tt-header-cell${isToday?' today-col':''}">${d.substring(0,3)}<br><span style="font-size:9px;opacity:.5;font-weight:400">${d}</span></div>`;
  });

  // Time rows
  TT_TIMES.forEach((time, ti) => {
    const nextTime = TT_TIMES[ti+1] ? TT_TIMES[ti+1] : `${(parseInt(time)+1).toString().padStart(2,'0')}:00`;
    html += `<div class="tt-time-cell">${time}</div>`;
    TT_DAYS.forEach(day => {
      const entry = ttAllEntries.find(e => e.day === day && (e.time_slot||'').startsWith(time));
      if (entry) {
        const color = entry.subject_color || '#6366F1';
        html += `<div class="tt-slot">
          <div class="tt-class-block" style="background:${color}dd" onclick="viewTTEntry(${entry.id})">
            <strong>${escHtml(entry.subject_name || 'Class')}</strong>
            ${entry.classroom ? `<div class="tt-time">${escHtml(entry.classroom)}</div>` : ''}
            ${entry.time_slot ? `<div class="tt-time">${escHtml(entry.time_slot)}</div>` : ''}
          </div>
        </div>`;
      } else {
        html += `<div class="tt-slot" onclick="openTTModalForSlot('${day}','${time}-${nextTime}')"
                      style="cursor:pointer" title="Add class for ${day} ${time}"></div>`;
      }
    });
  });
  html += '</div>';
  grid.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

function openTTModal(id) {
  document.getElementById('tt-modal-title').textContent = 'Add Class';
  document.getElementById('tt-edit-id').value   = '';
  document.getElementById('tt-time').value      = '';
  document.getElementById('tt-classroom').value = '';
  document.getElementById('tt-faculty').value   = '';
  document.getElementById('tt-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('tt-time').focus(), 100);
}

function openTTModalForSlot(day, slot) {
  openTTModal(null);
  document.getElementById('tt-day').value  = day;
  document.getElementById('tt-time').value = slot;
}

function closeTTModal() {
  document.getElementById('tt-modal').classList.add('hidden');
}

function viewTTEntry(id) {
  const e = ttAllEntries.find(x => x.id === id);
  if (!e) return;
  ttViewingId = id;
  document.getElementById('tt-view-title').textContent = e.subject_name || 'Class';
  document.getElementById('tt-view-body').innerHTML = `
    <div style="display:flex;flex-direction:column;gap:10px">
      <div class="flex gap-2 items-center">
        <i data-lucide="calendar" style="width:15px;height:15px;color:var(--text-muted)"></i>
        <span style="color:var(--text-secondary)">${e.day}</span>
      </div>
      <div class="flex gap-2 items-center">
        <i data-lucide="clock" style="width:15px;height:15px;color:var(--text-muted)"></i>
        <span style="color:var(--text-secondary)">${e.time_slot || '—'}</span>
      </div>
      ${e.classroom ? `<div class="flex gap-2 items-center"><i data-lucide="map-pin" style="width:15px;height:15px;color:var(--text-muted)"></i><span style="color:var(--text-secondary)">${escHtml(e.classroom)}</span></div>` : ''}
      ${e.faculty_name ? `<div class="flex gap-2 items-center"><i data-lucide="user" style="width:15px;height:15px;color:var(--text-muted)"></i><span style="color:var(--text-secondary)">${escHtml(e.faculty_name)}</span></div>` : ''}
    </div>`;
  document.getElementById('tt-view-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeTTViewModal() {
  document.getElementById('tt-view-modal').classList.add('hidden');
  ttViewingId = null;
}

async function saveTTEntry() {
  const id   = document.getElementById('tt-edit-id').value;
  const slot = document.getElementById('tt-time').value.trim();
  if (!slot) { showToast('Time slot is required', 'warning'); return; }
  const payload = {
    day         : document.getElementById('tt-day').value,
    time_slot   : slot,
    subject_id  : parseInt(document.getElementById('tt-subject').value) || null,
    classroom   : document.getElementById('tt-classroom').value.trim() || null,
    faculty_name: document.getElementById('tt-faculty').value.trim() || null,
  };
  try {
    if (id) { await api('PUT', `/api/timetable/${id}`, payload); showToast('Class updated', 'success'); }
    else    { await api('POST', '/api/timetable', payload);      showToast('Class added!', 'success'); }
    closeTTModal();
    await loadTimetable();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

async function deleteTTEntry() {
  if (!ttViewingId) return;
  if (!confirm('Remove this class from timetable?')) return;
  try {
    await api('DELETE', `/api/timetable/${ttViewingId}`);
    showToast('Class removed', 'success');
    closeTTViewModal();
    await loadTimetable();
  } catch(e) { showToast(e.message, 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeTTModal(); closeTTViewModal(); } });
document.addEventListener('DOMContentLoaded', loadTimetable);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'timetable') loadTimetable(); });
