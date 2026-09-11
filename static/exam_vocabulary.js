'use strict';
const $ = id => document.getElementById(id);
let items = [], saved = {}, limit = 20, queue = [], position = 0;
function node(tag, text, cls) { const el = document.createElement(tag); if(text !== undefined) el.textContent = text; if(cls) el.className = cls; return el; }
function status(message, error = false) { $('status').textContent = message; $('status').className = error ? 'error' : ''; }
async function api(path, body) {
  const response = await fetch('/api/exam-vocabulary' + path, {
    method: body ? 'POST' : 'GET', credentials: 'same-origin', signal: AbortSignal.timeout(15000),
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content},
    ...(body ? {body: JSON.stringify(body)} : {})
  });
  const data = await response.json();
  if(!response.ok) throw Error(data.error || '暫時無法載入，請稍後重試。');
  return data;
}
function sources(item) {
  const details = node('details'); details.append(node('summary', '查看原題片段（可能不完整）'));
  for(const source of item.sources) {
    const p = node('div', source.excerpt, 'source');
    p.append(node('small', `${source.exam} · ${source.label}`)); details.append(p);
  }
  return details;
}
function render() {
  const query = $('search').value.trim().toLowerCase();
  const filtered = items.filter(i => i.level <= Number($('level').value) && (!query || i.word.includes(query) || i.meaning.includes(query)));
  $('cards').replaceChildren();
  $('count').textContent = `${filtered.length} 個候選字 · 已收藏 ${Object.keys(saved).length} 個`;
  for(const item of filtered.slice(0, limit)) {
    const card = node('article', undefined, 'card');
    card.append(node('span', `第 ${item.level} 級 · 出現於 ${item.exam_count} 份試卷`, 'meta'), node('h2', item.word));
    const reveal = node('button', '想好了，查看意思');
    const details = node('div'); details.hidden = true;
    const meaning = node('p', item.meaning, 'meaning');
    const save = node('button', saved[item.word] ? '已加入複習' : '這個不熟，加入複習', 'primary');
    save.disabled = Boolean(saved[item.word]);
    save.onclick = async () => {
      save.disabled = true;
      try { const result = await api('/save', {word: item.word}); saved[item.word] = result.id; save.textContent = '已加入複習'; status(`已收藏 ${item.word}，可到「複習已收藏單字」開始。`); $('count').textContent = `${filtered.length} 個候選字 · 已收藏 ${Object.keys(saved).length} 個`; }
      catch(error) { save.disabled = false; status(error.message, true); }
    };
    const actions = node('div', undefined, 'actions'); actions.append(save);
    details.append(meaning, sources(item), actions); card.append(reveal, details);
    reveal.onclick = () => { reveal.hidden = true; details.hidden = false; save.focus(); };
    $('cards').append(card);
  }
  if(!filtered.length) $('cards').append(node('p', '目前沒有符合條件的字，試試其他關鍵字或程度。'));
  $('more').hidden = filtered.length <= limit;
}
function renderReview() {
  const card = $('review-card'); card.replaceChildren();
  if(position >= queue.length) {
    card.append(node('h2', queue.length ? '這組完成了' : '目前沒有到期單字'), node('p', '可以繼續找不熟的字，或檢查下一組到期單字。'));
    const again = node('button', '檢查下一組'); again.onclick = loadReview; card.append(again); return;
  }
  const word = queue[position];
  card.append(node('p', `${position + 1} / ${queue.length}`, 'meta'), node('h2', word.english));
  const reveal = node('button', '回想後揭曉', 'primary'); card.append(reveal);
  reveal.onclick = () => {
    reveal.remove(); card.append(node('p', word.chinese, 'meaning'));
    const item = items.find(i => i.word === word.english); if(item) card.append(sources(item));
    const actions = node('div', undefined, 'actions');
    for(const [quality, label] of [[1, '不記得'], [3, '吃力'], [5, '記得']]) {
      const button = node('button', label); actions.append(button);
      button.onclick = async () => {
        actions.querySelectorAll('button').forEach(b => b.disabled = true);
        try { const result = await api('/review', {id: word.id, quality}); position++; renderReview(); status(`已記錄，下次複習：${new Date(result.next_review * 1000).toLocaleDateString('zh-TW')}`); }
        catch(error) { actions.querySelectorAll('button').forEach(b => b.disabled = false); status(error.message, true); }
      };
    }
    card.append(actions);
  };
}
async function loadReview() {
  $('review-card').replaceChildren(node('p', '正在載入…'));
  try { queue = (await api('/due')).words; position = 0; renderReview(); }
  catch(error) { $('review-card').replaceChildren(node('p', error.message)); status(error.message, true); }
}
$('browse-tab').onclick = () => { $('browse').hidden = false; $('review').hidden = true; $('browse-tab').setAttribute('aria-pressed', 'true'); $('review-tab').setAttribute('aria-pressed', 'false'); };
$('review-tab').onclick = () => { $('browse').hidden = true; $('review').hidden = false; $('browse-tab').setAttribute('aria-pressed', 'false'); $('review-tab').setAttribute('aria-pressed', 'true'); loadReview(); };
$('search').oninput = $('level').onchange = () => { limit = 20; render(); };
$('more').onclick = () => { limit += 20; render(); };
(async () => {
  try { const data = await api(''); items = data.items; saved = data.saved; $('audit').textContent = `共分析 ${data.audit.documents} 份題目文件；${data.audit.options_only_candidate || 0} 份疑似只有選項。`; status('每天先選少量真正不熟的字；意思與出處在揭曉後顯示。'); render(); }
  catch(error) { status(error.message, true); $('cards').append(node('p', '登入後請重新整理此頁。')); }
})();
