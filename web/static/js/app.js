/* ============================================================
   StudyFlow — app.js
   Core: SPA router, clock, theme, toast, search overlay
   ============================================================ */

/* ── API helper ───────────────────────────────────────────── */
async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' }
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const json = await res.json();
  if (json.error) throw new Error(json.error);
  return json.data;
}
window.api = api;

/* ── SPA Navigation ──────────────────────────────────────── */
const PAGE_TITLES = {
  dashboard:   'Dashboard',
  subjects:    'Subjects',
  assignments: 'Assignments',
  attendance:  'Attendance',
  timetable:   'Timetable',
  planner:     'Planner',
  calendar:    'Calendar',
  pomodoro:    'Focus Timer',
  cgpa:        'CGPA Calculator',
  documents:   'Documents',
  notes:       'Notes',
  settings:    'Settings',
};

// Track if a navigation is in-flight to prevent double loads
let _navInFlight = false;

async function navigateTo(page) {
  if (_navInFlight) return;
  _navInFlight = true;
  try {
    const content = document.getElementById('content-area');

    // Fade out
    content.style.opacity = '0.4';
    content.style.transition = 'opacity 80ms ease';

    const res  = await fetch(`/${page}?partial=1`);
    const html = await res.text();

    // Use a temp div to parse HTML — strips scripts safely
    const tmp = document.createElement('div');
    tmp.innerHTML = html;

    // Remove any <script> tags from partial (JS is loaded globally in base.html)
    tmp.querySelectorAll('script').forEach(s => s.remove());

    // Inject clean HTML
    content.innerHTML = tmp.innerHTML;
    content.scrollTop = 0;

    // Fade in
    content.style.opacity = '1';

    // Update breadcrumb
    const titleEl = document.getElementById('page-title');
    if (titleEl) titleEl.textContent = PAGE_TITLES[page] || page;

    // Update sidebar active state
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.page === page);
    });

    // Push browser history
    if (history.state && history.state.page !== page) {
      history.pushState({ page }, '', `/${page}`);
    } else if (!history.state) {
      history.pushState({ page }, '', `/${page}`);
    }

    // Re-init Lucide icons in new content
    if (window.lucide) lucide.createIcons();

    // Fire page-specific init AFTER DOM is ready
    const evt = new CustomEvent('pageLoaded', { detail: { page } });
    document.dispatchEvent(evt);

  } catch (e) {
    console.error('Navigation error:', e);
    showToast('Navigation failed', 'error');
  } finally {
    _navInFlight = false;
  }
}
window.navigateTo = navigateTo;

// Intercept sidebar nav item clicks
document.addEventListener('click', e => {
  const navItem = e.target.closest('.nav-item[data-page]');
  if (navItem) {
    e.preventDefault();
    navigateTo(navItem.dataset.page);
  }
});

// Browser back/forward
window.addEventListener('popstate', e => {
  const page = (e.state && e.state.page) || 'dashboard';
  navigateTo(page);
});

// Keyboard shortcuts: Alt+1..9 for quick nav
document.addEventListener('keydown', e => {
  if (!e.altKey) return;
  const pageMap = {
    '1':'dashboard','2':'subjects','3':'assignments','4':'attendance',
    '5':'planner','6':'calendar','7':'pomodoro','8':'documents','9':'cgpa','0':'settings'
  };
  if (pageMap[e.key]) { e.preventDefault(); navigateTo(pageMap[e.key]); }
});

/* ── Clock ───────────────────────────────────────────────── */
function updateClock() {
  const el = document.getElementById('header-clock');
  if (!el) return;
  const now = new Date();
  const h = now.getHours().toString().padStart(2, '0');
  const m = now.getMinutes().toString().padStart(2, '0');
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  el.textContent = `${days[now.getDay()]}  ${h}:${m}`;
}
updateClock();
setInterval(updateClock, 30000);

/* ── Theme ───────────────────────────────────────────────── */
function applyTheme(mode) {
  document.documentElement.setAttribute('data-theme', mode === 'light' ? 'light' : '');
  const toggle = document.getElementById('theme-toggle');
  if (toggle) toggle.checked = (mode === 'light');
}
window.applyTheme = applyTheme;

function toggleTheme() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const newMode = isLight ? 'dark' : 'light';
  applyTheme(newMode);
  api('POST', '/api/settings', { theme_mode: newMode }).catch(() => {});
}
window.toggleTheme = toggleTheme;

// Load saved theme
(async () => {
  try {
    const s = await api('GET', '/api/settings');
    applyTheme(s.theme_mode || 'dark');
  } catch {}
})();

