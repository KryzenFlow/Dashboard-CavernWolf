# MeloTunez Chrome extension (MV3)

Search-like side panel for **music discovery** and **build/app** prompts. Music hits your Express wrapper; AI uses a pluggable OpenAI-compatible provider (OpenRouter, Groq, Together, Ollama, …). **No Base44 AI.**

See product direction: [`docs/melotunez-direction.md`](../docs/melotunez-direction.md).

## Load unpacked (Chrome)

1. Start the music API (optional for Music tab):

   ```bash
   cd melotunez-backend && npm start
   # http://localhost:3001 — GET /api/tracks?q=
   ```

2. Open `chrome://extensions` → enable **Developer mode**.
3. **Load unpacked** → select this folder: `melotunez-extension/`.
4. Click the MeloTunez toolbar icon (opens the **side panel**).
5. Open **Options** → set Music API base (default `http://localhost:3001`) and an AI provider + key.

Chrome Web Store packaging can come later; this scaffold is for local / review builds.

## Layout

```
melotunez-extension/
├── manifest.json
├── background/service-worker.js
├── sidepanel/          Music | Build tabs
├── options/            provider + keys in chrome.storage.local
└── icons/
```

## Music tab

`GET {musicApiBase}/api/tracks?q=&limit=20`

Requires `melotunez-backend` (or any compatible REST) and host permission for that origin. Add production origins to `manifest.json` `host_permissions` when you deploy.

## Build tab

Calls `{aiBaseUrl}/chat/completions` with the key from Options. Presets:

| Provider   | Default base URL |
| ---------- | ---------------- |
| OpenRouter | `https://openrouter.ai/api/v1` |
| Groq       | `https://api.groq.com/openai/v1` |
| Together   | `https://api.together.xyz/v1` |
| Ollama     | `http://localhost:11434/v1` |
| OpenAI     | `https://api.openai.com/v1` |

For Anthropic direct API, use an OpenAI-compatible proxy (or LiteLLM) and set **Custom**.

## Security

- AI keys: `chrome.storage.local` only — not committed.
- Base44 music key stays on the Express server; the extension never embeds it.
- Expand `host_permissions` carefully when pointing at non-localhost APIs.

## Phased roadmap

1. Music dashboard + Express — done  
2. AI search via OpenRouter/Ollama — side panel Build tab (this scaffold)  
3. Extension shell — this folder  
4. OpenManus-like agent tools — later (not OpenGrok; that is code search)
