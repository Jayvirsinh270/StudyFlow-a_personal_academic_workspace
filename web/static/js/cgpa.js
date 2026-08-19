/* ── cgpa.js ── */
let cgpaRecords = [];
let cgpaChart   = null;

async function loadCGPA() {
  if (!document.getElementById('cgpa-display')) return; // not on this page
  try {
    const data = await api('GET', '/api/cgpa');
    cgpaRecords = data.records || [];
    renderCGPARing(data.cgpa || 0);
    renderCGPATable();
    renderCGPAChart();
  } catch(e) { showToast('Failed to load CGPA', 'error'); }
}

function renderCGPARing(cgpa) {
  const maxG  = 10;
  const circ  = 2 * Math.PI * 76;
  const off   = circ - (cgpa / maxG) * circ;
  const color = cgpa >= 7.5 ? 'var(--success)' : cgpa >= 5 ? 'var(--warning)' : cgpa > 0 ? 'var(--danger)' : 'var(--border-strong)';

  const ring = document.getElementById('cgpa-ring');
  if (ring) {
    ring.style.stroke = color;
    setTimeout(() => { ring.style.strokeDashoffset = off; }, 100);
  }
  const display = document.getElementById('cgpa-display');
  if (display) { display.textContent = cgpa.toFixed(2); display.style.color = color; }

  const badge = document.getElementById('cgpa-grade-badge');
  if (badge) {
    const grade = cgpa >= 9 ? 'Outstanding' : cgpa >= 7.5 ? 'Excellent' : cgpa >= 6 ? 'Good' : cgpa >= 5 ? 'Average' : 'Needs Improvement';
    const badgeCls = cgpa >= 7.5 ? 'badge-green' : cgpa >= 5 ? 'badge-orange' : cgpa > 0 ? 'badge-red' : 'badge-gray';
    badge.innerHTML = `<span class="badge ${badgeCls}">${grade}</span>`;
  }
}

function renderCGPATable() {
  const tbody = document.getElementById('cgpa-tbody');
  if (!tbody) return;
  if (!cgpaRecords.length) {
    tbody.innerHTML = `<tr><td colspan="5">
      <div class="empty-state" style="padding:32px">
        <div class="empty-icon"><i data-lucide="trending-up"></i></div>
        <h3>No records yet</h3>
        <p>Add your semester GPAs to start tracking.</p>
      </div>
    </td></tr>`;
    if (window.lucide) lucide.createIcons();
    return;
  }
  tbody.innerHTML = cgpaRecords.map(r => {
    const grade = r.gpa >= 9 ? 'O' : r.gpa >= 8 ? 'A+' : r.gpa >= 7 ? 'A' : r.gpa >= 6 ? 'B+' : r.gpa >= 5 ? 'B' : 'C';
    const color = r.gpa >= 7.5 ? 'var(--success)' : r.gpa >= 5 ? 'var(--warning)' : 'var(--danger)';
    return `<tr>
      <td style="font-weight:600">Semester ${r.semester}</td>
      <td style="font-weight:700;color:${color}">${parseFloat(r.gpa).toFixed(2)}</td>
      <td style="color:var(--text-secondary)">${r.credits || '—'}</td>
      <td><span style="color:${color};font-weight:700">${grade}</span></td>
      <td>
        <button class="btn btn-icon btn-ghost btn-sm" onclick="deleteCGPARecord(${r.id})" title="Delete" style="color:var(--danger)">
          <i data-lucide="trash-2"></i>
        </button>
      </td>
    </tr>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function renderCGPAChart() {
  const ctx = document.getElementById('cgpa-chart');
  if (!ctx) return;
  if (cgpaChart) { cgpaChart.destroy(); cgpaChart = null; }
  if (!cgpaRecords.length) {
    // Hide canvas, show message — don't replace the canvas or wrapper
    ctx.style.display = 'none';
    const existing = ctx.parentElement.querySelector('.cgpa-no-data');
    if (!existing) {
      const msg = document.createElement('p');
      msg.className = 'cgpa-no-data';
      msg.style.cssText = 'color:var(--text-muted);font-size:12.5px;text-align:center;padding:24px;margin:0';
      msg.textContent = 'Add semester records to see trend chart';
      ctx.parentElement.appendChild(msg);
    }
    return;
  }
  // Restore canvas if it was hidden
  ctx.style.display = '';
  const noDataMsg = ctx.parentElement.querySelector('.cgpa-no-data');
  if (noDataMsg) noDataMsg.remove();

  cgpaChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: cgpaRecords.map(r => `Sem ${r.semester}`),
      datasets: [{
        label: 'GPA',
        data: cgpaRecords.map(r => r.gpa),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59,130,246,0.08)',
        borderWidth: 2.5, pointRadius: 5,
        pointBackgroundColor: '#3B82F6',
        tension: 0.4, fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false, // parent div has fixed height:200px — safe
      animation: { duration: 400 },
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#8B949E', font: { size: 11 } } },
        y: { min: 0, max: 10,
             grid: { color: 'rgba(255,255,255,0.04)' },
             ticks: { color: '#8B949E', font: { size: 11 }, stepSize: 1 } },
      },
    },
  });
}

function openCGPAModal() {
  document.getElementById('cgpa-semester').value = '';
  document.getElementById('cgpa-gpa').value      = '';
  document.getElementById('cgpa-credits').value  = '';
  document.getElementById('cgpa-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('cgpa-semester').focus(), 100);
}

function closeCGPAModal() {
  document.getElementById('cgpa-modal').classList.add('hidden');
}

async function saveCGPA() {
  const semester = parseInt(document.getElementById('cgpa-semester').value);
  const gpa      = parseFloat(document.getElementById('cgpa-gpa').value);
  const credits  = parseFloat(document.getElementById('cgpa-credits').value) || null;
  if (!semester) { showToast('Semester number is required', 'warning'); return; }
  if (isNaN(gpa) || gpa < 0 || gpa > 10) { showToast('Enter a valid GPA (0–10)', 'warning'); return; }
  try {
    await api('POST', '/api/cgpa', { semester, gpa, credits });
    showToast('CGPA record added!', 'success');
    closeCGPAModal();
    await loadCGPA();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

async function deleteCGPARecord(id) {
  if (!confirm('Delete this semester record?')) return;
  try {
    await api('DELETE', `/api/cgpa/${id}`);
    showToast('Record deleted', 'success');
    await loadCGPA();
  } catch(e) { showToast(e.message, 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeCGPAModal(); });
document.addEventListener('DOMContentLoaded', loadCGPA);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'cgpa') loadCGPA(); });