/* ── Profile chip ─────────────────────────────────────────── */
async function loadProfileChip() {
  try {
    const p = await api('GET', '/api/profile');
    const nameEl = document.getElementById('profile-chip-name');
    const initEl = document.getElementById('profile-chip-init');
    const sidebarNameEl = document.getElementById('sidebar-profile-name');
    const sidebarSubEl  = document.getElementById('sidebar-profile-sub');
    const sidebarInitEl = document.getElementById('sidebar-profile-init');
    const name = p.name || 'Student';
    const init = name.charAt(0).toUpperCase();
    if (nameEl)  nameEl.textContent = name.split(' ')[0];
    if (initEl)  initEl.textContent = init;
    if (sidebarNameEl) sidebarNameEl.textContent = name;
    if (sidebarSubEl)  sidebarSubEl.textContent  = [p.department, p.semester ? `Sem ${p.semester}` : ''].filter(Boolean).join(' · ');
    if (sidebarInitEl) sidebarInitEl.textContent = init;
  } catch {}
}
window.loadProfileChip = loadProfileChip;
loadProfileChip();

/* ── Toast notifications ──────────────────────────────────── */
const TOAST_ICONS = {
  success: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--success)"><polyline points="20 6 9 17 4 12"/></svg>',
  error:   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--danger)"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  info:    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--info)"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
  warning: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--warning)"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
};

function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span class="toast-icon">${TOAST_ICONS[type]||TOAST_ICONS.info}</span><span class="toast-msg">${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('leaving');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}
window.showToast = showToast;

/* ── Search Overlay ───────────────────────────────────────── */
let searchResults = [];
let searchFocused = 0;

function openSearch() {
  const overlay = document.getElementById('search-overlay');
  if (!overlay) return;
  overlay.classList.remove('hidden');
  const inp = overlay.querySelector('#search-input');
  if (inp) { inp.value = ''; inp.focus(); }
  searchResults = [];
  renderSearchResults([]);
}

function closeSearch() {
  const overlay = document.getElementById('search-overlay');
  if (overlay) overlay.classList.add('hidden');
}

async function doSearch(q) {
  if (!q.trim()) { renderSearchResults([]); return; }
  try {
    const data = await api('GET', `/api/search?q=${encodeURIComponent(q)}`);
    searchResults = data;
    searchFocused = 0;
    renderSearchResults(data);
  } catch {}
}

const TYPE_META = {
  subject:    { bg: '#1E3A5F', icon: '📚' },
  assignment: { bg: '#2D1F0A', icon: '📝' },
  note:       { bg: '#0F2A1A', icon: '🗒️' },
  file:       { bg: '#2A1040', icon: '📄' },
};

function renderSearchResults(results) {
  const container = document.getElementById('search-results');
  if (!container) return;
  if (!results.length) {
    container.innerHTML = '<div class="search-empty">Type to search subjects, assignments, notes and files…</div>';
    return;
  }
  container.innerHTML = results.map((r, i) => {
    const meta = TYPE_META[r.type] || TYPE_META.file;
    return `
      <div class="search-result-item ${i === searchFocused ? 'focused' : ''}"
           onclick="goSearchResult('${r.url}')" data-idx="${i}">
        <div class="search-result-icon" style="background:${meta.bg}">${meta.icon}</div>
        <div class="search-result-info">
          <h4>${escHtml(r.title)}</h4>
          ${r.subtitle ? `<p>${escHtml(r.subtitle)}</p>` : ''}
        </div>
        <span class="badge badge-gray search-result-badge" style="text-transform:capitalize">${r.type}</span>
      </div>`;
  }).join('');
}

function goSearchResult(url) {
  closeSearch();
  const page = url.replace('/', '') || 'dashboard';
  navigateTo(page);
}
window.goSearchResult = goSearchResult;

// Keyboard events for search
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault(); openSearch();
  }
  if (e.key === 'Escape') closeSearch();
  const overlay = document.getElementById('search-overlay');
  if (!overlay || overlay.classList.contains('hidden')) return;
  if (e.key === 'ArrowDown') {
    searchFocused = Math.min(searchFocused + 1, searchResults.length - 1);
    renderSearchResults(searchResults);
  } else if (e.key === 'ArrowUp') {
    searchFocused = Math.max(searchFocused - 1, 0);
    renderSearchResults(searchResults);
  } else if (e.key === 'Enter' && searchResults[searchFocused]) {
    goSearchResult(searchResults[searchFocused].url);
  }
});

// Debounced search input
let searchTimer;
document.addEventListener('input', e => {
  if (e.target.id === 'search-input') {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => doSearch(e.target.value), 280);
  }
  if (e.target.id === 'header-search-input') {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { openSearch(); doSearch(e.target.value); }, 280);
  }
});

window.openSearch = openSearch;
window.closeSearch = closeSearch;

/* ── Utility: escape HTML ─────────────────────────────────── */
function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
window.escHtml = escHtml;

/* ── Utility: format date ─────────────────────────────────── */
function fmtDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return dateStr; }
}
window.fmtDate = fmtDate;

function fmtDateShort(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch { return dateStr; }
}
window.fmtDateShort = fmtDateShort;

/* ── Partial flag support (server-side) ───────────────────── */
// Flask returns full page or just block content based on ?partial=1
// This is handled server-side in app.py

/* ── Init Lucide icons after DOM ─────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
});
document.addEventListener('pageLoaded', () => {
  if (window.lucide) lucide.createIcons();
  // re-run page-specific scripts
});
