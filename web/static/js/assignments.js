/* ── assignments.js ── */
let allAssignments = [];
let allSubjectsMap = {};
let activeStatus   = 'all';

const PRI = {
  high:   { color: 'var(--danger)',  label: 'High'   },
  medium: { color: 'var(--warning)', label: 'Medium' },
  low:    { color: 'var(--success)', label: 'Low'    },
};
const STA = {
  pending:     { cls: 'badge-orange', label: 'Pending'     },
  in_progress: { cls: 'badge-blue',   label: 'In Progress' },
  completed:   { cls: 'badge-green',  label: 'Completed'   },
};

async function loadAssignments() {
  if (!document.getElementById('assignments-tbody')) return; // not on this page
  try {
    const [assignments, subjects] = await Promise.all([
      api('GET', '/api/assignments'),
      api('GET', '/api/subjects'),
    ]);
    allAssignments = assignments || [];
    allSubjectsMap = Object.fromEntries((subjects || []).map(s => [s.id, s]));

    // Populate subject dropdowns
    const filterSel = document.getElementById('subject-filter');
    const modalSel  = document.getElementById('assignment-subject');
    if (filterSel) {
      filterSel.innerHTML = '<option value="all">All Subjects</option>' +
        (subjects || []).map(s => `<option value="${s.id}">${escHtml(s.name)}</option>`).join('');
    }
    if (modalSel) {
      modalSel.innerHTML = '<option value="">— No Subject —</option>' +
        (subjects || []).map(s => `<option value="${s.id}">${escHtml(s.name)}</option>`).join('');
    }
    filterAssignments();
  } catch(e) {
    console.error('loadAssignments error:', e);
    showToast('Failed to load assignments: ' + e.message, 'error');
  }
}

