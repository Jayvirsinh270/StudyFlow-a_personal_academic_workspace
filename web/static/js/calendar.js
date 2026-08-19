/* ── calendar.js ── */
let calendarInstance = null;
let calendarEvents   = [];
let viewingEventId   = null;

const EVENT_COLORS = {
  personal: '#3B82F6',
  academic: '#6366F1',
  exam:     '#EF4444',
  holiday:  '#22C55E',
  reminder: '#F59E0B',
};

async function initCalendar() {
  if (!document.getElementById('calendar')) return; // not on this page
  const el = document.getElementById('calendar');

  try {
    calendarEvents = await api('GET', '/api/calendar-events');
  } catch(e) { calendarEvents = []; }

  if (calendarInstance) { calendarInstance.destroy(); calendarInstance = null; }

  calendarInstance = new FullCalendar.Calendar(el, {
    initialView: 'dayGridMonth',
    headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listWeek' },
    events: calendarEvents,
    eventClick: info => viewEvent(info.event),
    dateClick: info => openEventModal(null, info.dateStr),
    height: 620,
    eventDisplay: 'block',
  });
  calendarInstance.render();
}

function viewEvent(ev) {
  viewingEventId = parseInt(ev.id);
  const type = ev.extendedProps?.type || 'personal';
  const typeColor = EVENT_COLORS[type] || EVENT_COLORS.personal;
  document.getElementById('ev-view-title').textContent = ev.title;
  document.getElementById('ev-view-body').innerHTML = `
    <div style="display:flex;flex-direction:column;gap:10px">
      <div class="flex gap-2 items-center">
        <i data-lucide="calendar" style="width:15px;height:15px;color:var(--text-muted)"></i>
        <span style="color:var(--text-secondary)">${fmtDate(ev.startStr)}</span>
      </div>
      <div class="flex gap-2 items-center">
        <i data-lucide="tag" style="width:15px;height:15px;color:var(--text-muted)"></i>
        <span class="badge" style="background:${typeColor}22;color:${typeColor};border-color:${typeColor}44;text-transform:capitalize">${type}</span>
      </div>
      ${ev.extendedProps?.description ? `
        <div class="flex gap-2" style="align-items:flex-start">
          <i data-lucide="file-text" style="width:15px;height:15px;color:var(--text-muted);flex-shrink:0;margin-top:2px"></i>
          <span style="color:var(--text-secondary)">${escHtml(ev.extendedProps.description)}</span>
        </div>` : ''}
    </div>`;
  document.getElementById('event-view-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeEventViewModal() {
  document.getElementById('event-view-modal').classList.add('hidden');
  viewingEventId = null;
}

function openEventModal(id, prefillDate) {
  document.getElementById('event-modal-title').textContent = 'Add Event';
  document.getElementById('event-edit-id').value   = '';
  document.getElementById('event-title').value     = '';
  document.getElementById('event-date').value      = prefillDate || new Date().toISOString().substring(0, 10);
  document.getElementById('event-type').value      = 'personal';
  document.getElementById('event-desc').value      = '';
  document.getElementById('event-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('event-title').focus(), 100);
}

function closeEventModal() {
  document.getElementById('event-modal').classList.add('hidden');
}

async function saveEvent() {
  const title = document.getElementById('event-title').value.trim();
  const date  = document.getElementById('event-date').value;
  if (!title) { showToast('Title is required', 'warning'); return; }
  if (!date)  { showToast('Date is required', 'warning');  return; }
  const payload = {
    title,
    event_date  : date,
    event_type  : document.getElementById('event-type').value,
    description : document.getElementById('event-desc').value.trim() || null,
  };
  try {
    await api('POST', '/api/calendar-events', payload);
    showToast('Event added!', 'success');
    closeEventModal();
    await initCalendar();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

async function deleteEvent() {
  if (!viewingEventId) return;
  if (!confirm('Delete this event?')) return;
  try {
    await api('DELETE', `/api/calendar-events/${viewingEventId}`);
    showToast('Event deleted', 'success');
    closeEventViewModal();
    await initCalendar();
  } catch(e) { showToast(e.message, 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeEventModal(); closeEventViewModal(); } });
document.addEventListener('DOMContentLoaded', initCalendar);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'calendar') initCalendar(); });
