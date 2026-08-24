/**
 * Pluggable OpenAI-compatible chat (OpenRouter / Ollama / Groq / …).
 * Selected via AI_* env vars — never Base44 AI credits.
 *
 * See docs/melotunez-direction.md and melotunez-extension options.
 */

const PROVIDER_DEFAULTS = {
  openrouter: {
    baseUrl: 'https://openrouter.ai/api/v1',
    model: 'openai/gpt-4o-mini',
  },
  groq: {
    baseUrl: 'https://api.groq.com/openai/v1',
    model: 'llama-3.1-8b-instant',
  },
  together: {
    baseUrl: 'https://api.together.xyz/v1',
    model: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
  },
  ollama: {
    baseUrl: 'http://127.0.0.1:11434/v1',
    model: 'llama3.2',
  },
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
  },
  anthropic: {
    baseUrl: 'https://api.anthropic.com/v1',
    model: 'claude-3-5-haiku-latest',
  },
};

function providerKey() {
  return String(process.env.AI_PROVIDER || 'openrouter')
    .toLowerCase()
    .trim();
}

export function getAiConfig() {
  const provider = providerKey();
  const defaults = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.openrouter;
  return {
    provider,
    baseUrl: (process.env.AI_BASE_URL || defaults.baseUrl).replace(/\/$/, ''),
    apiKey: process.env.AI_API_KEY || '',
    model: process.env.AI_MODEL || defaults.model,
  };
}

/** True when env is enough to call a pluggable provider (Ollama needs no key). */
export function isPluggableAiConfigured() {
  const { provider, apiKey } = getAiConfig();
  if (provider === 'ollama') return true;
  return Boolean(apiKey);
}

function buildMessages(payload) {
  const system = {
    role: 'system',
    content:
      'You are the MeloTunez dashboard assistant. Help with tracks, playlists, and catalog questions. Be concise. Do not claim to be Base44 AI.',
  };

  if (Array.isArray(payload?.messages) && payload.messages.length > 0) {
    const normalized = payload.messages
      .filter((m) => m && (m.role === 'user' || m.role === 'assistant'))
      .map((m) => ({
        role: m.role,
        content: String(m.content ?? ''),
      }))
      .filter((m) => m.content.trim());
    return [system, ...normalized];
  }

  const text =
    payload?.message ||
    payload?.prompt ||
    payload?.content ||
    payload?.text ||
    '';
  return [system, { role: 'user', content: String(text) }];
}

/**
 * Call OpenAI-compatible /chat/completions.
 * @returns {{ reply: string, provider: string, model: string, raw?: unknown }}
 */
export async function pluggableChat(payload) {
  const config = getAiConfig();
  if (!isPluggableAiConfigured()) {
    const err = new Error(
      'Pluggable AI is not configured. Set AI_API_KEY (or AI_PROVIDER=ollama) on melotunez-backend.',
    );
    err.status = 503;
    err.code = 'ai_not_configured';
    throw err;
  }

  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
  if (config.apiKey) {
    headers.Authorization = `Bearer ${config.apiKey}`;
  }
  if (config.provider === 'openrouter') {
    headers['HTTP-Referer'] =
      process.env.AI_HTTP_REFERER ||
      'https://github.com/KryzenFlow/Dashboard-CavernWolf';
    headers['X-Title'] = process.env.AI_X_TITLE || 'MeloTunez Dashboard';
  }

  const response = await fetch(`${config.baseUrl}/chat/completions`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model: config.model,
      messages: buildMessages(payload),
      temperature: 0.4,
    }),
  });

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
  }

  if (!response.ok) {
    const message =
      (data && typeof data === 'object' && (data.error?.message || data.error || data.message)) ||
      text?.slice(0, 300) ||
      `AI provider HTTP ${response.status}`;
    const err = new Error(String(message));
    err.status = response.status >= 400 && response.status < 600 ? response.status : 502;
    err.code = 'ai_provider_error';
    err.provider = config.provider;
    throw err;
  }

  const reply =
    data?.choices?.[0]?.message?.content ||
    data?.message?.content ||
    data?.reply ||
    (typeof data === 'string' ? data : null);

  if (!reply) {
    const err = new Error('AI provider returned an empty response.');
    err.status = 502;
    err.code = 'ai_empty_response';
    throw err;
  }

  return {
    reply: String(reply),
    provider: config.provider,
    model: config.model,
    source: 'pluggable',
  };
}

export function isBase44AssistantUnavailable(err) {
  const message = String(
    err?.response?.data?.message ||
      err?.response?.data?.error ||
      err?.message ||
      '',
  ).toLowerCase();
  return (
    message.includes('not yet available') ||
    message.includes('unknown function') ||
    message.includes('function does not exist') ||
    (message.includes('not found') && message.includes('assistant')) ||
    (message.includes('not available') && message.includes('assistant'))
  );
}
