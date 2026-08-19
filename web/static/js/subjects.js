/* ── subjects.js ── */
const SUBJECT_COLORS = [
  '#6366F1','#2563EB','#0284C7','#0D9488',
  '#16A34A','#65A30D','#D97706','#DC2626',
  '#DB2777','#9333EA','#7C3AED','#EA580C'
];

let allSubjects       = [];
let deletingSubjectId = null;

/* ── Color swatch helpers ───────────────────────────── */
function buildColorSwatches(selectedColor) {
  const container = document.getElementById('subject-color-swatches');
  if (!container) return;
  container.innerHTML = SUBJECT_COLORS.map(c => `
    <div class="color-swatch${c === selectedColor ? ' selected' : ''}"
         style="background:${c}" onclick="pickColor('${c}')" title="${c}"></div>
  `).join('');
}

function pickColor(hex) {
  const hiddenInput = document.getElementById('subject-color');
  if (hiddenInput) hiddenInput.value = hex;
  document.querySelectorAll('.color-swatch').forEach(el => {
    el.classList.toggle('selected', el.getAttribute('onclick') === `pickColor('${hex}')`);
  });
}

/* ── Load + Render subjects ─────────────────────────── */
async function loadSubjects() {
  if (!document.getElementById('subjects-grid')) return;
  try {
    allSubjects = await api('GET', '/api/subjects') || [];
    renderSubjects(allSubjects);
  } catch(e) {
    console.error('loadSubjects error:', e);
    showToast('Failed to load subjects', 'error');
  }
}

function filterSubjects(q) {
  const query = (q || '').toLowerCase();
  renderSubjects(allSubjects.filter(s =>
    s.name.toLowerCase().includes(query) ||
    (s.subject_code  || '').toLowerCase().includes(query) ||
    (s.faculty_name  || '').toLowerCase().includes(query)
  ));
}

