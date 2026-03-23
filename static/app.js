/* ============================================================
   VocabMaster SPA — app.js
   ============================================================ */

// ── API Layer ─────────────────────────────────────────────────
const CSRF = () => document.querySelector('meta[name="csrf-token"]')?.content || '';

async function api(method, url, body) {
  const opts = {
    method,
    credentials: 'same-origin',
    headers: { 'X-CSRF-Token': CSRF() },
    signal: AbortSignal.timeout(15000),
  };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || err.message || `HTTP ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

const apiGet    = url => api('GET', url);
const apiPost   = (url, b) => api('POST', url, b);
const apiPut    = (url, b) => api('PUT', url, b);
const apiDelete = url => api('DELETE', url);

// ── Toast ─────────────────────────────────────────────────────
function toast(msg, type = 'info', duration = 3000) {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  // Error toasts are dismissible by click; longer duration
  const d = type === 'error' ? Math.max(duration, 5000) : duration;
  const inner = document.createElement('span');
  inner.textContent = msg;
  el.appendChild(inner);
  // X dismiss button
  const x = document.createElement('button');
  x.className = 'toast-dismiss';
  x.setAttribute('aria-label', '關閉');
  x.textContent = '×';
  x.onclick = () => { el.classList.add('fade-out'); el.addEventListener('animationend', () => el.remove(), { once: true }); };
  el.appendChild(x);
  c.appendChild(el);
  const tid = setTimeout(() => {
    el.classList.add('fade-out');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, d);
  el.addEventListener('click', () => clearTimeout(tid)); // clicking pauses auto-dismiss
}

// ── State ─────────────────────────────────────────────────────
const state = {
  tab: 'today',
  stats: null,
  dueCount: 0,
  practiceFolder: 'all',
  practiceMode: 'due',
  libFolder: 'all',
  libSearch: '',
  libWords: [],
  libPage: 0,
  libHasMore: true,
  libLoading: false,
  folders: [],
  session: null,
};

// ── Router (tabs) ─────────────────────────────────────────────
function switchTab(tab) {
  state.tab = tab;
  try { sessionStorage.setItem('vm_tab', tab); } catch {}
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  if (tab === 'today')    renderToday();
  if (tab === 'practice') renderPractice();
  if (tab === 'library')  renderLibrary();
}

// ── Today Tab ─────────────────────────────────────────────────
async function renderToday() {
  // Show loading placeholder if not yet loaded
  if (!state.stats) {
    ['streak-count','due-num','total-words-stat','folders-stat'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = '…';
    });
  }
  try {
    const [stats, dueData] = await Promise.all([
      apiGet('/api/statistics'),
      apiGet('/api/due?limit=1'),
    ]);
    state.stats = stats;
    state.dueCount = dueData.total ?? (dueData.words?.length ?? 0);
    updateTodayUI();
  } catch (e) {
    toast('無法載入今日資料，請重新整理', 'error');
  }
}

function updateTodayUI() {
  const s = state.stats || {};
  const due = state.dueCount;
  const streak = s.streak ?? 0;

  document.getElementById('streak-count').textContent = streak;

  const total = s.total_words ?? 0;
  const r = 52;
  const circ = 2 * Math.PI * r;
  const done = Math.max(0, total - due);
  const progress = total > 0 ? done / total : 0;
  const ringEl = document.getElementById('due-ring-fg');
  ringEl.style.strokeDasharray = circ;
  ringEl.style.strokeDashoffset = circ * (1 - progress);

  document.getElementById('due-num').textContent = due;
  document.getElementById('total-words-stat').textContent = total;
  document.getElementById('folders-stat').textContent = s.total_folders ?? 0;

  const cta = document.getElementById('today-cta');
  const doneBanner = document.getElementById('today-done');
  if (due === 0 && total > 0) {
    cta.classList.add('hidden');
    doneBanner.classList.remove('hidden');
  } else {
    cta.classList.remove('hidden');
    doneBanner.classList.add('hidden');
  }
}

// ── Practice Tab ──────────────────────────────────────────────
async function renderPractice() {
  await loadFolders();
  renderPracticeFolderPills();
  renderPracticeWordCount();
}

function renderPracticeFolderPills() {
  const wrap = document.getElementById('practice-folder-pills');
  wrap.innerHTML = '';
  ['all', ...state.folders].forEach(f => {
    const btn = document.createElement('button');
    btn.className = 'pill' + (state.practiceFolder === f ? ' active' : '');
    const label = f === 'all' ? '全部' : f;
    btn.textContent = label;
    if (f !== 'all') btn.title = f; // tooltip for full name
    btn.onclick = () => {
      state.practiceFolder = f;
      wrap.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      renderPracticeWordCount();
    };
    wrap.appendChild(btn);
  });
}

async function renderPracticeWordCount() {
  const countEl = document.getElementById('practice-word-count');
  countEl.textContent = '…';
  try {
    const folder = state.practiceFolder === 'all' ? '' : state.practiceFolder;
    const folderQ = folder ? `&folder=${encodeURIComponent(folder)}` : '';
    const url = state.practiceMode === 'due'
      ? `/api/due?limit=1${folderQ}`
      : `/api/words?limit=1${folderQ}`;
    const data = await apiGet(url);
    const cnt = data.total ?? data.words?.length ?? 0;
    countEl.textContent = `${cnt} 個單字`;
  } catch {
    countEl.textContent = '—';
  }
}

async function startSession() {
  const folder = state.practiceFolder === 'all' ? '' : state.practiceFolder;
  const folderQ = folder ? `&folder=${encodeURIComponent(folder)}` : '';
  const startBtn = document.getElementById('practice-start-btn');
  startBtn.disabled = true;
  startBtn.classList.add('btn-loading');
  try {
    const url = state.practiceMode === 'due'
      ? `/api/due?limit=200${folderQ}`
      : `/api/words?limit=200${folderQ}`;
    const data = await apiGet(url);
    const words = data.words || [];
    if (!words.length) { toast('沒有可練習的單字', 'info'); return; }
    state.session = { words, idx: 0, correct: 0, wrong: 0, flipped: false, submitting: false };
    openSession();
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    startBtn.disabled = false;
    startBtn.classList.remove('btn-loading');
  }
}

function openSession() {
  const overlay = document.getElementById('session-overlay');
  overlay.classList.add('active');
  document.getElementById('session-summary').style.display = 'none';
  document.getElementById('session-card-area').style.display = '';
  document.getElementById('session-actions').classList.add('hidden');
  renderSessionCard();
  document.addEventListener('keydown', onSessionKey);
  document.addEventListener('keydown', trapFocus);
  setupSwipe();
  // Move focus into overlay so keyboard works immediately
  setTimeout(() => document.getElementById('session-close-btn')?.focus(), 50);
}

function closeSession() {
  document.getElementById('session-overlay').classList.remove('active');
  document.removeEventListener('keydown', onSessionKey);
  document.removeEventListener('keydown', trapFocus);
  state.session = null;
  document.getElementById('practice-start-btn')?.focus();
}

function trapFocus(e) {
  if (e.key !== 'Tab') return;
  const overlay = document.getElementById('session-overlay');
  if (!overlay?.classList.contains('active')) return;
  const focusable = Array.from(overlay.querySelectorAll('button:not([disabled]), [tabindex="0"]')).filter(el => el.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}

function renderSessionCard() {
  const sess = state.session;
  const word = sess.words[sess.idx];
  const total = sess.words.length;

  document.getElementById('session-count').textContent = `${sess.idx + 1} / ${total}`;
  document.getElementById('session-progress-fill').style.width = `${(sess.idx / total) * 100}%`;

  document.getElementById('card-word').textContent = word.english;
  document.getElementById('card-pos-front').textContent = word.part_of_speech || '';
  document.getElementById('card-pos-back').textContent = word.part_of_speech || '';
  document.getElementById('card-meaning').textContent = word.chinese;
  document.getElementById('card-folder-tag').textContent = word.folder || '';

  const fc = document.getElementById('flip-card');
  fc.classList.remove('flipped', 'tilt-right', 'tilt-left');
  sess.flipped = false;
  document.getElementById('session-actions').classList.add('hidden');
}

function flipCard() {
  const sess = state.session;
  if (!sess || sess.flipped) return;
  sess.flipped = true;
  document.getElementById('flip-card').classList.add('flipped');
  document.getElementById('session-actions').classList.remove('hidden');
}

async function submitReview(quality) {
  const sess = state.session;
  if (!sess || !sess.flipped || sess.submitting) return;
  sess.submitting = true;
  // Lock action buttons to prevent double-tap
  document.getElementById('btn-unknown').disabled = true;
  document.getElementById('btn-know').disabled = true;
  const word = sess.words[sess.idx];
  const fc = document.getElementById('flip-card');
  fc.classList.add(quality >= 3 ? 'tilt-right' : 'tilt-left');
  if (quality >= 3) sess.correct++; else sess.wrong++;
  apiPut(`/api/words/${word.id}/review`, { quality }).catch(e => console.warn('review:', e.message));
  setTimeout(() => {
    sess.submitting = false;
    sess.idx++;
    if (sess.idx >= sess.words.length) showSummary();
    else {
      renderSessionCard();
      document.getElementById('btn-unknown').disabled = false;
      document.getElementById('btn-know').disabled = false;
    }
  }, 260);
}

function showSummary() {
  const sess = state.session;
  const total = sess.correct + sess.wrong;
  const pct = total > 0 ? Math.round((sess.correct / total) * 100) : 0;
  document.getElementById('session-card-area').style.display = 'none';
  document.getElementById('session-actions').classList.add('hidden');
  const sum = document.getElementById('session-summary');
  sum.style.display = 'flex';
  document.getElementById('sum-emoji').textContent = pct >= 80 ? '🎉' : pct >= 50 ? '💪' : '📖';
  document.getElementById('sum-title').textContent = pct >= 80 ? '太棒了！' : pct >= 50 ? '繼續加油！' : '多多練習！';
  document.getElementById('sum-subtitle').textContent = `完成 ${total} 個單字，進度已儲存`;
  document.getElementById('sum-correct').textContent = sess.correct;
  document.getElementById('sum-wrong').textContent = sess.wrong;
  document.getElementById('sum-pct').textContent = pct + '%';
  document.getElementById('session-progress-fill').style.width = '100%';
  document.getElementById('session-count').textContent = `${total} / ${total}`;
  state.dueCount = Math.max(0, state.dueCount - sess.correct);
}

function onSessionKey(e) {
  const tag = e.target.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;
  if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flipCard(); }
  if (e.key === 'ArrowRight') { e.preventDefault(); submitReview(5); }
  if (e.key === 'ArrowLeft')  { e.preventDefault(); submitReview(2); }
  if (e.key === 'Escape') closeSession();
}

function setupSwipe() {
  const area = document.getElementById('session-card-area');
  let startX = 0, startY = 0;
  const onStart = e => { startX = e.touches[0].clientX; startY = e.touches[0].clientY; };
  const onEnd = e => {
    const dx = e.changedTouches[0].clientX - startX;
    const dy = e.changedTouches[0].clientY - startY;
    if (Math.abs(dy) > Math.abs(dx) + 20) return;
    if (!state.session?.flipped) { flipCard(); return; }
    if (dx > 60) submitReview(5);
    else if (dx < -60) submitReview(2);
  };
  // remove old listeners by cloning
  const fresh = area.cloneNode(true);
  area.parentNode.replaceChild(fresh, area);
  fresh.addEventListener('touchstart', onStart, { passive: true });
  fresh.addEventListener('touchend', onEnd, { passive: true });
  fresh.addEventListener('click', flipCard);
}

// ── Library Tab ───────────────────────────────────────────────
async function renderLibrary() {
  await loadFolders();
  renderLibFolderPills();
  if (state.libWords.length === 0) {
    state.libPage = 0;
    state.libHasMore = true;
    await loadMoreWords(true);
  } else {
    renderWordList(true);
  }
}

function renderLibFolderPills() {
  const wrap = document.getElementById('lib-folder-pills');
  wrap.innerHTML = '';
  ['all', ...state.folders].forEach(f => {
    const btn = document.createElement('button');
    btn.className = 'pill' + (state.libFolder === f ? ' active' : '');
    const label = f === 'all' ? '全部' : f;
    btn.textContent = label;
    if (f !== 'all') btn.title = f; // tooltip for full name
    btn.onclick = () => {
      state.libFolder = f;
      wrap.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      state.libWords = []; state.libPage = 0; state.libHasMore = true;
      loadMoreWords(true);
    };
    wrap.appendChild(btn);
  });
}

const PAGE = 50;

async function loadMoreWords(reset = false) {
  if (state.libLoading || (!state.libHasMore && !reset)) return;
  state.libLoading = true;
  const list = document.getElementById('word-list');
  if (reset) list.innerHTML = '<div class="spinner-wrap"><div class="spinner"></div></div>';

  const offset = reset ? 0 : state.libWords.length;
  const folder = state.libFolder === 'all' ? '' : state.libFolder;
  const search = state.libSearch.trim();

  try {
    let words, hasMore;
    if (search) {
      // /api/search returns plain array, no pagination
      const data = await apiGet(`/api/search?keyword=${encodeURIComponent(search)}`);
      words = Array.isArray(data) ? data : (data.words || []);
      hasMore = false;
    } else {
      const url = `/api/words?limit=${PAGE}&offset=${offset}` + (folder ? `&folder=${encodeURIComponent(folder)}` : '');
      const data = await apiGet(url);
      words = data.words || [];
      hasMore = words.length === PAGE;
    }
    if (reset) state.libWords = words;
    else state.libWords = [...state.libWords, ...words];
    state.libHasMore = hasMore;
    renderWordList(reset);
  } catch (e) {
    toast(e.message, 'error');
    if (reset) list.innerHTML = '';
  } finally {
    state.libLoading = false;
  }
}

function renderWordList(reset) {
  const list = document.getElementById('word-list');
  if (reset) list.innerHTML = '';

  if (state.libWords.length === 0) {
    list.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📚</div><div class="empty-state-title">沒有單字</div><div class="empty-state-sub">按右下角 + 新增第一個單字</div></div>`;
    document.getElementById('load-more-wrap').classList.add('hidden');
    return;
  }

  const slice = reset ? state.libWords : state.libWords.slice(-PAGE);
  slice.forEach(w => {
    const item = document.createElement('div');
    item.className = 'word-item';
    item.dataset.id = w.id;
    item.innerHTML = `
      <div class="word-item-main">
        <div class="word-en">${esc(w.english)}</div>
        <div class="word-zh">${esc(w.chinese)}</div>
      </div>
      <div class="word-item-meta">
        <span class="folder-badge">${esc(w.folder)}</span>
        ${w.error_count > 0 ? `<span class="error-badge">✗ ${w.error_count}</span>` : ''}
      </div>
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#484F58" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>`;
    item.onclick = () => openWordDetail(w);
    list.appendChild(item);
  });

  document.getElementById('load-more-wrap').classList.toggle('hidden', !state.libHasMore);
}

