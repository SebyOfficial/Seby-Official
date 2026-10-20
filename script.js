const searchInput = document.getElementById('searchInput');
const guideList = document.getElementById('guideList');
const resultCount = document.getElementById('resultCount');
const emptyState = document.getElementById('emptyState');

function filterGuides() {
  const query = searchInput.value.trim().toLocaleLowerCase('ro');
  const guides = [...guideList.querySelectorAll('.guide')];
  let shown = 0;
  guides.forEach((guide) => {
    const searchable = (guide.innerText + ' ' + guide.dataset.search).toLocaleLowerCase('ro');
    const match = searchable.includes(query);
    guide.hidden = !match;
    if (match) shown++;
  });
  resultCount.textContent = `${shown} ${shown === 1 ? 'rezultat' : 'rezultate'}`;
  emptyState.hidden = shown !== 0;
}
if (searchInput && guideList && resultCount && emptyState) {
  searchInput.addEventListener('input', filterGuides);
}

document.querySelectorAll('article[data-href]').forEach((card) => {
  card.tabIndex = 0;
  card.setAttribute('role', 'link');
  card.addEventListener('click', (event) => {
    if (event.target.closest('a, button, input, textarea, select, summary')) return;
    location.href = card.dataset.href;
  });
  card.addEventListener('keydown', (event) => {
    if ((event.key === 'Enter' || event.key === ' ') && !event.target.closest('a, button, input, textarea, select, summary')) {
      event.preventDefault();
      location.href = card.dataset.href;
    }
  });
});
const menuToggle = document.getElementById('menuToggle');
const nav = document.getElementById('nav');
if (nav) nav.innerHTML = `
  <a href="index.html">Acasă</a>
  <a href="personaje.html">Personaje</a>
  <a href="echipamente.html">Echipamente</a>
  <a href="harti.html">Hărți &amp; ghiduri</a>
  <a href="evenimente.html">Evenimente</a>
  <details class="topic-menu"><summary>Toate ghidurile</summary><div class="topic-menu-list">
    <a href="ranger.html">Ranger</a><a href="dragonknight.html">Dragonknight</a>
    <a href="spellweaver.html">Spellweaver</a><a href="steam-mechanicus.html">Steam Mechanicus</a>
    <a href="arme.html">Arme</a><a href="armuri.html">Armuri</a><a href="mantale.html">Mantale</a>
    <a href="bijuterii.html">Bijuterii</a><a href="pietre.html">Pietre prețioase</a><a href="rune.html">Rune</a>
    <a href="misiuni.html">Misiuni</a>
    <a href="bossi.html">Bossi</a><a href="grup-pvp.html">Grup &amp; PvP</a><a href="clasament.html">Clasament</a>
    <a href="coduri.html">Coduri promoționale</a><a href="noutati.html">Noutăți live</a>
  </div></details>`;
if (menuToggle && nav) menuToggle.addEventListener('click', () => nav.classList.toggle('open'));

document.addEventListener('click', (event) => {
  const card = event.target.closest('.live-card[data-href]');
  if (!card || event.target.closest('a, button, input, textarea, select')) return;
  location.href = card.dataset.href;
});
const copySuggestion = document.getElementById('copySuggestion');
if (copySuggestion) copySuggestion.addEventListener('click', async () => {
  const value = document.getElementById('suggestion').value.trim();
  const status = document.getElementById('copyStatus');
  if (!value) {
    status.textContent = 'Scrie mai întâi o sugestie.';
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
    status.textContent = 'Sugestia a fost copiată.';
  } catch {
    status.textContent = 'Selectează și copiază textul manual.';
  }
});

const runeSearch = document.getElementById('runeSearch');
if (runeSearch) runeSearch.addEventListener('input', () => {
  const query = runeSearch.value.trim().toLocaleLowerCase('ro');
  document.querySelectorAll('.rune-card').forEach((card) => {
    card.hidden = !card.dataset.rune.toLocaleLowerCase('ro').includes(query)
      && !card.innerText.toLocaleLowerCase('ro').includes(query);
  });
});

const gemSearch = document.getElementById('gemSearch');
if (gemSearch) gemSearch.addEventListener('input', () => {
  const query = gemSearch.value.trim().toLocaleLowerCase('ro');
  document.querySelectorAll('.gem-card').forEach((card) => {
    card.hidden = !card.dataset.gem.toLocaleLowerCase('ro').includes(query)
      && !card.innerText.toLocaleLowerCase('ro').includes(query);
  });
});
const year = document.getElementById('year');
if (year) year.textContent = new Date().getFullYear();

