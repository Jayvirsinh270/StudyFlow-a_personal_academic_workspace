/* ── settings.js ── */
async function loadSettings() {
  if (!document.getElementById('profile-name')) return; // not on this page
  try {
    const [profile, settings] = await Promise.all([
      api('GET', '/api/profile'),
      api('GET', '/api/settings'),
    ]);

    document.getElementById('profile-name').value       = profile.name || '';
    document.getElementById('profile-enrollment').value = profile.enrollment_number || '';
    document.getElementById('profile-dept').value       = profile.department || '';
    document.getElementById('profile-semester').value   = profile.semester || '';

    const toggle = document.getElementById('settings-theme-toggle');
    if (toggle) toggle.checked = settings.theme_mode === 'light';
  } catch(e) { showToast('Failed to load settings', 'error'); }
}

async function saveProfile() {
  const name       = document.getElementById('profile-name').value.trim();
  const enrollment = document.getElementById('profile-enrollment').value.trim();
  const dept       = document.getElementById('profile-dept').value.trim();
  const semester   = parseInt(document.getElementById('profile-semester').value) || null;

  if (!name) { showToast('Name is required', 'warning'); return; }
  try {
    await api('POST', '/api/profile', { name, enrollment_number: enrollment, department: dept, semester });
    showToast('Profile saved!', 'success');
    // Refresh profile chip in header/sidebar
    if (window.loadProfileChip) window.loadProfileChip();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

function settingsToggleTheme(isLight) {
  const mode = isLight ? 'light' : 'dark';
  if (window.applyTheme) window.applyTheme(mode);
  else document.documentElement.setAttribute('data-theme', mode);

  // Sync sidebar toggle too
  const sidebarToggle = document.getElementById('theme-toggle');
  if (sidebarToggle) sidebarToggle.checked = isLight;

  api('POST', '/api/settings', { theme_mode: mode }).catch(() => {});
}

async function exportData() {
  showToast('Export feature — backup your UserData folder manually.', 'info');
}

function confirmReset() {
  document.getElementById('reset-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeResetModal() {
  document.getElementById('reset-modal').classList.add('hidden');
}

async function doReset() {
  // This is a destructive no-op for safety — only show a toast
  showToast('Reset not implemented for safety. Delete the database file manually.', 'warning', 5000);
  closeResetModal();
}

// Enter key saves profile
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeResetModal();
  if (e.key === 'Enter' && document.activeElement?.closest('#profile-name, #profile-enrollment, #profile-dept, #profile-semester')) {
    saveProfile();
  }
});

document.addEventListener('DOMContentLoaded', loadSettings);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'settings') loadSettings(); });
