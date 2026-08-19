/* ── attendance.js ── */
let attSummary = null;
let attSubjectsList = [];
let attBarChart = null;

async function loadAttendance() {
  if (!document.getElementById('attendance-list')) return; // not on this page
  try {
    [attSummary, attSubjectsList] = await Promise.all([
      api('GET', '/api/attendance/summary'),
      api('GET', '/api/subjects'),
    ]);

    document.getElementById('att-overall').textContent  = attSummary.overall + '%';
    document.getElementById('att-present').textContent  = attSummary.total_present;
    document.getElementById('att-absent').textContent   = attSummary.total_lectures - attSummary.total_present;

    // Subject dropdown in modal
    const sel = document.getElementById('att-subject-select');
    if (sel) {
      sel.innerHTML = attSubjectsList.map(s =>
        `<option value="${s.id}">${escHtml(s.name)}</option>`
      ).join('');
      // Pre-fill on change
      sel.onchange = () => prefillAttModal(parseInt(sel.value));
    }

    renderAttendanceRows(attSummary.subjects);

  } catch(e) { showToast('Failed to load attendance', 'error'); console.error(e); }
}

function renderAttendanceRows(subjects) {
  const container = document.getElementById('attendance-list');
  if (!container) return;

  if (!subjects.length) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-icon"><i data-lucide="circle-check"></i></div>
      <h3>No subjects yet</h3>
      <p>Add subjects and mark attendance to see progress.</p>
    </div>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  container.innerHTML = subjects.map(s => {
    const pct  = s.percentage;
    const cls  = pct >= 75 ? 'green' : pct >= 60 ? 'orange' : 'red';
    const status = pct >= 75
      ? '<span class="badge badge-green">On Track</span>'
      : pct >= 60
        ? '<span class="badge badge-orange">At Risk</span>'
        : '<span class="badge badge-red">Critical</span>';
    return `
      <div class="attendance-row">
        <div class="att-subject" style="min-width:180px;max-width:220px">
          <div class="att-dot" style="background:${s.subject_color||'var(--accent)'}"></div>
          <span class="att-name truncate">${escHtml(s.subject_name)}</span>
        </div>
        <div class="att-bar-wrapper" style="flex:1;max-width:220px">
          <div class="progress-bar">
            <div class="progress-fill ${cls} progress-fill-animate" style="width:${pct}%"></div>
          </div>
        </div>
        <span class="att-pct ${cls}">${pct}%</span>
        <span class="att-counts">${s.present}P / ${s.absent}A</span>
        ${status}
        <button class="btn btn-ghost btn-sm" onclick="openMarkModalForSubject(${s.subject_id})">
          <i data-lucide="edit-2"></i> Update
        </button>
      </div>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function prefillAttModal(sid) {
  if (!attSummary) return;
  const row = attSummary.subjects.find(r => r.subject_id === sid);
  if (row) {
    document.getElementById('att-total').value         = row.total;
    document.getElementById('att-present-input').value = row.present;
  } else {
    document.getElementById('att-total').value         = '';
    document.getElementById('att-present-input').value = '';
  }
}

function openMarkModal() {
  document.getElementById('att-total').value         = '';
  document.getElementById('att-present-input').value = '';
  document.getElementById('mark-attendance-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function openMarkModalForSubject(sid) {
  const sel = document.getElementById('att-subject-select');
  if (sel) { sel.value = sid; prefillAttModal(sid); }
  document.getElementById('mark-attendance-modal').classList.remove('hidden');
}

function closeMarkModal() {
  document.getElementById('mark-attendance-modal').classList.add('hidden');
}

async function saveAttendance() {
  const sid     = parseInt(document.getElementById('att-subject-select').value);
  const total   = parseInt(document.getElementById('att-total').value) || 0;
  const present = parseInt(document.getElementById('att-present-input').value) || 0;
  if (!sid) { showToast('Select a subject', 'warning'); return; }
  if (present > total) { showToast('Present cannot exceed total lectures', 'warning'); return; }
  try {
    await api('PUT', `/api/attendance/${sid}`, {
      total_lectures:   total,
      present_lectures: present,
      absent_lectures:  total - present,
    });
    showToast('Attendance saved!', 'success');
    closeMarkModal();
    await loadAttendance();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMarkModal(); });
document.addEventListener('DOMContentLoaded', loadAttendance);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'attendance') loadAttendance(); });