function setStatusFilter(status, el) {
  activeStatus = status;
  document.querySelectorAll('#status-tabs .filter-tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  filterAssignments();
}

function filterAssignments() {
  const q   = (document.getElementById('assignment-search')?.value || '').toLowerCase();
  const pri = document.getElementById('priority-filter')?.value || 'all';
  const sid = document.getElementById('subject-filter')?.value || 'all';

  const filtered = allAssignments.filter(a => {
    if (activeStatus !== 'all' && a.status !== activeStatus) return false;
    if (pri !== 'all' && a.priority !== pri) return false;
    if (sid !== 'all' && String(a.subject_id) !== sid) return false;
    if (q && !a.title.toLowerCase().includes(q)) return false;
    return true;
  });
  renderAssignmentsTable(filtered);
}

function renderAssignmentsTable(list) {
  const tbody = document.getElementById('assignments-tbody');
  if (!tbody) return;

  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="7">
      <div class="empty-state" style="padding:40px">
        <div class="empty-icon"><i data-lucide="check-square"></i></div>
        <h3>No assignments found</h3>
        <p>Try adjusting your filters or add a new assignment.</p>
      </div>
    </td></tr>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const today = new Date(); today.setHours(0,0,0,0);
  tbody.innerHTML = list.map(a => {
    const pri = PRI[a.priority] || PRI.medium;
    const sta = STA[a.status]   || STA.pending;
    const subj = allSubjectsMap[a.subject_id];
    const subjChip = subj
      ? `<span class="badge" style="background:${subj.color||'#6366F1'}22;color:${subj.color||'var(--accent)'};border-color:${subj.color||'var(--accent)'}44;max-width:140px;overflow:hidden;text-overflow:ellipsis">${escHtml(subj.name)}</span>`
      : '<span class="text-muted" style="font-size:12px">—</span>';

    let dueHtml = '<span style="color:var(--text-muted)">—</span>';
    if (a.due_date) {
      const due  = new Date(a.due_date.substring(0,10) + 'T00:00:00');
      const diff = Math.round((due - today) / 86400000);
      const col  = diff < 0 ? 'var(--danger)' : diff <= 1 ? 'var(--danger)' : diff <= 3 ? 'var(--warning)' : 'var(--text-secondary)';
      const lbl  = diff < 0 ? 'Overdue' : diff === 0 ? 'Today' : diff === 1 ? 'Tomorrow' : fmtDateShort(a.due_date);
      dueHtml = `<span style="color:${col};font-weight:600;font-size:12.5px">${lbl}</span>`;
    }

    return `<tr>
      <td>
        <div class="task-checkbox${a.status==='completed'?' done':''}" onclick="toggleAssignment(${a.id},'${a.status}')">
          ${a.status==='completed' ? '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;color:white"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
        </div>
      </td>
      <td>
        <div style="font-weight:500;color:var(--text-primary);${a.status==='completed'?'text-decoration:line-through;opacity:0.5':''}">
          ${escHtml(a.title)}
        </div>
        ${a.description ? `<div style="font-size:11.5px;color:var(--text-muted);margin-top:2px">${escHtml(a.description.substring(0,60))}${a.description.length>60?'…':''}</div>` : ''}
      </td>
      <td>${subjChip}</td>
      <td><span style="color:${pri.color};font-weight:600;font-size:12px">● ${pri.label}</span></td>
      <td>${dueHtml}</td>
      <td><span class="badge ${sta.cls}">${sta.label}</span></td>
      <td>
        <div style="display:flex;gap:4px">
          <button class="btn btn-icon btn-ghost btn-sm" onclick="openAssignmentModal(${a.id})" title="Edit">
            <i data-lucide="pencil"></i>
          </button>
          <button class="btn btn-icon btn-ghost btn-sm" onclick="deleteAssignment(${a.id})" title="Delete" style="color:var(--danger)">
            <i data-lucide="trash-2"></i>
          </button>
        </div>
      </td>
    </tr>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

async function toggleAssignment(id, currentStatus) {
  const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
  try {
    await api('PUT', `/api/assignments/${id}`, { status: newStatus });
    const a = allAssignments.find(x => x.id === id);
    if (a) a.status = newStatus;
    filterAssignments();
  } catch(e) { showToast(e.message, 'error'); }
}

function openAssignmentModal(id) {
  const isEdit = !!id;
  document.getElementById('assignment-modal-title').textContent = isEdit ? 'Edit Assignment' : 'Add Assignment';
  document.getElementById('assignment-edit-id').value = id || '';

  if (isEdit) {
    const a = allAssignments.find(x => x.id === id);
    if (a) {
      document.getElementById('assignment-title').value    = a.title || '';
      document.getElementById('assignment-subject').value  = a.subject_id || '';
      document.getElementById('assignment-priority').value = a.priority || 'medium';
      document.getElementById('assignment-due').value      = a.due_date ? a.due_date.substring(0,10) : '';
      document.getElementById('assignment-status').value   = a.status || 'pending';
      document.getElementById('assignment-desc').value     = a.description || '';
    }
  } else {
    document.getElementById('assignment-title').value    = '';
    document.getElementById('assignment-subject').value  = '';
    document.getElementById('assignment-priority').value = 'medium';
    document.getElementById('assignment-due').value      = '';
    document.getElementById('assignment-status').value   = 'pending';
    document.getElementById('assignment-desc').value     = '';
  }
  document.getElementById('assignment-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('assignment-title').focus(), 100);
}

function closeAssignmentModal() {
  document.getElementById('assignment-modal').classList.add('hidden');
}

async function saveAssignment() {
  const id    = document.getElementById('assignment-edit-id').value;
  const title = document.getElementById('assignment-title').value.trim();
  if (!title) { showToast('Title is required', 'warning'); return; }
  const payload = {
    title,
    subject_id  : parseInt(document.getElementById('assignment-subject').value) || null,
    priority    : document.getElementById('assignment-priority').value,
    due_date    : document.getElementById('assignment-due').value || null,
    status      : document.getElementById('assignment-status').value,
    description : document.getElementById('assignment-desc').value.trim() || null,
  };
  try {
    if (id) { await api('PUT', `/api/assignments/${id}`, payload); showToast('Assignment updated', 'success'); }
    else    { await api('POST', '/api/assignments', payload);      showToast('Assignment added!', 'success'); }
    closeAssignmentModal();
    await loadAssignments();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

async function deleteAssignment(id) {
  if (!confirm('Delete this assignment?')) return;
  try {
    await api('DELETE', `/api/assignments/${id}`);
    showToast('Assignment deleted', 'success');
    await loadAssignments();
  } catch(e) { showToast(e.message, 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAssignmentModal(); });
document.addEventListener('DOMContentLoaded', loadAssignments);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'assignments') loadAssignments(); });
