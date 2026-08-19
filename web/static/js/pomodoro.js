/* ── pomodoro.js ── */
const MODES = {
  work:  { label: 'FOCUS',       color: '#2563EB', ringColor: '#3B82F6' },
  short: { label: 'SHORT BREAK', color: '#22C55E', ringColor: '#4ADE80' },
  long:  { label: 'LONG BREAK',  color: '#7C3AED', ringColor: '#A78BFA' },
};
const QUOTES = [
  "Focus on progress, not perfection.",
  "Small steps every day lead to big results.",
  "Deep work is the superpower of the 21st century.",
  "Your future self will thank you for studying today.",
  "Discipline is choosing between what you want now and what you want most.",
  "Success is the sum of small efforts repeated day in and day out.",
  "The secret of getting ahead is getting started.",
  "Knowledge is power. Study hard.",
];

let pomodoroMode      = 'work';
let pomodoroRunning   = false;
let pomodoroRemaining = 25 * 60;
let pomodoroTotal     = 25 * 60;
let pomodoroTimer     = null;
let sessionCount      = 0;
let sessionLog        = [];

function getDurations() {
  return {
    work:  (parseInt(document.getElementById('work-duration')?.value)  || 25) * 60,
    short: (parseInt(document.getElementById('short-break')?.value)    || 5)  * 60,
    long:  (parseInt(document.getElementById('long-break')?.value)     || 15) * 60,
  };
}

function setMode(mode) {
  if (pomodoroRunning) stopTimer();
  pomodoroMode = mode;
  const durations = getDurations();
  pomodoroTotal     = durations[mode];
  pomodoroRemaining = pomodoroTotal;

  document.querySelectorAll('.timer-mode-tab').forEach(el => el.classList.remove('active'));
  const tabEl = document.getElementById(`mode-${mode}`);
  if (tabEl) tabEl.classList.add('active');

  const m = MODES[mode];
  const ring = document.getElementById('timer-ring');
  if (ring) { ring.style.stroke = m.ringColor; ring.style.strokeDashoffset = '0'; }
  updateTimerDisplay();
  updateModeLabel();
  showRandomQuote();
}

function updateTimerDisplay() {
  const m = Math.floor(pomodoroRemaining / 60).toString().padStart(2, '0');
  const s = (pomodoroRemaining % 60).toString().padStart(2, '0');
  const el = document.getElementById('timer-display');
  if (el) el.textContent = `${m}:${s}`;
}

function updateModeLabel() {
  const el = document.getElementById('timer-mode-label');
  if (el) el.textContent = MODES[pomodoroMode]?.label || 'FOCUS';
}

function updateRing() {
  const ring = document.getElementById('timer-ring');
  if (!ring) return;
  const circ  = 2 * Math.PI * 108;
  const off   = circ - (pomodoroRemaining / pomodoroTotal) * circ;
  ring.style.strokeDasharray  = circ.toString();
  ring.style.strokeDashoffset = off.toString();
}

function toggleTimer() {
  if (pomodoroRunning) stopTimer();
  else startTimer();
}

function startTimer() {
  pomodoroRunning = true;
  const playIcon  = document.getElementById('play-icon');
  if (playIcon) {
    playIcon.setAttribute('data-lucide', 'pause');
    if (window.lucide) lucide.createIcons();
  }
  pomodoroTimer = setInterval(() => {
    pomodoroRemaining--;
    updateTimerDisplay();
    updateRing();
    if (pomodoroRemaining <= 0) {
      clearInterval(pomodoroTimer);
      pomodoroRunning = false;
      onSessionComplete();
    }
  }, 1000);
}

function stopTimer() {
  clearInterval(pomodoroTimer);
  pomodoroRunning = false;
  const playIcon = document.getElementById('play-icon');
  if (playIcon) {
    playIcon.setAttribute('data-lucide', 'play');
    if (window.lucide) lucide.createIcons();
  }
}

function resetTimer() {
  stopTimer();
  const durations = getDurations();
  pomodoroTotal     = durations[pomodoroMode];
  pomodoroRemaining = pomodoroTotal;
  updateTimerDisplay();
  updateRing();
}

function skipSession() {
  stopTimer();
  onSessionComplete();
}

function onSessionComplete() {
  const playIcon = document.getElementById('play-icon');
  if (playIcon) { playIcon.setAttribute('data-lucide', 'play'); if (window.lucide) lucide.createIcons(); }

  if (pomodoroMode === 'work') {
    sessionCount++;
    const now = new Date();
    sessionLog.unshift({
      label: `Work session #${sessionCount}`,
      time: now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      color: MODES.work.ringColor,
    });
    renderSessionDots();
    renderSessionLog();
    showToast('Focus session complete! Take a break.', 'success');
    // Auto-switch to break
    if (sessionCount % 4 === 0) setMode('long');
    else setMode('short');
  } else {
    showToast('Break over! Time to focus.', 'info');
    setMode('work');
  }
}

function renderSessionDots() {
  const el = document.getElementById('session-dots');
  if (!el) return;
  const count = sessionCount % 4 || (sessionCount > 0 ? 4 : 0);
  el.innerHTML = Array.from({ length: 4 }, (_, i) => `
    <div style="width:10px;height:10px;border-radius:50%;background:${i < count ? MODES.work.ringColor : 'var(--border)'}"></div>
  `).join('');
}

function renderSessionLog() {
  const el = document.getElementById('session-log');
  if (!el) return;
  if (!sessionLog.length) {
    el.innerHTML = '<div class="empty-state" style="padding:20px"><p style="font-size:12px;color:var(--text-muted)">No sessions yet.</p></div>';
    return;
  }
  el.innerHTML = sessionLog.slice(0, 8).map(s => `
    <div class="session-item">
      <div class="session-dot" style="background:${s.color}"></div>
      <span style="flex:1">${escHtml(s.label)}</span>
      <span style="font-size:11px;color:var(--text-muted)">${s.time}</span>
    </div>`).join('');
}

function clearLog() {
  sessionLog = [];
  sessionCount = 0;
  renderSessionLog();
  renderSessionDots();
  resetTimer();
}

function updateDurations() {
  if (!pomodoroRunning) resetTimer();
}

function showRandomQuote() {
  const el = document.getElementById('motivation-quote');
  if (el) el.textContent = `"${QUOTES[Math.floor(Math.random() * QUOTES.length)]}"`;
}

function initPomodoro() {
  if (!document.getElementById('timer-display')) return; // not on this page
  setMode('work');
  renderSessionDots();
  renderSessionLog();
  updateRing();
}

document.addEventListener('DOMContentLoaded', initPomodoro);
document.addEventListener('pageLoaded', e => { if (e.detail.page === 'pomodoro') initPomodoro(); });
