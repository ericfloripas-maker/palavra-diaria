/* ---------- Carregar e escolher o devocional ---------- */

const MONTHS = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];

function formatDisplayDate(isoDate) {
  const [y, m, d] = isoDate.split('-').map(Number);
  return `${d} de ${MONTHS[m - 1]}`;
}

function formatShortDate(isoDate) {
  const [, m, d] = isoDate.split('-').map(Number);
  return `${d.toString().padStart(2, '0')} ${MONTHS[m - 1].slice(0, 3)}`;
}

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
}

function pickEntry(entries, requestedDate) {
  const sorted = [...entries].sort((a, b) => b.date.localeCompare(a.date));
  if (requestedDate) {
    const exact = sorted.find(e => e.date === requestedDate);
    if (exact) return exact;
  }
  const today = todayISO();
  const exactToday = sorted.find(e => e.date === today);
  if (exactToday) return exactToday;
  // sem devocional exatamente hoje: usa o mais recente que já passou
  const pastOrToday = sorted.find(e => e.date <= today);
  return pastOrToday || sorted[0];
}

function renderEntry(entry, allEntries) {
  document.getElementById('page-title').textContent = `Palavra Diária — ${entry.title}`;
  document.getElementById('hero-date').textContent = formatDisplayDate(entry.date);
  document.getElementById('hero-title').textContent = entry.title;

  const verseExcerpt = entry.verseText.length > 140 ? entry.verseText.slice(0, 137) + '…' : entry.verseText;
  document.getElementById('hero-verse').textContent = `"${verseExcerpt}" – ${entry.verseRef}`;

  document.getElementById('reading-heading').textContent = `A Leitura de Hoje: ${entry.verseRef}`;
  document.getElementById('scripture-text').textContent = entry.verseText;
  document.getElementById('scripture-ref').textContent = entry.verseRef;

  const reflectionEl = document.getElementById('reflection');
  reflectionEl.innerHTML = '';
  entry.reflection.forEach(paragraph => {
    const p = document.createElement('p');
    p.textContent = paragraph;
    reflectionEl.appendChild(p);
  });

  const prayerBlock = document.getElementById('prayer-block');
  if (entry.prayer) {
    document.getElementById('prayer-text').textContent = entry.prayer;
    prayerBlock.style.display = '';
  } else {
    prayerBlock.style.display = 'none';
  }

  document.getElementById('author-name').textContent = entry.author || '';

  const pageLink = `${window.location.origin}${window.location.pathname}?data=${entry.date}`;
  const shareText = `${entry.title} — Palavra Diária\n${pageLink}`;
  document.getElementById('share-wa').href = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
  document.getElementById('share-fb').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageLink)}`;
  document.getElementById('share-ig').dataset.shareText = shareText;
  document.getElementById('share-mail').href = `mailto:?subject=${encodeURIComponent('Palavra Diária: ' + entry.title)}&body=${encodeURIComponent(shareText)}`;

  const tagRow = document.getElementById('tag-row');
  tagRow.innerHTML = '';
  (entry.tags || []).forEach(tag => {
    const a = document.createElement('a');
    a.className = 'tag';
    a.href = `temas.html?tema=${encodeURIComponent(tag)}`;
    a.textContent = `#${tag}`;
    tagRow.appendChild(a);
  });

  const relatedEl = document.getElementById('related-themes');
  relatedEl.innerHTML = '';
  (entry.relatedThemes || entry.tags || []).forEach(tag => {
    const a = document.createElement('a');
    a.className = 'tag';
    a.href = `temas.html?tema=${encodeURIComponent(tag)}`;
    a.textContent = `#${tag}`;
    relatedEl.appendChild(a);
  });

  // Áudio
  const audio = document.getElementById('devotional-audio');
  const source = document.getElementById('audio-source');
  source.src = entry.audio;
  document.getElementById('download-btn').href = entry.audio;
  audio.load();
  document.getElementById('time-current').textContent = '0:00';
  document.getElementById('time-total').textContent = '0:00';
  document.getElementById('progress-fill').style.width = '0%';

  // Devocionais recentes (todos exceto o exibido agora, mais recentes primeiro)
  const recentList = document.getElementById('recent-list');
  recentList.innerHTML = '';
  const others = allEntries
    .filter(e => e.slug !== entry.slug)
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 5);
  others.forEach(e => {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = `?data=${e.date}`;
    a.innerHTML = `<span class="rdate">${formatShortDate(e.date)}:</span> ${e.title}`;
    li.appendChild(a);
    recentList.appendChild(li);
  });
  if (others.length === 0) {
    recentList.innerHTML = '<li>Este é o primeiro devocional publicado.</li>';
  }
}

