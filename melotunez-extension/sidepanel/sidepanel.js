/**
 * Side panel: Music tab → Express GET /api/tracks?q=
 * Build tab → OpenAI-compatible chat (OpenRouter / Ollama / …) — never Base44 AI.
 */

const DEFAULTS = {
  musicApiBase: 'http://localhost:3001',
  aiProvider: 'openrouter',
  aiBaseUrl: 'https://openrouter.ai/api/v1',
  aiModel: 'openai/gpt-4o-mini',
  aiApiKey: '',
};

async function loadSettings() {
  const stored = await chrome.storage.local.get(Object.keys(DEFAULTS));
  return { ...DEFAULTS, ...stored };
}

function setStatus(el, text, isError = false) {
  el.textContent = text;
  el.classList.toggle('is-error', isError);
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach((btn) => {
    const active = btn.dataset.tab === name;
    btn.classList.toggle('is-active', active);
    btn.setAttribute('aria-selected', String(active));
  });
  document.querySelectorAll('.panel').forEach((panel) => {
    const active = panel.id === `panel-${name}`;
    panel.classList.toggle('is-active', active);
    panel.hidden = !active;
  });
}

document.querySelectorAll('.tab').forEach((btn) => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

document.getElementById('open-options')?.addEventListener('click', (e) => {
  e.preventDefault();
  if (chrome.runtime.openOptionsPage) {
    chrome.runtime.openOptionsPage();
  } else {
    window.open(chrome.runtime.getURL('options/index.html'));
  }
});

document.getElementById('music-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const status = document.getElementById('music-status');
  const list = document.getElementById('music-results');
  const q = document.getElementById('music-q').value.trim();
  list.innerHTML = '';
  setStatus(status, 'Searching…');

  const { musicApiBase } = await loadSettings();
  const base = musicApiBase.replace(/\/$/, '');
  const url = `${base}/api/tracks?q=${encodeURIComponent(q)}&limit=20`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const tracks = Array.isArray(data) ? data : data.tracks || data.items || [];
    if (!tracks.length) {
      setStatus(status, 'No tracks found. Is melotunez-backend running?');
      return;
    }
    setStatus(status, `${tracks.length} result(s)`);
    for (const t of tracks) {
      const li = document.createElement('li');
      const title = document.createElement('div');
      title.className = 'title';
      title.textContent = t.title || t.name || 'Untitled';
      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = [t.artist, t.album, t.genre].filter(Boolean).join(' · ');
      li.append(title, meta);
      list.appendChild(li);
    }
  } catch (err) {
    setStatus(
      status,
      `Music API failed (${err.message}). Start melotunez-backend or set Music API base in Options.`,
      true,
    );
  }
});

document.getElementById('build-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const status = document.getElementById('build-status');
  const out = document.getElementById('build-out');
  const prompt = document.getElementById('build-q').value.trim();
  out.hidden = true;
  out.textContent = '';

  if (!prompt) {
    setStatus(status, 'Enter a build question.', true);
    return;
  }

  const settings = await loadSettings();
  if (!settings.aiApiKey && settings.aiProvider !== 'ollama') {
    setStatus(status, 'Add an AI API key in Options (or use Ollama).', true);
    return;
  }

  setStatus(status, `Calling ${settings.aiProvider}…`);

  const baseUrl = (settings.aiBaseUrl || DEFAULTS.aiBaseUrl).replace(/\/$/, '');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (settings.aiApiKey) {
    headers.Authorization = `Bearer ${settings.aiApiKey}`;
  }
  if (settings.aiProvider === 'openrouter') {
    headers['HTTP-Referer'] = 'https://github.com/KryzenFlow/Dashboard-CavernWolf';
    headers['X-Title'] = 'MeloTunez Extension';
  }

  try {
    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: settings.aiModel || DEFAULTS.aiModel,
        messages: [
          {
            role: 'system',
            content:
              'You are MeloTunez Build assistant. Help the user discover approaches and scaffold web apps. Be concise. Do not claim to run Base44 AI.',
          },
          { role: 'user', content: prompt },
        ],
        temperature: 0.4,
      }),
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`HTTP ${res.status}: ${body.slice(0, 200)}`);
    }
    const data = await res.json();
    const text =
      data.choices?.[0]?.message?.content ||
      data.message?.content ||
      JSON.stringify(data, null, 2);
    out.textContent = text;
    out.hidden = false;
    setStatus(status, 'Done (pluggable provider — not Base44 AI)');
  } catch (err) {
    setStatus(status, `AI request failed: ${err.message}`, true);
  }
});
