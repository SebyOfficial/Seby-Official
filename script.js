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
searchInput.addEventListener('input', filterGuides);

document.getElementById('menuToggle').addEventListener('click', () => {
  document.getElementById('nav').classList.toggle('open');
});

document.getElementById('copySuggestion').addEventListener('click', async () => {
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

document.getElementById('year').textContent = new Date().getFullYear();

// The live reader talks only to the small local server in server.py.
const liveSearch = document.getElementById('liveSearch');
const liveStatus = document.getElementById('liveStatus');
const liveUpdated = document.getElementById('liveUpdated');
const refreshLive = document.getElementById('refreshLive');
let latestLiveData = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

function liveCard(title, description, url, searchText, extra = '') {
  return `<article class="live-card" data-live-search="${escapeHtml(`${title} ${description} ${searchText}`.toLocaleLowerCase('ro'))}">
    <h4>${escapeHtml(title)}</h4><p>${escapeHtml(description)}</p>${extra}
    ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Deschide sursa oficială ↗</a>` : ''}
  </article>`;
}

function renderLive(data) {
  latestLiveData = data;
  const codes = data.codes || [];
  const events = data.events || [];
  const schedule = data.schedule || { title: '', url: '', items: [] };
  document.getElementById('codesList').innerHTML = codes.length
    ? codes.map((item) => liveCard(item.code, `${item.validity || 'Verifică pagina oficială pentru termenul de valabilitate.'}${item.expired ? ' · Termenul pare expirat.' : ''}`, item.url, item.title,
      `<button class="copy-live-code" type="button" data-code="${escapeHtml(item.code)}">Copiază codul</button>`)).join('')
    : '<p class="live-placeholder">Nu am găsit coduri în cele mai recente știri oficiale citite.</p>';

  const scheduleCards = (schedule.items || []).map((line) => liveCard(line, schedule.title || 'Program publicat pe forumul oficial.', schedule.url, 'program dată oră eveniment'));
  const eventCards = events.map((item) => liveCard(item.title, item.duration || item.summary || 'Deschide anunțul pentru detalii și oră.', item.url, 'eveniment data oră calendar'));
  document.getElementById('eventsList').innerHTML = [...scheduleCards, ...eventCards].join('')
    || '<p class="live-placeholder">Programul nu a putut fi extras automat. Deschide anunțurile oficiale de mai jos.</p>';
  document.getElementById('newsList').innerHTML = (data.news || []).map((item) => liveCard(item.title, item.date ? `Publicat: ${item.date}. ${item.summary || ''}` : (item.summary || 'Deschide știrea pentru detalii.'), item.url, (item.codes || []).map((code) => code.code).join(' '))).join('')
    || '<p class="live-placeholder">Nu s-au putut încărca știrile. Încearcă din nou puțin mai târziu.</p>';

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
document.getElementById('codesList').addEventListener('click', async (event) => {
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
  liveStatus.textContent = 'Pentru informații live, pornește Pornește-site.bat din folderul Seby-Official. Se va deschide adresa locală potrivită.';
} else {
  loadLiveInfo();
  window.setInterval(() => loadLiveInfo(), 15 * 60 * 1000);
}