fetch('devocionais.json')
  .then(res => res.json())
  .then(entries => {
    const params = new URLSearchParams(window.location.search);
    const requestedDate = params.get('data');
    const entry = pickEntry(entries, requestedDate);
    renderEntry(entry, entries);
  })
  .catch(err => {
    console.error('Não foi possível carregar devocionais.json', err);
    document.getElementById('hero-title').textContent = 'Não foi possível carregar o devocional.';
  });

/* ---------- Player de áudio ---------- */

const audio = document.getElementById('devotional-audio');
const playBtn = document.getElementById('play-btn');
const playIcon = document.getElementById('play-icon');
const timeCurrent = document.getElementById('time-current');
const timeTotal = document.getElementById('time-total');
const progressTrack = document.getElementById('progress-track');
const progressFill = document.getElementById('progress-fill');
const volumeBtn = document.getElementById('volume-btn');
const volumeIcon = document.getElementById('volume-icon');
const speedBtn = document.getElementById('speed-btn');

const ICON_PLAY = '<path d="M8 5v14l11-7Z"/>';
const ICON_PAUSE = '<path d="M7 5h4v14H7zM13 5h4v14h-4z"/>';
const ICON_VOLUME_ON = '<path d="M4 9v6h4l5 5V4L8 9H4Z"/><path d="M17 9a3 3 0 0 1 0 6"/>';
const ICON_VOLUME_OFF = '<path d="M4 9v6h4l5 5V4L8 9H4Z"/><path d="m16 9 5 6m0-6-5 6"/>';

function formatTime(seconds) {
  if (!isFinite(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

playBtn.addEventListener('click', () => {
  if (audio.paused) {
    audio.play();
  } else {
    audio.pause();
  }
});

audio.addEventListener('play', () => {
  playIcon.innerHTML = ICON_PAUSE;
  playBtn.setAttribute('aria-label', 'Pausar');
});

audio.addEventListener('pause', () => {
  playIcon.innerHTML = ICON_PLAY;
  playBtn.setAttribute('aria-label', 'Reproduzir');
});

audio.addEventListener('ended', () => {
  playIcon.innerHTML = ICON_PLAY;
  playBtn.setAttribute('aria-label', 'Reproduzir');
});

audio.addEventListener('loadedmetadata', () => {
  timeTotal.textContent = formatTime(audio.duration);
});

audio.addEventListener('timeupdate', () => {
  timeCurrent.textContent = formatTime(audio.currentTime);
  if (audio.duration) {
    progressFill.style.width = (audio.currentTime / audio.duration) * 100 + '%';
  }
});

progressTrack.classList.add('seekable');
progressTrack.addEventListener('click', (e) => {
  if (!audio.duration) return;
  const rect = progressTrack.getBoundingClientRect();
  const ratio = (e.clientX - rect.left) / rect.width;
  audio.currentTime = ratio * audio.duration;
});

volumeBtn.addEventListener('click', () => {
  audio.muted = !audio.muted;
  volumeIcon.innerHTML = audio.muted ? ICON_VOLUME_OFF : ICON_VOLUME_ON;
  volumeBtn.setAttribute('aria-label', audio.muted ? 'Ativar som' : 'Mudo');
});

const speeds = [1, 1.25, 1.5, 0.75];
const speedLabels = ['1,0×', '1,25×', '1,5×', '0,75×'];
let speedIdx = 0;
speedBtn.addEventListener('click', () => {
  speedIdx = (speedIdx + 1) % speeds.length;
  audio.playbackRate = speeds[speedIdx];
  speedBtn.textContent = speedLabels[speedIdx];
});

/* ---------- Compartilhar no Instagram (copiar link) ---------- */

document.getElementById('share-ig').addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  const text = btn.dataset.shareText || window.location.href;
  try {
    await navigator.clipboard.writeText(text);
  } catch (err) {
    // navegador sem suporte a clipboard: seleciona o texto manualmente como alternativa
    console.warn('Não foi possível copiar automaticamente', err);
  }
  btn.classList.add('copied');
  setTimeout(() => btn.classList.remove('copied'), 2200);
});
