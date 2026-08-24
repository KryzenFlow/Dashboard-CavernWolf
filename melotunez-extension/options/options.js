const DEFAULTS = {
  musicApiBase: 'http://localhost:3001',
  aiProvider: 'openrouter',
  aiBaseUrl: 'https://openrouter.ai/api/v1',
  aiModel: 'openai/gpt-4o-mini',
  aiApiKey: '',
};

const PROVIDER_PRESETS = {
  openrouter: {
    aiBaseUrl: 'https://openrouter.ai/api/v1',
    aiModel: 'openai/gpt-4o-mini',
  },
  groq: {
    aiBaseUrl: 'https://api.groq.com/openai/v1',
    aiModel: 'llama-3.3-70b-versatile',
  },
  together: {
    aiBaseUrl: 'https://api.together.xyz/v1',
    aiModel: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
  },
  ollama: {
    aiBaseUrl: 'http://localhost:11434/v1',
    aiModel: 'llama3.2',
  },
  openai: {
    aiBaseUrl: 'https://api.openai.com/v1',
    aiModel: 'gpt-4o-mini',
  },
  anthropic: {
    aiBaseUrl: 'https://api.anthropic.com/v1',
    aiModel: 'claude-sonnet-4-20250514',
  },
  custom: {
    aiBaseUrl: '',
    aiModel: '',
  },
};

async function hydrate() {
  const stored = await chrome.storage.local.get(Object.keys(DEFAULTS));
  const values = { ...DEFAULTS, ...stored };
  for (const key of Object.keys(DEFAULTS)) {
    const el = document.getElementById(key);
    if (el) el.value = values[key] ?? '';
  }
}

document.getElementById('aiProvider').addEventListener('change', (e) => {
  const preset = PROVIDER_PRESETS[e.target.value];
  if (!preset) return;
  if (preset.aiBaseUrl) document.getElementById('aiBaseUrl').value = preset.aiBaseUrl;
  if (preset.aiModel) document.getElementById('aiModel').value = preset.aiModel;
});

document.getElementById('options-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {};
  for (const key of Object.keys(DEFAULTS)) {
    payload[key] = document.getElementById(key).value.trim();
  }
  await chrome.storage.local.set(payload);
  const status = document.getElementById('save-status');
  status.textContent = 'Saved.';
  setTimeout(() => {
    status.textContent = '';
  }, 2000);
});

hydrate();
