/* ── notes.js ── */
let allNotes        = [];
let allNotesSubjects = [];
let editingNoteId    = null;

async function loadNotes() {
  if (!document.getElementById('notes-grid')) return; // not on this page
  try {
    [allNotes, allNotesSubjects] = await Promise.all([
      api('GET', '/api/notes'),
      api('GET', '/api/subjects'),
    ]);
    const subFilter = document.getElementById('note-subject-filter');
    const modalSel  = document.getElementById('note-subject');
    const opts = allNotesSubjects.map(s => `<option value="${s.id}">${escHtml(s.name)}</option>`).join('');
    if (subFilter) subFilter.innerHTML = '<option value="all">All Subjects</option>' + opts;
    if (modalSel)  modalSel.innerHTML  = '<option value="">— No Subject —</option>' + opts;
    filterNotes();
  } catch(e) { showToast('Failed to load notes', 'error'); }
}

function filterNotes(q) {
  const query = (q || document.getElementById('note-search')?.value || '').toLowerCase();
  const subId = document.getElementById('note-subject-filter')?.value || 'all';
  const filtered = allNotes.filter(n => {
    if (subId !== 'all' && String(n.subject_id) !== subId) return false;
    if (query && !(n.title || '').toLowerCase().includes(query) && !(n.content || '').toLowerCase().includes(query)) return false;
    return true;
  });
  renderNotes(filtered);
}

function renderNotes(list) {
  const grid = document.getElementById('notes-grid');
  if (!grid) return;
  if (!list.length) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;padding:60px">
        <div class="empty-icon"><i data-lucide="notebook-pen"></i></div>
        <h3>${allNotes.length ? 'No notes match your filter' : 'No notes yet'}</h3>
        <p>${allNotes.length ? 'Try adjusting filters.' : 'Create your first note for any subject.'}</p>
        ${!allNotes.length ? '<button class="btn btn-primary mt-4" onclick="openNoteModal()"><i data-lucide="plus"></i> New Note</button>' : ''}
      </div>`;
    if (window.lucide) lucide.createIcons();
    return;
  }
  const subjMap = Object.fromEntries(allNotesSubjects.map(s => [s.id, s]));
  grid.innerHTML = list.map(n => {
    const subj    = subjMap[n.subject_id];
    const color   = subj?.color || 'var(--accent)';
    const preview = (n.content || '').substring(0, 120);
    const pinned  = !!n.is_pinned;
    const updAt   = n.updated_at ? new Date(n.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
    return `
      <div class="note-card${pinned ? ' pinned' : ''}" onclick="openNoteModal(${n.id})">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">
          <div style="width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0"></div>
          ${subj ? `<span style="font-size:11px;color:var(--text-muted);font-weight:500">${escHtml(subj.name)}</span>` : ''}
        </div>
        <h4>${escHtml(n.title || 'Untitled')}</h4>
        ${preview ? `<p>${escHtml(preview)}${(n.content||'').length > 120 ? '…' : ''}</p>` : '<p style="color:var(--text-muted);font-style:italic">Empty note</p>'}
        <div class="note-card-footer">
          <span style="font-size:11px;color:var(--text-muted)">${updAt}</span>
          ${pinned ? '<span style="font-size:10px;color:var(--warning);font-weight:600">PINNED</span>' : ''}
        </div>
      </div>`;
  }).join('');
  if (window.lucide) lucide.createIcons();
}

function openNoteModal(id) {
  const isEdit = !!id;
  editingNoteId = id || null;
  document.getElementById('note-modal-title').textContent = isEdit ? 'Edit Note' : 'New Note';
  document.getElementById('note-edit-id').value  = id || '';
  const delBtn = document.getElementById('note-delete-btn');
  if (delBtn) delBtn.style.display = isEdit ? 'inline-flex' : 'none';

  if (isEdit) {
    const n = allNotes.find(x => x.id === id);
    if (n) {
      document.getElementById('note-title').value   = n.title || '';
      document.getElementById('note-subject').value = n.subject_id || '';
      document.getElementById('note-content').value = n.content || '';
      document.getElementById('note-pinned').checked = !!n.is_pinned;
    }
  } else {
    document.getElementById('note-title').value   = '';
    document.getElementById('note-subject').value = '';
    document.getElementById('note-content').value = '';
    document.getElementById('note-pinned').checked = false;
  }
  document.getElementById('note-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
  setTimeout(() => document.getElementById('note-title').focus(), 100);
}

function closeNoteModal() {
  document.getElementById('note-modal').classList.add('hidden');
  editingNoteId = null;
}

async function saveNote() {
  const id      = document.getElementById('note-edit-id').value;
  const title   = document.getElementById('note-title').value.trim();
  const subId   = parseInt(document.getElementById('note-subject').value) || null;
  const content = document.getElementById('note-content').value;
  const pinned  = document.getElementById('note-pinned').checked;
  if (!title) { showToast('Title is required', 'warning'); return; }
  if (!subId) { showToast('Please select a subject', 'warning'); return; }
  try {
    if (id) {
      await api('PUT', `/api/notes/${id}`, { title, content, is_pinned: pinned });
      showToast('Note updated', 'success');
    } else {
      await api('POST', '/api/notes', { subject_id: subId, title, content });
      if (pinned) {
        const notes = await api('GET', '/api/notes');
        const newest = notes[0];
        if (newest) await api('PUT', `/api/notes/${newest.id}`, { is_pinned: true });
      }
      showToast('Note created!', 'success');
    }
    closeNoteModal();
    await loadNotes();
  } catch(e) { showToast(e.message || 'Save failed', 'error'); }
}

async function deleteNote() {
  if (!editingNoteId) return;
  if (!confirm('Delete this note?')) return;
  try {
    await api('DELETE', `/api/notes/${editingNoteId}`);
    showToast('Note deleted', 'success');
    closeNoteModal();
    await loadNotes();
  } catch(e) { showToast(e.message, 'error'); }
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeNoteModal(); });
document.addEventListener('DOMContentLoaded', loadNotes);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'notes') loadNotes(); });
