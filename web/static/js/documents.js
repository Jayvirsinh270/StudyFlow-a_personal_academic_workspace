/* ── documents.js ── */
let allDocs        = [];
let allDocsSubjects = [];
let activeDocType   = 'all';
let pendingFilePath = null;

const FILE_ICONS = {
  PDF:   { icon: '📄', bg: '#1A0A0A', color: '#F87171' },
  Image: { icon: '🖼️', bg: '#0A1A10', color: '#4ADE80' },
  Word:  { icon: '📝', bg: '#0A0F1A', color: '#60A5FA' },
  Other: { icon: '📎', bg: '#130A1A', color: '#A78BFA' },
};

async function loadDocuments() {
  if (!document.getElementById('docs-grid')) return; // not on this page
  try {
    [allDocs, allDocsSubjects] = await Promise.all([
      api('GET', '/api/documents'),
      api('GET', '/api/subjects'),
    ]);
    const subFilter = document.getElementById('doc-subject-filter');
    const uploadSel = document.getElementById('upload-subject');
    const opts = allDocsSubjects.map(s => `<option value="${s.id}">${escHtml(s.name)}</option>`).join('');
    if (subFilter) subFilter.innerHTML = '<option value="all">All Subjects</option>' + opts;
    if (uploadSel) uploadSel.innerHTML = '<option value="">— No Subject —</option>' + opts;
    filterDocs();
  } catch(e) { showToast('Failed to load documents', 'error'); }
}

function setDocType(type, el) {
  activeDocType = type;
  document.querySelectorAll('#doc-type-tabs .filter-tab').forEach(t => t.classList.remove('active'));
  if (el) el.classList.add('active');
  filterDocs();
}

function filterDocs(q) {
  const query  = (q || document.getElementById('doc-search')?.value || '').toLowerCase();
  const subId  = document.getElementById('doc-subject-filter')?.value || 'all';

  const filtered = allDocs.filter(f => {
    if (activeDocType !== 'all' && (f.file_type || 'Other') !== activeDocType) return false;
    if (subId !== 'all' && String(f.subject_id) !== subId) return false;
    if (query && !(f.file_name || '').toLowerCase().includes(query)) return false;
    return true;
  });
  renderDocuments(filtered);
}

function renderDocuments(list) {
  const grid = document.getElementById('docs-grid');
  if (!grid) return;
  if (!list.length) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;padding:60px">
        <div class="empty-icon"><i data-lucide="file-stack"></i></div>
        <h3>${allDocs.length ? 'No files match your filter' : 'No documents yet'}</h3>
        <p>${allDocs.length ? 'Try changing filters.' : 'Upload your first file to get started.'}</p>
        ${!allDocs.length ? '<button class="btn btn-primary mt-4" onclick="uploadDocument()"><i data-lucide="upload"></i> Upload File</button>' : ''}
      </div>`;
    if (window.lucide) lucide.createIcons();
    return;
  }

  const subjMap = Object.fromEntries(allDocsSubjects.map(s => [s.id, s]));
  grid.innerHTML = list.map(f => {
    const type   = f.file_type || 'Other';
    const meta   = FILE_ICONS[type] || FILE_ICONS.Other;
    const subj   = subjMap[f.subject_id];
    const sizeKB = f.file_size ? (f.file_size / 1024).toFixed(0) + ' KB' : '';
    return `
      <div class="doc-card card-hover" onclick="openDoc(${f.id})">
        <div class="doc-icon" style="background:${meta.bg}">
          <span style="font-size:22px">${meta.icon}</span>
        </div>
        <div class="doc-name truncate">${escHtml(f.file_name || 'Unnamed')}</div>
        <div class="doc-meta">
          <span class="badge" style="background:${meta.bg};color:${meta.color};border-color:${meta.color}33">${type}</span>
          ${subj ? `<span class="badge" style="background:${subj.color||'#6366F1'}22;color:${subj.color||'var(--accent)'};border-color:${subj.color||'var(--accent)'}44;max-width:90px;overflow:hidden;text-overflow:ellipsis">${escHtml(subj.name)}</span>` : ''}
        </div>
        ${sizeKB ? `<span style="font-size:11px;color:var(--text-muted)">${sizeKB}</span>` : ''}
        <div class="doc-actions">
          <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openDoc(${f.id})">
            <i data-lucide="external-link"></i> Open
          </button>
          <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();deleteDoc(${f.id})" style="color:var(--danger)">
            <i data-lucide="trash-2"></i>
          </button>
        </div>
      </div>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

async function openDoc(id) {
  try {
    await api('POST', `/api/documents/open/${id}`);
  } catch(e) { showToast('Could not open file — it may have been moved or deleted.', 'error'); }
}

async function uploadDocument() {
  // Try pywebview file dialog first
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_file_dialog) {
    try {
      const path = await window.pywebview.api.open_file_dialog();
      if (path) {
        pendingFilePath = path;
        const fileName = path.split(/[\\/]/).pop();
        document.getElementById('upload-filename').textContent = fileName;
        document.getElementById('upload-modal').classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
      }
    } catch(e) { fallbackFileInput(); }
  } else {
    fallbackFileInput();
  }
}

function fallbackFileInput() {
  const input = document.createElement('input');
  input.type = 'file';
  input.onchange = async (ev) => {
    const file = ev.target.files[0];
    if (!file) return;
    document.getElementById('upload-filename').textContent = file.name;
    pendingFilePath = null;
    // Store file for form upload
    window._pendingFile = file;
    document.getElementById('upload-modal').classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
  };
  input.click();
}

function closeUploadModal() {
  document.getElementById('upload-modal').classList.add('hidden');
  pendingFilePath = null;
  window._pendingFile = null;
}

async function confirmUpload() {
  const subjectId = document.getElementById('upload-subject').value || null;
  const btn = document.querySelector('#upload-modal .btn-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Uploading…'; }
  try {
    if (pendingFilePath) {
      // pywebview native-dialog path — send as form field, server copies the file
      const formData = new FormData();
      formData.append('local_path', pendingFilePath);
      if (subjectId) formData.append('subject_id', subjectId);
      const res  = await fetch('/api/documents/upload', { method: 'POST', body: formData });
      const json = await res.json();
      if (json.error) throw new Error(json.error);
      showToast(`${json.data.file_name} uploaded!`, 'success');
    } else if (window._pendingFile) {
      // Browser <input type="file"> multipart upload
      const file = window._pendingFile;
      const formData = new FormData();
      formData.append('file', file);
      if (subjectId) formData.append('subject_id', subjectId);
      const res  = await fetch('/api/documents/upload', { method: 'POST', body: formData });
      const json = await res.json();
      if (json.error) throw new Error(json.error);
      showToast(`${file.name} uploaded!`, 'success');
    } else {
      showToast('No file selected — please pick a file first.', 'warning');
      return;
    }
    closeUploadModal();
    await loadDocuments();
  } catch(e) {
    showToast(e.message || 'Upload failed', 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="upload"></i> Upload'; if(window.lucide) lucide.createIcons(); }
  }
}

async function deleteDoc(id) {
  if (!confirm('Delete this file record?')) return;
  try {
    await api('DELETE', `/api/documents/${id}`);
    showToast('File deleted', 'success');
    await loadDocuments();
  } catch(e) { showToast(e.message, 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeUploadModal(); });
document.addEventListener('DOMContentLoaded', loadDocuments);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'documents') loadDocuments(); });