// ── Word Detail Sheet ─────────────────────────────────────────
async function openWordDetail(word) {
  document.getElementById('detail-word').textContent = word.english;
  document.getElementById('detail-pos').textContent = word.part_of_speech || '';
  document.getElementById('detail-meaning').textContent = word.chinese;
  document.getElementById('detail-folder-val').textContent = word.folder;
  document.getElementById('detail-errors-val').textContent = word.error_count ?? 0;
  document.getElementById('detail-interval-val').textContent = word.interval != null ? `${word.interval} 天` : '未開始';
  document.getElementById('detail-efactor-val').textContent = word.efactor != null ? Number(word.efactor).toFixed(2) : '2.50';

  const nr = word.next_review;
  let nextStr = '未排程';
  if (nr) {
    const t = nr * 1000;
    nextStr = t <= Date.now() ? '現在待複習' : new Date(t).toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
  }
  document.getElementById('detail-next-val').textContent = nextStr;

  const morphWrap = document.getElementById('detail-morph-wrap');
  const morphBadges = document.getElementById('detail-morph-badges');
  // Show skeleton while loading morphology
  morphWrap.classList.remove('hidden');
  morphBadges.innerHTML = '<span class="morph-loading"><span class="spinner" style="width:14px;height:14px;border-width:2px;vertical-align:middle"></span> 分析中…</span>';

  document.getElementById('detail-delete-btn').onclick = () => deleteWord(word.id);
  openSheet('word-detail-sheet');

  try {
    const m = await apiGet(`/api/morphology/analyze/${word.id}`);
    morphBadges.innerHTML = '';
    if (m && (m.prefix || m.root || m.suffix)) {
      if (m.prefix) morphBadges.innerHTML += `<span class="morph-badge morph-prefix">${esc(m.prefix)}</span>`;
      if (m.root)   morphBadges.innerHTML += `<span class="morph-badge morph-root">${esc(m.root)}</span>`;
      if (m.suffix) morphBadges.innerHTML += `<span class="morph-badge morph-suffix">${esc(m.suffix)}</span>`;
    } else {
      morphWrap.classList.add('hidden');
    }
  } catch {
    morphWrap.classList.add('hidden');
  }
}

