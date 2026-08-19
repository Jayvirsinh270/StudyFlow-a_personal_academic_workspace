/* ── dashboard.js ── */
async function loadDashboard() {
  const now = new Date();
  const hour = now.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const el = document.getElementById('dash-greeting');
  if (el) el.textContent = `${greeting} — ${days[now.getDay()]}, ${months[now.getMonth()]} ${now.getDate()}`;

  try {
    const d = await api('GET', '/api/dashboard/stats');

    // Stat cards
    const s = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    s('stat-subjects',   d.subject_count);
    s('stat-pending',    d.pending_count);
    s('stat-attendance', d.overall_attendance + '%');
    s('stat-cgpa',       d.cgpa.toFixed(2));

    // CGPA ring
    const cgpa  = d.cgpa || 0;
    const maxG  = 10;
    const circ  = 2 * Math.PI * 76;
    const off   = circ - (cgpa / maxG) * circ;
    const color = cgpa >= 7.5 ? 'var(--success)' : cgpa >= 5 ? 'var(--warning)' : 'var(--danger)';
    const ring  = document.getElementById('cgpa-ring-fill');
    if (ring) { ring.style.stroke = color; setTimeout(() => { ring.style.strokeDashoffset = off; }, 120); }
    const bigEl = document.getElementById('cgpa-big');
    if (bigEl) { bigEl.textContent = cgpa.toFixed(2); bigEl.style.color = color; }

    // CGPA trend chart
    const ctx = document.getElementById('cgpa-trend-chart');
    if (ctx) {
      if (ctx._chart) { ctx._chart.destroy(); ctx._chart = null; }
      if (d.cgpa_records && d.cgpa_records.length) {
        ctx._chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: d.cgpa_records.map(r => `S${r.semester}`),
            datasets: [{ data: d.cgpa_records.map(r => r.gpa),
              borderColor: '#3B82F6', backgroundColor: 'rgba(59,130,246,0.08)',
              borderWidth: 2, pointRadius: 3, tension: 0.4, fill: true }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false, // parent div has fixed height:140px — safe
            animation: { duration: 400 },
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8B949E', font: { size: 10 } } },
              y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8B949E', font: { size: 10 } },
                   min: 0, max: 10 }
            }
          }
        });
      } else {
        // Don't replace the canvas — just overlay a message so the wrapper keeps its height
        ctx.style.display = 'none';
        const msg = document.createElement('p');
        msg.style.cssText = 'color:var(--text-muted);font-size:12px;text-align:center;padding:20px 0;margin:0';
        msg.textContent = 'No CGPA records yet';
        ctx.parentElement.appendChild(msg);
      }
    }

    // Today's classes
    const classEl = document.getElementById('today-classes');
    if (classEl) {
      if (d.today_classes && d.today_classes.length) {
        classEl.innerHTML = d.today_classes.map(c => `
          <div style="display:flex;align-items:center;gap:12px;padding:12px 20px;border-bottom:1px solid var(--border)">
            <div style="width:3px;height:38px;border-radius:2px;background:${c.subject_color||'var(--accent)'};flex-shrink:0"></div>
            <div style="flex:1;min-width:0">
              <div style="font-size:13.5px;font-weight:600;color:var(--text-primary)">${escHtml(c.subject_name||'Class')}</div>
              <div style="font-size:11.5px;color:var(--text-muted)">${escHtml(c.time_slot||'')}${c.classroom?' · '+escHtml(c.classroom):''}</div>
            </div>
          </div>`).join('');
      }
    }

    // Due soon
    const dueEl = document.getElementById('due-soon-list');
    if (dueEl && d.due_soon && d.due_soon.length) {
      const today = new Date(); today.setHours(0,0,0,0);
      dueEl.innerHTML = d.due_soon.map(a => {
        const dl = a.days_left;
        const dlColor = dl < 0 ? 'var(--danger)' : dl <= 1 ? 'var(--danger)' : dl <= 3 ? 'var(--warning)' : 'var(--text-muted)';
        const dlText  = dl < 0 ? 'Overdue' : dl === 0 ? 'Due today' : dl === 1 ? 'Tomorrow' : `${dl}d left`;
        const priColor = a.priority==='high' ? 'var(--danger)' : a.priority==='medium' ? 'var(--warning)' : 'var(--success)';
        return `
          <div style="display:flex;align-items:center;gap:12px;padding:12px 20px;border-bottom:1px solid var(--border);cursor:pointer"
               onclick="navigateTo('assignments')">
            <div style="width:8px;height:8px;border-radius:50%;background:${priColor};flex-shrink:0"></div>
            <div style="flex:1;min-width:0;overflow:hidden">
              <div style="font-size:13px;font-weight:500;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(a.title)}</div>
              <div style="font-size:11.5px;color:var(--text-muted)">${escHtml(a.subject_name||'')}</div>
            </div>
            <span style="font-size:11.5px;font-weight:600;color:${dlColor};white-space:nowrap">${dlText}</span>
          </div>`;
      }).join('');
    }

    // Recent notes
    const notesEl = document.getElementById('recent-notes-list');
    if (notesEl && d.recent_notes && d.recent_notes.length) {
      notesEl.innerHTML = d.recent_notes.map(n => `
        <div style="display:flex;align-items:flex-start;gap:12px;padding:12px 20px;border-bottom:1px solid var(--border);cursor:pointer"
             onclick="navigateTo('notes')">
          <div style="width:8px;height:8px;border-radius:50%;background:${n.subject_color||'var(--accent)'};flex-shrink:0;margin-top:4px"></div>
          <div style="flex:1;min-width:0">
            <div style="font-size:13px;font-weight:500;color:var(--text-primary)">${escHtml(n.title)}</div>
            <div style="font-size:11.5px;color:var(--text-muted)">${escHtml(n.subject_name||'')}</div>
          </div>
        </div>`).join('');
    }

    if (window.lucide) lucide.createIcons();
  } catch(e) { console.error('Dashboard error:', e); }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'dashboard') loadDashboard(); });
