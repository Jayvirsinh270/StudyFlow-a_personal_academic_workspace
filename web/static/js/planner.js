/* ── planner.js ── */
let plannerCurrentDate = new Date();
let plannerTaskList    = [];

function fmtPlannerDate(d) {
  return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

function syncDateUI() {
  const s = plannerCurrentDate.toISOString().substring(0, 10);
  const lbl = document.getElementById('planner-date-label');
  const pk  = document.getElementById('planner-date-picker');
  if (lbl) lbl.textContent = fmtPlannerDate(plannerCurrentDate);
  if (pk)  pk.value = s;

  const titleEl = document.getElementById('planner-card-title');
  const today = new Date(); today.setHours(0,0,0,0);
  const cur   = new Date(plannerCurrentDate); cur.setHours(0,0,0,0);
  const diff  = Math.round((cur - today) / 86400000);
  if (titleEl) titleEl.textContent = diff === 0 ? "Today's Tasks" : diff === 1 ? "Tomorrow's Tasks" : diff === -1 ? "Yesterday's Tasks" : "Tasks";
}

function changeDate(delta) {
  plannerCurrentDate.setDate(plannerCurrentDate.getDate() + delta);
  syncDateUI();
  loadPlannerTasks();
}

function jumpToDate(val) {
  plannerCurrentDate = new Date(val + 'T12:00:00');
  syncDateUI();
  loadPlannerTasks();
}

function goToday() {
  plannerCurrentDate = new Date();
  syncDateUI();
  loadPlannerTasks();
}

async function loadPlannerTasks() {
  if (!document.getElementById('task-list')) return; // not on this page
  const dateStr = plannerCurrentDate.toISOString().substring(0, 10);
  try {
    plannerTaskList = await api('GET', `/api/planner?date=${dateStr}`);
    renderPlannerTasks();
  } catch(e) { showToast('Failed to load tasks', 'error'); }
}

function renderPlannerTasks() {
  const cnt = document.getElementById('planner-task-count');
  const el  = document.getElementById('task-list');
  if (!el) return;

  const done  = plannerTaskList.filter(t => t.status === 'completed').length;
  const total = plannerTaskList.length;
  if (cnt) cnt.textContent = `${total} task${total !== 1 ? 's' : ''}`;

  if (!plannerTaskList.length) {
    el.innerHTML = `<div class="empty-state" style="padding:48px">
      <div class="empty-icon"><i data-lucide="sun"></i></div>
      <h3>No tasks for this day</h3>
      <p>Add a task to plan your study session.</p>
      <button class="btn btn-primary mt-4" onclick="openTaskModal()">
        <i data-lucide="plus"></i> Add Task
      </button>
    </div>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const TYPE_COLORS = { daily: 'var(--text-muted)', weekly: 'var(--accent)', exam: 'var(--danger)' };
  el.innerHTML = plannerTaskList.map(t => {
    const isDone = t.status === 'completed';
    const typeColor = TYPE_COLORS[t.task_type] || TYPE_COLORS.daily;
    return `
      <div class="task-item" style="padding:13px 20px">
        <div class="task-checkbox${isDone ? ' done' : ''}" onclick="togglePlannerTask(${t.id},'${t.status}')">
          ${isDone ? '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="width:11px;height:11px;color:white"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
        </div>
        <div style="flex:1;min-width:0">
          <div class="task-title${isDone ? ' done' : ''}">${escHtml(t.title)}</div>
          ${t.description ? `<div style="font-size:11.5px;color:var(--text-muted);margin-top:2px">${escHtml(t.description)}</div>` : ''}
        </div>
        <span style="font-size:11px;font-weight:600;color:${typeColor};text-transform:capitalize;white-space:nowrap">
          ${t.task_type || 'task'}
        </span>
        <button class="btn btn-icon btn-ghost btn-sm" onclick="deletePlannerTask(${t.id})" style="color:var(--danger)">
          <i data-lucide="trash-2"></i>
        </button>
      </div>`;
  }).join('');

  // Progress line above list
  const progPct = total ? Math.round(done / total * 100) : 0;
  if (cnt) cnt.innerHTML = `<span style="font-size:11px;color:var(--text-muted)">${done}/${total} done &nbsp; ${progPct}%</span>`;
  if (window.lucide) lucide.createIcons();
}

async function togglePlannerTask(id, currentStatus) {
  const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
  try {
    await api('PUT', `/api/planner/${id}`, { status: newStatus });
    const t = plannerTaskList.find(x => x.id === id);
    if (t) t.status = newStatus;
    renderPlannerTasks();
  } catch(e) { showToast(e.message, 'error'); }
}

async function deletePlannerTask(id) {
  try {
    await api('DELETE', `/api/planner/${id}`);
    showToast('Task removed', 'info');
    await loadPlannerTasks();
  } catch(e) { showToast(e.message, 'error'); }
}

function openTaskModal() {
  document.getElementById('task-modal-title').textContent = 'Add Task';
  document.getElementById('task-edit-id').value  = '';
  document.getElementById('task-title').value    = '';
  document.getElementById('task-desc').value     = '';
  document.getElementById('task-date').value     = plannerCurrentDate.toISOString().substring(0, 10);
  document.getElementById('task-type').value     = 'daily';
  document.getElementById('task-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('task-title').focus(), 100);
}

function closeTaskModal() {
  document.getElementById('task-modal').classList.add('hidden');
}

async function saveTask() {
  const title = document.getElementById('task-title').value.trim();
  if (!title) { showToast('Title is required', 'warning'); return; }
  try {
    await api('POST', '/api/planner', {
      title,
      task_type   : document.getElementById('task-type').value,
      description : document.getElementById('task-desc').value.trim() || null,
      due_date    : document.getElementById('task-date').value || null,
      status      : 'pending',
    });
    showToast('Task added!', 'success');
    closeTaskModal();
    await loadPlannerTasks();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeTaskModal(); });
document.addEventListener('DOMContentLoaded', () => { syncDateUI(); loadPlannerTasks(); });
document.addEventListener('pageLoaded', e => {
  if (e.detail.page === 'planner') {
    plannerCurrentDate = new Date();
    syncDateUI();
    loadPlannerTasks();
  }
});