async function deleteWord(id) {
  const word = state.libWords.find(w => w.id === id);
  const ok = await showConfirm(`確定要刪除「${word?.english ?? id}」嗎？此操作無法復原。`, '確定刪除');
  if (!ok) return;
  try {
    await apiDelete(`/api/words/${id}`);
    closeSheet();
    toast('已刪除', 'success');
    const item = document.querySelector(`.word-item[data-id="${id}"]`);
    if (item) {
      item.style.transition = 'opacity .2s, transform .2s';
      item.style.opacity = '0';
      item.style.transform = 'translateX(20px)';
      setTimeout(() => {
        item.remove();
        state.libWords = state.libWords.filter(w => w.id !== id);
        if (state.libWords.length === 0) renderWordList(true);
      }, 200);
    } else {
      state.libWords = state.libWords.filter(w => w.id !== id);
      if (state.libWords.length === 0) renderWordList(true);
    }
  } catch (e) { toast(e.message, 'error'); }
}

// ── Add Word Sheet ────────────────────────────────────────────
function openAddSheet() {
  ['add-english','add-chinese','add-folder','add-pos'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  openSheet('add-sheet');
  setTimeout(() => document.getElementById('add-english')?.focus(), 150);
}

async function submitAddWord(e) {
  e.preventDefault();
  const english = document.getElementById('add-english').value.trim().toLowerCase();
  const chinese = document.getElementById('add-chinese').value.trim();
  const folder  = document.getElementById('add-folder').value.trim() || '預設';
  const pos     = document.getElementById('add-pos').value.trim();
  if (!english || !chinese) { toast('請填寫英文和中文', 'error'); return; }
  try {
    await apiPost('/api/words', { english, chinese, folder, part_of_speech: pos });
    toast(`已新增「${english}」`, 'success');
    closeSheet();
    state.folders = [];
    await loadFolders();
    renderLibFolderPills();
    state.libWords = []; state.libPage = 0; state.libHasMore = true;
    await loadMoreWords(true);
  } catch (e) { toast(e.message, 'error'); }
}

// ── Sheet helpers ─────────────────────────────────────────────
function openSheet(id) {
  closeSheet();
  document.getElementById(id).classList.add('active');
  document.getElementById('sheet-backdrop').classList.add('active');
}

function closeSheet() {
  document.querySelectorAll('.bottom-sheet').forEach(s => s.classList.remove('active'));
  document.getElementById('sheet-backdrop').classList.remove('active');
}

// ── Folders ───────────────────────────────────────────────────
async function loadFolders() {
  if (state.folders.length > 0) return;
  try {
    const data = await apiGet('/api/folders');
    state.folders = data.folders || (Array.isArray(data) ? data : []);
    const dl = document.getElementById('folder-datalist');
    if (dl) dl.innerHTML = state.folders.map(f => `<option value="${esc(f)}">`).join('');
  } catch { state.folders = []; }
}

// ── Search ────────────────────────────────────────────────────
let searchTimer;
function onSearchInput(e) {
  clearTimeout(searchTimer);
  state.libSearch = e.target.value;
  document.getElementById('search-clear').classList.toggle('hidden', !state.libSearch);
  searchTimer = setTimeout(() => {
    // Notify user if folder filter will be cleared
    if (state.libSearch && state.libFolder !== 'all') {
      toast(`搜尋範圍已切換為全部單字庫`, 'info', 2500);
      state.libFolder = 'all';
      document.querySelectorAll('#lib-folder-pills .pill').forEach((p, i) => p.classList.toggle('active', i === 0));
    }
    state.libWords = []; state.libPage = 0; state.libHasMore = true;
    loadMoreWords(true);
  }, 320);
}

function clearSearch() {
  state.libSearch = '';
  document.getElementById('lib-search').value = '';
  document.getElementById('search-clear').classList.add('hidden');
  state.libWords = []; state.libPage = 0; state.libHasMore = true;
  loadMoreWords(true);
}

// ── Infinite scroll ───────────────────────────────────────────
function setupInfiniteScroll() {
  document.getElementById('tab-library').addEventListener('scroll', () => {
    const el = document.getElementById('tab-library');
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 200) loadMoreWords(false);
  });
}

