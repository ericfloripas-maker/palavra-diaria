const MONTHS_FULL = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];

function formatFullDate(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number);
  return `${d} de ${MONTHS_FULL[m - 1]} de ${y}`;
}

function formatShortDay(isoDate) {
  const [, , d] = isoDate.split('-').map(Number);
  return d.toString().padStart(2, '0');
}

function groupByYearMonth(entries) {
  const byYear = {};
  entries.forEach(entry => {
    const [y, m] = entry.date.split('-');
    byYear[y] = byYear[y] || {};
    byYear[y][m] = byYear[y][m] || [];
    byYear[y][m].push(entry);
  });
  return byYear;
}

function renderYears(byYear, activeYear) {
  const el = document.getElementById('archive-years');
  el.innerHTML = '';
  const years = Object.keys(byYear).sort((a, b) => b.localeCompare(a));

  years.forEach(year => {
    const count = Object.values(byYear[year]).reduce((sum, arr) => sum + arr.length, 0);
    const a = document.createElement('a');
    a.className = 'topic-pill' + (year === activeYear ? ' active' : '');
    a.href = `arquivo.html?ano=${year}`;
    a.textContent = year;
    const span = document.createElement('span');
    span.className = 'topic-pill-count';
    span.textContent = count;
    a.appendChild(span);
    el.appendChild(a);
  });
}

function renderMonths(byYear, activeYear, activeMonth) {
  const el = document.getElementById('archive-months');
  el.innerHTML = '';
  if (!activeYear || !byYear[activeYear]) return;

  const months = Object.keys(byYear[activeYear]).sort((a, b) => a.localeCompare(b));

  months.forEach(month => {
    const count = byYear[activeYear][month].length;
    const a = document.createElement('a');
    a.className = 'topic-pill month-pill' + (month === activeMonth ? ' active' : '');
    a.href = `arquivo.html?ano=${activeYear}&mes=${month}`;
    a.textContent = MONTHS_FULL[parseInt(month, 10) - 1];
    const span = document.createElement('span');
    span.className = 'topic-pill-count';
    span.textContent = count;
    a.appendChild(span);
    el.appendChild(a);
  });
}

function renderResults(byYear, activeYear, activeMonth) {
  const results = document.getElementById('archive-results');
  results.innerHTML = '';
  if (!activeYear || !byYear[activeYear]) return;

  let entries = [];
  if (activeMonth) {
    entries = byYear[activeYear][activeMonth] || [];
  } else {
    Object.values(byYear[activeYear]).forEach(arr => entries.push(...arr));
  }
  entries = [...entries].sort((a, b) => b.date.localeCompare(a.date));

  const heading = document.createElement('h2');
  heading.className = 'topics-results-heading';
  heading.textContent = activeMonth
    ? `${MONTHS_FULL[parseInt(activeMonth, 10) - 1].charAt(0).toUpperCase() + MONTHS_FULL[parseInt(activeMonth, 10) - 1].slice(1)} de ${activeYear}`
    : `Todos os devocionais de ${activeYear}`;
  results.appendChild(heading);

  if (entries.length === 0) {
    const p = document.createElement('p');
    p.className = 'topics-empty';
    p.textContent = 'Nenhum devocional encontrado neste período.';
    results.appendChild(p);
    return;
  }

  const list = document.createElement('div');
  list.className = 'topics-list';
  entries.forEach(entry => {
    const card = document.createElement('a');
    card.className = 'topics-list-item';
    card.href = `index.html?data=${entry.date}`;

    const day = document.createElement('span');
    day.className = 'topics-list-date';
    day.textContent = formatFullDate(entry.date).split(' de ')[0].padStart(2, '0') + ' ' + MONTHS_FULL[parseInt(entry.date.split('-')[1], 10) - 1].slice(0, 3);

    const title = document.createElement('span');
    title.className = 'topics-list-title';
    title.textContent = entry.title;

    const ref = document.createElement('span');
    ref.className = 'topics-list-ref';
    ref.textContent = entry.verseRef;

    if (entry.audio) {
      const audioIcon = document.createElement('span');
      audioIcon.className = 'topics-list-audio';
      audioIcon.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7Z"/></svg>';
      audioIcon.title = 'Áudio disponível';
      card.appendChild(day);
      card.appendChild(title);
      card.appendChild(ref);
      card.appendChild(audioIcon);
    } else {
      card.appendChild(day);
      card.appendChild(title);
      card.appendChild(ref);
    }
    list.appendChild(card);
  });
  results.appendChild(list);
}

fetch('devocionais.json')
  .then(res => res.json())
  .then(entries => {
    const byYear = groupByYearMonth(entries);
    const years = Object.keys(byYear).sort((a, b) => b.localeCompare(a));

    const params = new URLSearchParams(window.location.search);
    const activeYear = params.get('ano') || years[0] || null;
    const activeMonth = params.get('mes');

    if (activeYear) {
      document.getElementById('archive-subtitle').textContent = activeMonth
        ? `Mostrando ${MONTHS_FULL[parseInt(activeMonth, 10) - 1]} de ${activeYear}.`
        : `Mostrando todos os devocionais de ${activeYear}.`;
    }

    renderYears(byYear, activeYear);
    renderMonths(byYear, activeYear, activeMonth);
    renderResults(byYear, activeYear, activeMonth);
  })
  .catch(err => {
    console.error('Não foi possível carregar devocionais.json', err);
    document.getElementById('archive-years').innerHTML = '<p class="topics-empty">Não foi possível carregar o arquivo.</p>';
  });