function renderSubjects(list) {
  const grid = document.getElementById('subjects-grid');
  if (!grid) return;
  if (!list.length) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;padding:60px">
        <div class="empty-icon"><i data-lucide="book-open"></i></div>
        <h3>${allSubjects.length ? 'No subjects match your search' : 'No subjects yet'}</h3>
        <p>${allSubjects.length ? 'Try a different search term.' : 'Add your first subject to get started.'}</p>
        ${!allSubjects.length ? '<button class="btn btn-primary mt-4" onclick="openSubjectModal()"><i data-lucide="plus"></i> Add Subject</button>' : ''}
      </div>`;
    if (window.lucide) lucide.createIcons();
    return;
  }
  grid.innerHTML = list.map(s => {
    const color = s.color || '#6366F1';
    const init  = (s.name || '?').charAt(0).toUpperCase();
    return `
    <div class="subject-card card-hover" onclick="openSubjectDrawer(${s.id})" style="cursor:pointer">
      <div class="subject-card-accent" style="background:${color}"></div>
      <div class="subject-card-body">
        <div class="subject-card-header">
          <div class="subject-initial" style="background:${color}">${init}</div>
          <div class="subject-actions">
            <button class="btn btn-icon btn-ghost btn-sm" onclick="event.stopPropagation();openSubjectModal(${s.id})" title="Edit">
              <i data-lucide="pencil"></i>
            </button>
            <button class="btn btn-icon btn-ghost btn-sm" onclick="event.stopPropagation();deleteSubject(${s.id},'${escHtml(s.name)}')" title="Delete" style="color:var(--danger)">
              <i data-lucide="trash-2"></i>
            </button>
          </div>
        </div>
        <h3 style="margin-top:10px">${escHtml(s.name)}</h3>
        ${s.subject_code ? `<div class="subject-code">${escHtml(s.subject_code)}</div>` : ''}
        <div class="subject-meta">
          ${s.faculty_name ? `<span class="subject-meta-item"><i data-lucide="user"></i>${escHtml(s.faculty_name)}</span>` : ''}
          ${s.credit       ? `<span class="subject-meta-item"><i data-lucide="star"></i>${s.credit} cr</span>` : ''}
          ${s.semester     ? `<span class="subject-meta-item"><i data-lucide="layers"></i>Sem ${s.semester}</span>` : ''}
        </div>
        <div style="margin-top:10px">
          <span class="badge badge-gray" style="font-size:10.5px">
            <i data-lucide="arrow-right" style="width:10px;height:10px"></i> Click for details
          </span>
        </div>
      </div>
    </div>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

/* ── Add / Edit modal ───────────────────────────────── */
function openSubjectModal(id) {
  const isEdit = !!id;
  document.getElementById('subject-modal-title').textContent = isEdit ? 'Edit Subject' : 'Add Subject';
  document.getElementById('subject-edit-id').value = id || '';

  let selectedColor = SUBJECT_COLORS[0];
  if (isEdit) {
    const s = allSubjects.find(x => x.id === id);
    if (s) {
      document.getElementById('subject-name').value    = s.name || '';
      document.getElementById('subject-code').value    = s.subject_code || '';
      document.getElementById('subject-credit').value  = s.credit || '';
      document.getElementById('subject-faculty').value = s.faculty_name || '';
      selectedColor = s.color || SUBJECT_COLORS[0];
    }
  } else {
    document.getElementById('subject-name').value    = '';
    document.getElementById('subject-code').value    = '';
    document.getElementById('subject-credit').value  = '';
    document.getElementById('subject-faculty').value = '';
  }
  document.getElementById('subject-color').value = selectedColor;
  buildColorSwatches(selectedColor);
  document.getElementById('subject-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('subject-name').focus(), 100);
}

function closeSubjectModal() {
  document.getElementById('subject-modal').classList.add('hidden');
}
function closeDeleteModal() {
  document.getElementById('subject-delete-modal').classList.add('hidden');
}

async function saveSubject() {
  const id   = document.getElementById('subject-edit-id').value;
  const name = document.getElementById('subject-name').value.trim();
  if (!name) { showToast('Subject name is required', 'warning'); return; }
  const payload = {
    name,
    subject_code : document.getElementById('subject-code').value.trim()    || null,
    faculty_name : document.getElementById('subject-faculty').value.trim()  || null,
    credit       : parseFloat(document.getElementById('subject-credit').value) || null,
    color        : document.getElementById('subject-color').value || SUBJECT_COLORS[0],
  };
  try {
    if (id) {
      await api('PUT', `/api/subjects/${id}`, payload);
      showToast('Subject updated', 'success');
    } else {
      await api('POST', '/api/subjects', payload);
      showToast('Subject added!', 'success');
    }
    closeSubjectModal();
    await loadSubjects();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

function deleteSubject(id, name) {
  deletingSubjectId = id;
  const el = document.getElementById('delete-subject-name');
  if (el) el.textContent = name;
  document.getElementById('subject-delete-modal').classList.remove('hidden');
}

async function confirmDeleteSubject() {
  if (!deletingSubjectId) return;
  try {
    await api('DELETE', `/api/subjects/${deletingSubjectId}`);
    showToast('Subject deleted', 'success');
    closeDeleteModal();
    deletingSubjectId = null;
    closeSubjectDrawer(); // close drawer if open
    await loadSubjects();
  } catch(e) { showToast(e.message || 'Delete failed', 'error'); }
}

/* ─────────────────────────────────────────────────────
   SUBJECT DETAIL DRAWER
   ───────────────────────────────────────────────────── */
let _drawerSubjectId  = null;
let _activeDrawerTab  = 'overview';

async function openSubjectDrawer(sid) {
  _drawerSubjectId = sid;
  _activeDrawerTab = 'overview';

  // Remove any existing drawer
  _removeDrawerDOM();

  // Create backdrop
  const backdrop = document.createElement('div');
  backdrop.id = 'subject-drawer-backdrop';
  backdrop.className = 'subject-drawer-backdrop';
  backdrop.onclick = e => { if (e.target === backdrop) closeSubjectDrawer(); };

  // Create drawer shell with loading state
  const drawer = document.createElement('div');
  drawer.id = 'subject-drawer';
  drawer.className = 'subject-drawer';
  drawer.innerHTML = `
    <div class="drawer-header">
      <div class="drawer-header-top">
        <div class="drawer-subject-identity">
          <div class="drawer-subject-avatar" id="drawer-avatar">…</div>
          <div>
            <div class="drawer-subject-name" id="drawer-name">Loading…</div>
            <div class="drawer-subject-meta" id="drawer-meta"></div>
          </div>
        </div>
        <button class="drawer-close" onclick="closeSubjectDrawer()">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- Quick stats strip -->
      <div class="drawer-stats" id="drawer-stats">
        <div class="drawer-stat"><div class="drawer-stat-value" id="ds-assignments">—</div><div class="drawer-stat-label">Assignments</div></div>
        <div class="drawer-stat"><div class="drawer-stat-value" id="ds-pending">—</div><div class="drawer-stat-label">Pending</div></div>
        <div class="drawer-stat"><div class="drawer-stat-value" id="ds-attendance">—%</div><div class="drawer-stat-label">Attendance</div></div>
        <div class="drawer-stat"><div class="drawer-stat-value" id="ds-notes">—</div><div class="drawer-stat-label">Notes</div></div>
      </div>

      <!-- Tabs -->
      <div class="drawer-tabs" id="drawer-tabs">
        <div class="drawer-tab active" onclick="switchDrawerTab('overview')">Overview</div>
        <div class="drawer-tab" onclick="switchDrawerTab('assignments')">Assignments</div>
        <div class="drawer-tab" onclick="switchDrawerTab('attendance')">Attendance</div>
        <div class="drawer-tab" onclick="switchDrawerTab('timetable')">Timetable</div>
        <div class="drawer-tab" onclick="switchDrawerTab('notes')">Notes</div>
        <div class="drawer-tab" onclick="switchDrawerTab('files')">Files</div>
      </div>
    </div>

    <!-- Body panels -->
    <div class="drawer-body" id="drawer-body">
      <div style="display:flex;align-items:center;justify-content:center;height:200px">
        <div class="spinner"></div>
      </div>
    </div>

    <!-- Footer actions -->
    <div class="drawer-actions" id="drawer-footer-actions">
      <button class="btn btn-primary btn-sm" onclick="openSubjectModal(${sid});closeSubjectDrawer()">
        <i data-lucide="pencil"></i> Edit Subject
      </button>
      <button class="btn btn-ghost btn-sm" onclick="navigateTo('assignments')">
        <i data-lucide="check-square"></i> All Assignments
      </button>
      <button class="btn btn-ghost btn-sm" onclick="navigateTo('attendance')">
        <i data-lucide="circle-check"></i> Attendance
      </button>
      <button class="btn btn-ghost btn-sm" onclick="navigateTo('notes')">
        <i data-lucide="notebook-pen"></i> Notes
      </button>
      <button class="btn btn-danger btn-sm" style="margin-left:auto" onclick="deleteSubject(${sid},'')">
        <i data-lucide="trash-2"></i> Delete
      </button>
    </div>`;

  backdrop.appendChild(drawer);
  document.body.appendChild(backdrop);
  if (window.lucide) lucide.createIcons();

  // Fetch detail data
  try {
    const data = await api('GET', `/api/subjects/${sid}/detail`);
    _renderDrawerData(data);
  } catch(e) {
    document.getElementById('drawer-body').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon"><i data-lucide="alert-circle"></i></div>
        <h3>Failed to load details</h3>
        <p>${escHtml(e.message)}</p>
      </div>`;
    if (window.lucide) lucide.createIcons();
  }
}

function _renderDrawerData(data) {
  const s   = data.subject;
  const att = data.attendance;
  const color = s.color || '#6366F1';
  const init  = (s.name || '?').charAt(0).toUpperCase();

  // Header
  const avatarEl = document.getElementById('drawer-avatar');
  if (avatarEl) { avatarEl.textContent = init; avatarEl.style.background = color; }
  const nameEl = document.getElementById('drawer-name');
  if (nameEl) nameEl.textContent = s.name;
  const metaEl = document.getElementById('drawer-meta');
  if (metaEl) {
    const parts = [];
    if (s.subject_code) parts.push(`<span>📋 ${escHtml(s.subject_code)}</span>`);
    if (s.faculty_name) parts.push(`<span>👤 ${escHtml(s.faculty_name)}</span>`);
    if (s.credit)       parts.push(`<span>⭐ ${s.credit} credits</span>`);
    if (s.semester)     parts.push(`<span>📅 Semester ${s.semester}</span>`);
    metaEl.innerHTML = parts.join('');
  }

  // Stats strip
  const sv = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  sv('ds-assignments', data.assignments.total);
  sv('ds-pending',     data.assignments.pending_count);
  sv('ds-attendance',  att.percentage + '%');
  sv('ds-notes',       data.notes.length);

  // Color the attendance stat
  const attEl = document.getElementById('ds-attendance');
  if (attEl) {
    attEl.style.color = att.percentage >= 75 ? 'var(--success)' : att.percentage >= 60 ? 'var(--warning)' : 'var(--danger)';
  }

  // Also update delete button label
  const delBtn = document.querySelector('#drawer-footer-actions .btn-danger');
  if (delBtn) delBtn.onclick = () => deleteSubject(s.id, s.name);

  // Build all panel HTML
  _buildDrawerPanels(data);
  switchDrawerTab('overview');
}

function _buildDrawerPanels(data) {
  const s   = data.subject;
  const att = data.attendance;
  const color = s.color || '#6366F1';
  const attPct = att.percentage;
  const attCls = attPct >= 75 ? 'var(--success)' : attPct >= 60 ? 'var(--warning)' : 'var(--danger)';
  const circ   = 2 * Math.PI * 36;
  const off    = circ - (attPct / 100) * circ;

  // ── OVERVIEW TAB ─────────────────────────────────────
  const overviewHTML = `
    <div class="drawer-panel active" id="drawer-panel-overview">

      <!-- Attendance ring mini -->
      <p class="drawer-section-title">Attendance</p>
      <div class="drawer-att-ring">
        <svg class="drawer-att-ring-svg" viewBox="0 0 90 90" style="transform:rotate(-90deg)">
          <circle cx="45" cy="45" r="36" fill="none" stroke="var(--border)" stroke-width="7"/>
          <circle cx="45" cy="45" r="36" fill="none" stroke="${attCls}" stroke-width="7"
                  stroke-linecap="round"
                  stroke-dasharray="${circ.toFixed(1)}"
                  stroke-dashoffset="${off.toFixed(1)}"
                  style="transition:stroke-dashoffset 0.8s ease"/>
        </svg>
        <div>
          <div style="font-size:28px;font-weight:800;color:${attCls};font-variant-numeric:tabular-nums">${attPct}%</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${att.present} present / ${att.absent} absent / ${att.total} total</div>
          <div style="margin-top:8px">
            ${attPct >= 75
              ? '<span class="badge badge-green">✓ On Track</span>'
              : attPct >= 60
                ? '<span class="badge badge-orange">⚠ At Risk</span>'
                : '<span class="badge badge-red">✗ Critical</span>'}
          </div>
          ${att.total > 0 && attPct < 75 ? `
            <div style="font-size:11.5px;color:var(--text-muted);margin-top:8px">
              Need <strong style="color:var(--warning)">${Math.ceil((0.75 * att.total - att.present) / 0.25)}</strong> more classes to reach 75%
            </div>` : ''}
        </div>
      </div>

      <!-- Upcoming assignments -->
      <p class="drawer-section-title" style="margin-top:20px">Pending Assignments (${data.assignments.pending_count})</p>
      ${data.assignments.all.filter(a => a.status !== 'completed').length === 0
        ? '<div style="color:var(--text-muted);font-size:13px;padding:12px 0">🎉 All caught up!</div>'
        : data.assignments.all
            .filter(a => a.status !== 'completed')
            .slice(0, 4)
            .map(a => _assignmentRowHTML(a))
            .join('')
      }

      <!-- Next class -->
      <p class="drawer-section-title" style="margin-top:20px">Timetable (${data.timetable.length} slot${data.timetable.length !== 1 ? 's' : ''})</p>
      ${data.timetable.length === 0
        ? '<div style="color:var(--text-muted);font-size:13px;padding:8px 0">No classes scheduled</div>'
        : data.timetable.map(t => _ttSlotHTML(t, color)).join('')
      }
    </div>`;

  // ── ASSIGNMENTS TAB ───────────────────────────────────
  const pending   = data.assignments.all.filter(a => a.status !== 'completed');
  const completed = data.assignments.all.filter(a => a.status === 'completed');
  const assignmentsHTML = `
    <div class="drawer-panel" id="drawer-panel-assignments">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <p class="drawer-section-title" style="margin:0;border:none">All Assignments (${data.assignments.all.length})</p>
        <button class="btn btn-primary btn-sm" onclick="closeSubjectDrawer();navigateTo('assignments')">
          <i data-lucide="external-link"></i> Open Full View
        </button>
      </div>
      ${data.assignments.all.length === 0
        ? '<div class="empty-state" style="padding:32px"><div class="empty-icon"><i data-lucide="check-square"></i></div><h3>No assignments</h3><p>No assignments for this subject yet.</p></div>'
        : `
          ${pending.length ? `<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--warning);margin-bottom:8px">Pending (${pending.length})</p>
            ${pending.map(a => _assignmentRowHTML(a)).join('')}` : ''}
          ${completed.length ? `<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--text-muted);margin-top:16px;margin-bottom:8px">Completed (${completed.length})</p>
            ${completed.map(a => _assignmentRowHTML(a)).join('')}` : ''}
        `}
    </div>`;

  // ── ATTENDANCE TAB ────────────────────────────────────
  const needed75 = att.total > 0 ? Math.max(0, Math.ceil((0.75 * att.total - att.present) / 0.25)) : 0;
  const canMiss  = att.total > 0 ? Math.max(0, Math.floor(att.present / 0.75 - att.total)) : 0;
  const attendanceHTML = `
    <div class="drawer-panel" id="drawer-panel-attendance">
      <div style="display:flex;justify-content:center;margin-bottom:20px">
        <svg viewBox="0 0 160 160" style="width:160px;height:160px;transform:rotate(-90deg)">
          <circle cx="80" cy="80" r="66" fill="none" stroke="var(--border)" stroke-width="10"/>
          <circle cx="80" cy="80" r="66" fill="none" stroke="${attCls}" stroke-width="10"
                  stroke-linecap="round"
                  stroke-dasharray="${(2*Math.PI*66).toFixed(1)}"
                  stroke-dashoffset="${(2*Math.PI*66 - (attPct/100)*2*Math.PI*66).toFixed(1)}"
                  style="transition:stroke-dashoffset 0.8s ease"/>
        </svg>
      </div>
      <div style="text-align:center;margin-top:-130px;margin-bottom:110px">
        <div style="font-size:36px;font-weight:800;color:${attCls}">${attPct}%</div>
        <div style="font-size:12px;color:var(--text-muted)">Attendance</div>
      </div>

      <div class="drawer-stats" style="margin-bottom:16px">
        <div class="drawer-stat"><div class="drawer-stat-value" style="color:var(--success)">${att.present}</div><div class="drawer-stat-label">Present</div></div>
        <div class="drawer-stat"><div class="drawer-stat-value" style="color:var(--danger)">${att.absent}</div><div class="drawer-stat-label">Absent</div></div>
        <div class="drawer-stat"><div class="drawer-stat-value">${att.total}</div><div class="drawer-stat-label">Total</div></div>
        <div class="drawer-stat"><div class="drawer-stat-value" style="color:${attCls}">${attPct}%</div><div class="drawer-stat-label">Percentage</div></div>
      </div>

      ${att.total > 0 ? `
      <div style="background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);padding:14px 16px;display:flex;flex-direction:column;gap:8px">
        ${attPct < 75 ? `<div style="font-size:13px;color:var(--text-secondary)">
          📈 You need <strong style="color:var(--warning)">${needed75}</strong> more consecutive classes to reach 75%
        </div>` : `<div style="font-size:13px;color:var(--success)">
          ✅ You can miss <strong>${canMiss}</strong> more class${canMiss !== 1 ? 'es' : ''} and stay above 75%
        </div>`}
      </div>` : ''}

      <div style="margin-top:16px;text-align:center">
        <button class="btn btn-primary btn-sm" onclick="closeSubjectDrawer();navigateTo('attendance')">
          <i data-lucide="edit-2"></i> Update Attendance
        </button>
      </div>
    </div>`;

  // ── TIMETABLE TAB ─────────────────────────────────────
  const timetableHTML = `
    <div class="drawer-panel" id="drawer-panel-timetable">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <p class="drawer-section-title" style="margin:0;border:none">Class Schedule (${data.timetable.length} slots)</p>
        <button class="btn btn-ghost btn-sm" onclick="closeSubjectDrawer();navigateTo('timetable')">
          <i data-lucide="external-link"></i> Edit Timetable
        </button>
      </div>
      ${data.timetable.length === 0
        ? `<div class="empty-state" style="padding:40px">
            <div class="empty-icon"><i data-lucide="table-2"></i></div>
            <h3>No slots scheduled</h3>
            <p>Go to Timetable to add class slots for this subject.</p>
            <button class="btn btn-primary btn-sm mt-4" onclick="closeSubjectDrawer();navigateTo('timetable')">
              <i data-lucide="plus"></i> Add to Timetable
            </button>
           </div>`
        : data.timetable.map(t => _ttSlotHTML(t, color)).join('')
      }
    </div>`;

  // ── NOTES TAB ─────────────────────────────────────────
  const notesHTML = `
    <div class="drawer-panel" id="drawer-panel-notes">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <p class="drawer-section-title" style="margin:0;border:none">Notes (${data.notes.length})</p>
        <button class="btn btn-primary btn-sm" onclick="closeSubjectDrawer();navigateTo('notes')">
          <i data-lucide="plus"></i> New Note
        </button>
      </div>
      ${data.notes.length === 0
        ? `<div class="empty-state" style="padding:40px">
            <div class="empty-icon"><i data-lucide="notebook-pen"></i></div>
            <h3>No notes yet</h3>
            <p>Start taking notes for this subject.</p>
           </div>`
        : data.notes.map(n => `
          <div class="drawer-note-card" onclick="closeSubjectDrawer();navigateTo('notes')">
            <div style="display:flex;align-items:center;justify-content:space-between">
              <h5>${escHtml(n.title || 'Untitled')}</h5>
              ${n.is_pinned ? '<span style="font-size:12px">📌</span>' : ''}
            </div>
            ${n.content ? `<p>${escHtml(n.content.substring(0, 100))}${n.content.length > 100 ? '…' : ''}</p>` : '<p style="font-style:italic">Empty note</p>'}
            <div style="font-size:11px;color:var(--text-muted);margin-top:8px">
              ${n.updated_at ? new Date(n.updated_at).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) : ''}
            </div>
          </div>`).join('')
      }
    </div>`;

  // ── FILES TAB ─────────────────────────────────────────
  const FILE_ICONS = { PDF:'📄', Image:'🖼️', Word:'📝', Other:'📎' };
  const filesHTML = `
    <div class="drawer-panel" id="drawer-panel-files">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
        <p class="drawer-section-title" style="margin:0;border:none">Files (${data.files.length})</p>
        <button class="btn btn-primary btn-sm" onclick="closeSubjectDrawer();navigateTo('documents')">
          <i data-lucide="upload"></i> Upload File
        </button>
      </div>
      ${data.files.length === 0
        ? `<div class="empty-state" style="padding:40px">
            <div class="empty-icon"><i data-lucide="file-stack"></i></div>
            <h3>No files yet</h3>
            <p>Upload study materials for this subject.</p>
           </div>`
        : data.files.map(f => `
          <div class="drawer-file-card" onclick="openDocFromDrawer(${f.id})">
            <span class="drawer-file-icon">${FILE_ICONS[f.file_type] || FILE_ICONS.Other}</span>
            <span class="drawer-file-name">${escHtml(f.file_name || 'Unnamed')}</span>
            ${f.file_size ? `<span class="drawer-file-size">${(f.file_size/1024).toFixed(0)} KB</span>` : ''}
          </div>`).join('')
      }
    </div>`;

  document.getElementById('drawer-body').innerHTML =
    overviewHTML + assignmentsHTML + attendanceHTML + timetableHTML + notesHTML + filesHTML;

  if (window.lucide) lucide.createIcons();
}

/* ── Helper: assignment row HTML ────────────────────── */
function _assignmentRowHTML(a) {
  const today = new Date(); today.setHours(0,0,0,0);
  const PRI_C = { high:'var(--danger)', medium:'var(--warning)', low:'var(--success)' };
  const STA_B = { pending:'badge-orange', in_progress:'badge-blue', completed:'badge-green' };
  const STA_L = { pending:'Pending', in_progress:'In Progress', completed:'Done' };
  let dueStr = '';
  if (a.due_date) {
    const due  = new Date(a.due_date.substring(0,10) + 'T00:00:00');
    const diff = Math.round((due - today) / 86400000);
    const col  = diff < 0 ? 'var(--danger)' : diff <= 1 ? 'var(--danger)' : diff <= 3 ? 'var(--warning)' : 'var(--text-muted)';
    const lbl  = diff < 0 ? 'Overdue' : diff === 0 ? 'Today' : diff === 1 ? 'Tomorrow' : fmtDateShort(a.due_date);
    dueStr = `<span style="font-size:11px;color:${col};font-weight:600;white-space:nowrap">${lbl}</span>`;
  }
  return `<div class="drawer-assignment-row">
    <div style="width:8px;height:8px;border-radius:50%;background:${PRI_C[a.priority]||PRI_C.medium};flex-shrink:0"></div>
    <div style="flex:1;min-width:0">
      <div style="font-size:13px;font-weight:500;color:${a.status==='completed'?'var(--text-muted)':'var(--text-primary)'};${a.status==='completed'?'text-decoration:line-through':''};overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(a.title)}</div>
    </div>
    ${dueStr}
    <span class="badge ${STA_B[a.status]||STA_B.pending}" style="font-size:10px">${STA_L[a.status]||'Pending'}</span>
  </div>`;
}

/* ── Helper: timetable slot HTML ────────────────────── */
function _ttSlotHTML(t, color) {
  return `<div class="drawer-tt-slot">
    <div style="width:4px;height:36px;border-radius:2px;background:${color};flex-shrink:0"></div>
    <div class="drawer-tt-info">
      <div class="drawer-tt-time">${escHtml(t.time_slot || '—')}</div>
      <small>${escHtml(t.day || '')}${t.classroom ? ' · ' + escHtml(t.classroom) : ''}${t.faculty_name ? ' · ' + escHtml(t.faculty_name) : ''}</small>
    </div>
  </div>`;
}

/* ── Tab switching ──────────────────────────────────── */
function switchDrawerTab(tabName) {
  _activeDrawerTab = tabName;
  // Update tab buttons
  document.querySelectorAll('.drawer-tab').forEach((el, i) => {
    const tabs = ['overview','assignments','attendance','timetable','notes','files'];
    el.classList.toggle('active', tabs[i] === tabName);
  });
  // Show/hide panels
  document.querySelectorAll('.drawer-panel').forEach(el => {
    el.classList.remove('active');
  });
  const panel = document.getElementById(`drawer-panel-${tabName}`);
  if (panel) panel.classList.add('active');
}
window.switchDrawerTab = switchDrawerTab;

/* ── Close drawer ───────────────────────────────────── */
function closeSubjectDrawer() {
  const backdrop = document.getElementById('subject-drawer-backdrop');
  const drawer   = document.getElementById('subject-drawer');
  if (!backdrop) return;
  backdrop.classList.add('closing');
  if (drawer) drawer.classList.add('closing');
  setTimeout(_removeDrawerDOM, 210);
}

function _removeDrawerDOM() {
  const el = document.getElementById('subject-drawer-backdrop');
  if (el) el.remove();
  _drawerSubjectId = null;
}

window.openSubjectDrawer  = openSubjectDrawer;
window.closeSubjectDrawer = closeSubjectDrawer;

/* ── Open doc from drawer ───────────────────────────── */
async function openDocFromDrawer(fid) {
  try {
    await api('POST', `/api/documents/open/${fid}`);
  } catch(e) { showToast('Could not open file', 'error'); }
}
window.openDocFromDrawer = openDocFromDrawer;

/* ── Keyboard ───────────────────────────────────────── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (document.getElementById('subject-drawer-backdrop')) {
      closeSubjectDrawer();
    } else {
      closeSubjectModal();
      closeDeleteModal();
    }
  }
});

document.addEventListener('DOMContentLoaded', loadSubjects);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'subjects') loadSubjects(); });