// ── Confirm modal (replaces browser confirm()) ────────────────
function showConfirm(body, okLabel = '確定') {
  return new Promise(resolve => {
    const modal = document.getElementById('confirm-modal');
    document.getElementById('confirm-body').textContent = body;
    document.getElementById('confirm-ok-btn').textContent = okLabel;
    modal.classList.add('active');
    const cleanup = ok => {
      modal.classList.remove('active');
      okBtn.replaceWith(okBtn.cloneNode(true));
      cancelBtn.replaceWith(cancelBtn.cloneNode(true));
      resolve(ok);
    };
    const okBtn     = document.getElementById('confirm-ok-btn');
    const cancelBtn = document.getElementById('confirm-cancel-btn');
    okBtn.onclick     = () => cleanup(true);
    cancelBtn.onclick = () => cleanup(false);
    modal.onclick = e => { if (e.target === modal) cleanup(false); };
  });
}

// ── Helpers ───────────────────────────────────────────────────
function esc(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Offline detection ─────────────────────────────────────────
window.addEventListener('offline', () => toast('網路已中斷，部分功能可能無法使用', 'error', 0));
window.addEventListener('online',  () => toast('網路已恢復連線', 'success', 2500));

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-btn').forEach(btn =>
    btn.addEventListener('click', () => switchTab(btn.dataset.tab)));

  document.getElementById('today-cta').addEventListener('click', () => {
    state.practiceMode = 'due'; state.practiceFolder = 'all';
    switchTab('practice');
  });
  document.getElementById('today-free-btn')?.addEventListener('click', () => switchTab('practice'));

  document.querySelectorAll('.mode-btn').forEach(btn =>
    btn.addEventListener('click', () => {
      state.practiceMode = btn.dataset.mode;
      document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === state.practiceMode));
      renderPracticeWordCount();
    }));

  document.getElementById('practice-start-btn').addEventListener('click', startSession);

  // Session
  document.getElementById('btn-unknown').addEventListener('click', () => submitReview(2));
  document.getElementById('btn-know').addEventListener('click', () => submitReview(5));
  document.getElementById('session-close-btn').addEventListener('click', closeSession);
  document.getElementById('summary-done-btn').addEventListener('click', closeSession);
  document.getElementById('summary-again-btn').addEventListener('click', () => {
    if (!state.session) return;
    state.session = { words: state.session.words, idx: 0, correct: 0, wrong: 0, flipped: false };
    document.getElementById('session-summary').style.display = 'none';
    document.getElementById('session-card-area').style.display = '';
    renderSessionCard();
  });

  // Library
  document.getElementById('lib-search').addEventListener('input', onSearchInput);
  document.getElementById('search-clear').addEventListener('click', clearSearch);
  document.getElementById('fab').addEventListener('click', openAddSheet);
  document.getElementById('nav-add-btn')?.addEventListener('click', openAddSheet);
  document.getElementById('add-word-form').addEventListener('submit', submitAddWord);
  document.getElementById('sheet-backdrop').addEventListener('click', closeSheet);
  document.querySelectorAll('.sheet-close').forEach(btn => btn.addEventListener('click', closeSheet));
  document.getElementById('load-more-btn')?.addEventListener('click', () => loadMoreWords(false));

  setupInfiniteScroll();

  // OAuth buttons: show loading text on click (page will redirect)
  document.querySelectorAll('.oauth-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      this.style.opacity = '.6';
      this.style.pointerEvents = 'none';
      const span = this.querySelector('span');
      if (span) span.textContent = '跳轉中…';
    });
  });

  // Onboarding & account
  initOnboardingUI();
  document.getElementById('user-chip')?.addEventListener('click', openAccountSheet);
  document.getElementById('mobile-account-btn')?.addEventListener('click', openAccountSheet);
  document.getElementById('logout-btn')?.addEventListener('click', doLogout);
  document.getElementById('change-goal-btn')?.addEventListener('click', () => { closeSheet(); showGoalStep(); document.getElementById('onboarding-overlay').classList.add('active'); });
  document.getElementById('guest-email-login-btn')?.addEventListener('click', () => { closeSheet(); document.getElementById('onboarding-overlay').classList.add('active'); showAuthStep(); });
  document.getElementById('save-pw-btn')?.addEventListener('click', saveNewPassword);

  // Start app after onboarding check — restore last tab if available
  initOnboarding().then(() => {
    const lastTab = sessionStorage.getItem('vm_tab');
    switchTab(['today','practice','library'].includes(lastTab) ? lastTab : 'today');
  });
});

