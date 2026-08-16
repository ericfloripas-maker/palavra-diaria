const MONTHS = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];

function formatShortDate(isoDate) {
  const [, m, d] = isoDate.split('-').map(Number);
  return `${d.toString().padStart(2, '0')} ${MONTHS[m - 1].slice(0, 3)}`;
}

function collectTagCounts(entries) {
  const counts = {};
  entries.forEach(entry => {
    (entry.tags || []).forEach(tag => {
      counts[tag] = (counts[tag] || 0) + 1;
    });
  });
  return counts;
}

function renderCloud(counts, activeTag) {
  const cloud = document.getElementById('topics-cloud');
  cloud.innerHTML = '';

  const tags = Object.keys(counts).sort((a, b) => a.localeCompare(b, 'pt-BR'));

  if (tags.length === 0) {
    cloud.innerHTML = '<p class="topics-empty">Nenhum tema cadastrado ainda.</p>';
    return;
  }

  tags.forEach(tag => {
    const a = document.createElement('a');
    a.className = 'topic-pill' + (tag === activeTag ? ' active' : '');
    a.href = `temas.html?tema=${encodeURIComponent(tag)}`;
    a.textContent = `#${tag}`;
    const count = document.createElement('span');
    count.className = 'topic-pill-count';
    count.textContent = counts[tag];
    a.appendChild(count);
    cloud.appendChild(a);
  });
}

function renderResults(entries, activeTag) {
  const results = document.getElementById('topics-results');
  results.innerHTML = '';

  if (!activeTag) {
    return;
  }

  const matches = entries
    .filter(e => (e.tags || []).includes(activeTag))
    .sort((a, b) => b.date.localeCompare(a.date));

  const heading = document.createElement('h2');
  heading.className = 'topics-results-heading';
  heading.textContent = `Devocionais sobre #${activeTag}`;
  results.appendChild(heading);

  if (matches.length === 0) {
    const p = document.createElement('p');
    p.className = 'topics-empty';
    p.textContent = 'Nenhum devocional encontrado para este tema.';
    results.appendChild(p);
    return;
  }

  const list = document.createElement('div');
  list.className = 'topics-list';
  matches.forEach(entry => {
    const card = document.createElement('a');
    card.className = 'topics-list-item';
    card.href = `index.html?data=${entry.date}`;

    const date = document.createElement('span');
    date.className = 'topics-list-date';
    date.textContent = formatShortDate(entry.date);

    const title = document.createElement('span');
    title.className = 'topics-list-title';
    title.textContent = entry.title;

    const ref = document.createElement('span');
    ref.className = 'topics-list-ref';
    ref.textContent = entry.verseRef;

    card.appendChild(date);
    card.appendChild(title);
    card.appendChild(ref);
    list.appendChild(card);
  });
  results.appendChild(list);
}

fetch('devocionais.json')
  .then(res => res.json())
  .then(entries => {
    const params = new URLSearchParams(window.location.search);
    const activeTag = params.get('tema');

    if (activeTag) {
      document.getElementById('page-title').textContent = `#${activeTag} — Palavra Diária`;
      document.getElementById('topics-subtitle').textContent = `Mostrando devocionais sobre #${activeTag}. Escolha outro tema abaixo se quiser.`;
    }

    const counts = collectTagCounts(entries);
    renderCloud(counts, activeTag);
    renderResults(entries, activeTag);
  })
  .catch(err => {
    console.error('Não foi possível carregar devocionais.json', err);
    document.getElementById('topics-cloud').innerHTML = '<p class="topics-empty">Não foi possível carregar os temas.</p>';
  });