// The live reader talks only to the small local server in server.py.
const liveSearch = document.getElementById('liveSearch');
const liveStatus = document.getElementById('liveStatus');
const liveUpdated = document.getElementById('liveUpdated');
const refreshLive = document.getElementById('refreshLive');
if (liveSearch && liveStatus && liveUpdated && refreshLive && (document.getElementById('codesList') || document.getElementById('eventsList') || document.getElementById('newsList'))) {
let latestLiveData = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

function liveCard(title, description, url, searchText, extra = '', destination = 'noutati.html') {
  return `<article class="live-card" data-href="${destination}" data-live-search="${escapeHtml(`${title} ${description} ${searchText}`.toLocaleLowerCase('ro'))}">
    <h4><a href="${destination}">${escapeHtml(title)}</a></h4><p>${escapeHtml(description)}</p>${extra}
    ${url ? '<small class="source-note">Detalii afișate pe Seby Official · sursă verificată de cititorul de noutăți</small>' : ''}
  </article>`;
}

function renderLive(data) {
  latestLiveData = data;
  const codes = data.codes || [];
  const events = data.events || [];
  const schedule = data.schedule || { title: '', url: '', items: [] };
  const codesList = document.getElementById('codesList');
  if (codesList) codesList.innerHTML = codes.length
    ? codes.map((item) => liveCard(item.code, `${item.validity || 'Verifică termenul de valabilitate din descrierea codului.'}${item.expired ? ' · Termenul pare expirat.' : ''}`, item.url, item.title,
      `<button class="copy-live-code" type="button" data-code="${escapeHtml(item.code)}">Copiază codul</button>`, 'coduri.html')).join('')
    : '<p class="live-placeholder">Nu am găsit coduri în cele mai recente știri citite. <a href="coduri.html">Deschide pagina cu coduri →</a></p>';

  const scheduleCards = (schedule.items || []).map((item) => {
    const event = typeof item === 'string' ? { title: item, duration: schedule.title || 'Program de eveniment.' } : item;
    return liveCard(event.title, event.duration || event.summary || 'Program de eveniment.', event.url || schedule.url, 'program dată oră eveniment', '', 'evenimente.html');
  });
  const eventCards = events.map((item) => liveCard(item.title, item.duration || item.summary || 'Detalii și perioadă pentru eveniment.', item.url, 'eveniment data oră calendar', '', 'evenimente.html'));
  const eventsList = document.getElementById('eventsList');
  if (eventsList) eventsList.innerHTML = [...scheduleCards, ...eventCards].join('')
    || '<p class="live-placeholder">Programul nu a putut fi extras automat. <a href="evenimente.html">Deschide pagina evenimentelor →</a></p>';
  const newsList = document.getElementById('newsList');
  if (newsList) newsList.innerHTML = (data.news || []).map((item) => liveCard(item.title, item.date ? `Publicat: ${item.date}. ${item.summary || ''}` : (item.summary || 'Detalii despre această noutate.'), item.url, (item.codes || []).map((code) => code.code).join(' '))).join('')
    || '<p class="live-placeholder">Nu s-au putut încărca știrile. <a href="noutati.html">Deschide pagina de noutăți →</a></p>';

  liveUpdated.textContent = data.checkedAt ? `Ultima verificare: ${new Date(data.checkedAt).toLocaleString('ro-RO')}` : '';
  liveStatus.textContent = data.errors?.length
    ? 'Unele surse nu au răspuns. Poți încerca din nou sau deschide sursele oficiale.'
    : `Am verificat ${codes.length} coduri și ${events.length} știri despre evenimente.`;
  filterLiveCards();
}

function filterLiveCards() {
  const query = liveSearch.value.trim().toLocaleLowerCase('ro');
  document.querySelectorAll('.live-card').forEach((card) => {
    card.hidden = !card.dataset.liveSearch.includes(query);
  });
}

async function loadLiveInfo(force = false) {
  refreshLive.disabled = true;
  liveStatus.textContent = 'Caut informațiile oficiale…';
  try {
    const onLocalServer = location.hostname === '127.0.0.1' || location.hostname === 'localhost';
    const endpoint = onLocalServer
      ? `/api/updates${force ? '?refresh=1' : ''}`
      : `updates.json?v=${Date.now()}`;
    const response = await fetch(endpoint, { cache: 'no-store' });
    if (!response.ok) throw new Error('Server unavailable');
    renderLive(await response.json());
  } catch {
    liveStatus.textContent = 'Nu m-am putut conecta. Pornește site-ul cu fișierul Pornește-site.bat și deschide http://127.0.0.1:8765.';
  } finally {
    refreshLive.disabled = false;
  }
}

refreshLive.addEventListener('click', () => loadLiveInfo(true));
liveSearch.addEventListener('input', filterLiveCards);
const codesList = document.getElementById('codesList');
if (codesList) codesList.addEventListener('click', async (event) => {
  const button = event.target.closest('.copy-live-code');
  if (!button) return;
  try {
    await navigator.clipboard.writeText(button.dataset.code);
    button.textContent = 'Copiat!';
  } catch {
    button.textContent = button.dataset.code;
  }
});

if (location.protocol === 'file:') {
  if (window.DSO_UPDATES_SEED) renderLive(window.DSO_UPDATES_SEED);
  liveStatus.textContent = 'Afișez informațiile verificate la 20.10.2026. Pentru căutare automată și actualizare, pornește Pornește-site.bat.';
} else {
  loadLiveInfo();
  window.setInterval(() => loadLiveInfo(), 5 * 60 * 1000);
}
}