// ── Onboarding ────────────────────────────────────────────────
const ob = {
  user: null,
  selectedGoal: null,
  mode: 'login',  // 'login' | 'register'
};

async function initOnboarding() {
  // Check URL params from OAuth redirect
  const params = new URLSearchParams(location.search);
  const oauthDone  = params.get('oauth') === '1';
  const linkedProv = params.get('linked'); // 'google' | 'github'
  const authError  = params.get('auth_error');
  if (oauthDone || linkedProv || authError) {
    history.replaceState(null, '', '/');
  }
  if (authError) {
    toast('登入失敗：' + decodeURIComponent(authError), 'error');
  }
  if (linkedProv) {
    const label = linkedProv === 'google' ? 'Google' : 'GitHub';
    toast(`已成功綁定 ${label} 帳號`, 'success');
  }

  try {
    const data = await apiGet('/auth/me');
    ob.user = data.success ? data.user : null;
  } catch { ob.user = null; }

  updateUserChip();

  if (ob.user) {
    if (ob.user.onboarding_done) return; // all good
    // Logged in but hasn't picked goal
    showGoalStep();
    document.getElementById('onboarding-overlay').classList.add('active');
    return;
  }

  // Guest
  if (localStorage.getItem('vm_guest_onboarded') === '1') return;
  // First visit — show overlay
  showAuthStep();
  document.getElementById('onboarding-overlay').classList.add('active');
}

function initOnboardingUI() {
  // Auth step: tabs (login / register)
  document.querySelectorAll('.ob-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      ob.mode = btn.dataset.form;
      document.querySelectorAll('.ob-tab-btn').forEach(b => b.classList.toggle('active', b.dataset.form === ob.mode));
      document.getElementById('ob-email-submit').textContent = ob.mode === 'login' ? '登入' : '註冊';
      document.getElementById('ob-email-error').style.display = 'none';
    });
  });

  // Auth step: email submit
  document.getElementById('ob-email-submit')?.addEventListener('click', doEmailAuth);
  document.getElementById('ob-username')?.addEventListener('keydown', e => { if (e.key === 'Enter') doEmailAuth(); });
  document.getElementById('ob-password')?.addEventListener('keydown', e => { if (e.key === 'Enter') doEmailAuth(); });

  // Skip
  document.getElementById('ob-skip-btn')?.addEventListener('click', () => {
    showGoalStep();
  });

  // Back (goal → auth)
  document.getElementById('ob-back-btn')?.addEventListener('click', () => {
    if (ob.user) return; // logged-in users can't go back
    showAuthStep();
  });

  // Confirm goal
  document.getElementById('ob-confirm-btn')?.addEventListener('click', completeOnboarding);
}

function showAuthStep() {
  document.getElementById('ob-step-auth').classList.add('active');
  document.getElementById('ob-step-goal').classList.remove('active');
  document.getElementById('ob-back-btn').style.display = 'none';
}

async function showGoalStep() {
  document.getElementById('ob-step-auth').classList.remove('active');
  document.getElementById('ob-step-goal').classList.add('active');
  // Hide back button if already logged in
  document.getElementById('ob-back-btn').style.display = ob.user ? 'none' : '';
  // Load folders for goal grid
  await loadFolders();
  renderGoalGrid();
}

function renderGoalGrid() {
  const grid = document.getElementById('goal-grid');
  if (!grid) return;
  grid.innerHTML = '';
  const folders = state.folders;
  if (!folders.length) {
    grid.innerHTML = '<div class="text-muted text-sm" style="grid-column:1/-1;text-align:center">沒有可用的資料夾</div>';
    return;
  }
  // Pre-select if user already has a goal or guest has one
  const currentGoal = ob.user?.learning_goal || localStorage.getItem('vm_guest_goal') || '';
  ob.selectedGoal = currentGoal || null;
  folders.forEach(f => {
    const card = document.createElement('button');
    card.className = 'goal-card' + (f === currentGoal ? ' selected' : '');
    card.innerHTML = `<span class="goal-card-name">${esc(f)}</span>`;
    card.addEventListener('click', () => {
      ob.selectedGoal = f;
      grid.querySelectorAll('.goal-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      document.getElementById('ob-confirm-btn').disabled = false;
    });
    grid.appendChild(card);
  });
  if (ob.selectedGoal) document.getElementById('ob-confirm-btn').disabled = false;
}

async function doEmailAuth() {
  const username = document.getElementById('ob-username').value.trim();
  const password = document.getElementById('ob-password').value;
  const errEl    = document.getElementById('ob-email-error');
  if (!username || !password) { showObError('請填寫暱稱和密碼'); return; }
  const btn = document.getElementById('ob-email-submit');
  btn.disabled = true;
  btn.classList.add('btn-loading');
  try {
    const url = ob.mode === 'login' ? '/auth/login' : '/auth/register';
    const data = await apiPost(url, { username, password });
    if (!data.success) { showObError(data.message || '失敗'); return; }
    ob.user = await apiGet('/auth/me').then(d => d.user);
    errEl.style.display = 'none';
    updateUserChip();
    showGoalStep();
  } catch (e) {
    showObError(e.message);
  } finally {
    btn.disabled = false;
    btn.classList.remove('btn-loading');
  }
}

function showObError(msg) {
  const el = document.getElementById('ob-email-error');
  el.textContent = msg;
  el.style.display = 'block';
}

async function completeOnboarding() {
  const goal = ob.selectedGoal;
  if (ob.user) {
    try {
      await apiPut('/api/user/settings', { learning_goal: goal, onboarding_done: 1 });
      ob.user.learning_goal = goal;
      ob.user.onboarding_done = 1;
    } catch (e) { toast(e.message, 'error'); return; }
  } else {
    // Guest
    localStorage.setItem('vm_guest_onboarded', '1');
    if (goal) localStorage.setItem('vm_guest_goal', goal);
  }
  // Apply goal to library/practice folder
  if (goal) {
    state.practiceFolder = goal;
    state.libFolder = goal;
  }
  document.getElementById('onboarding-overlay').classList.remove('active');
  updateUserChip();
  // Refresh folder pills (they may not have loaded yet)
  if (state.tab === 'practice') renderPracticeFolderPills();
  if (state.tab === 'library')  { renderLibFolderPills(); state.libWords = []; loadMoreWords(true); }
}

// ── Account sheet ─────────────────────────────────────────────
function openAccountSheet() {
  const loggedIn = document.getElementById('account-logged-in');
  const guestEl  = document.getElementById('account-guest-state');
  if (ob.user) {
    loggedIn.style.display = '';
    guestEl.style.display  = 'none';
    // Fill in details
    const name    = ob.user.display_name || ob.user.username || '用戶';
    const sub     = ob.user.username ? `@${ob.user.username}` : '';
    const goal    = ob.user.learning_goal || '未設定';
    const initials = (name[0] || '?').toUpperCase();
    document.getElementById('account-name').textContent  = name;
    document.getElementById('account-email').textContent = sub;
    document.getElementById('account-goal').textContent  = goal;
    document.getElementById('account-initial').textContent = initials;
    if (ob.user.avatar_url) {
      document.getElementById('account-avatar').innerHTML = `<img src="${esc(ob.user.avatar_url)}" alt="">`;
    } else {
      document.getElementById('account-avatar').innerHTML = `<span id="account-initial">${initials}</span>`;
    }
    // OAuth provider tags — show linked providers + link buttons for unlinked
    const tags = document.getElementById('provider-tags');
    tags.innerHTML = '';
    const linked = ob.user.oauth_providers || [];
    const providerLabel = { google: 'Google', github: 'GitHub' };
    linked.forEach(p => {
      const row = document.createElement('div');
      row.className = 'provider-linked';
      row.innerHTML = `<svg class="provider-linked-icon" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>${providerLabel[p] || p} 已連結`;
      tags.appendChild(row);
    });
    // Show link buttons for unlinked providers
    ['google', 'github'].forEach(p => {
      const btn = document.getElementById(`link-${p}-btn`);
      if (btn) btn.style.display = linked.includes(p) ? 'none' : 'flex';
    });
    // Change password section
    document.getElementById('change-pw-section').style.display = ob.user.has_password ? '' : 'none';
  } else {
    loggedIn.style.display  = 'none';
    guestEl.style.display   = '';
  }
  openSheet('account-sheet');
}

async function doLogout() {
  try {
    await apiPost('/auth/logout', {});
    ob.user = null;
    localStorage.removeItem('vm_guest_onboarded');
    localStorage.removeItem('vm_guest_goal');
    closeSheet();
    updateUserChip();
    toast('已登出', 'info');
    // Show onboarding again on next visit (or re-show now)
    setTimeout(() => { showAuthStep(); document.getElementById('onboarding-overlay').classList.add('active'); }, 400);
  } catch (e) { toast(e.message, 'error'); }
}

async function saveNewPassword() {
  const pw  = document.getElementById('new-password').value;
  const pw2 = document.getElementById('confirm-password').value;
  if (!pw) return toast('請輸入新密碼', 'error');
  if (pw !== pw2) return toast('兩次密碼不一致', 'error');
  try {
    await apiPut('/api/user/password', { password: pw });
    toast('密碼已更新', 'success');
    document.getElementById('new-password').value = '';
    document.getElementById('confirm-password').value = '';
  } catch (e) { toast(e.message, 'error'); }
}

function updateUserChip() {
  if (ob.user) {
    const name = ob.user.display_name || ob.user.email?.split('@')[0] || '用戶';
    const goal = ob.user.learning_goal || '';
    const initial = (name[0] || '?').toUpperCase();
    document.getElementById('sidebar-name').textContent = name;
    document.getElementById('sidebar-sub').textContent  = goal || '點此設定目標';
    document.getElementById('sidebar-initial').textContent = initial;
    document.getElementById('mobile-initial').textContent  = initial;
    if (ob.user.avatar_url) {
      const makeImg = (id, fallbackInitial) => {
        const img = new Image();
        img.src = ob.user.avatar_url;
        img.alt = '';
        img.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:50%';
        img.onerror = () => { img.replaceWith(document.createTextNode(fallbackInitial)); };
        document.getElementById(id).innerHTML = '';
        document.getElementById(id).appendChild(img);
      };
      makeImg('sidebar-avatar', initial);
      makeImg('mobile-avatar-circle', initial);
    }
  } else {
    const initial = '?';
    document.getElementById('sidebar-name').textContent = '訪客';
    const guestGoal = localStorage.getItem('vm_guest_goal') || '';
    document.getElementById('sidebar-sub').textContent  = guestGoal || '點此登入 / 設定';
    document.getElementById('sidebar-initial').textContent = initial;
    document.getElementById('mobile-initial').textContent  = initial;
  }
}
