# MeloTunez product direction

Short architecture note: keep Base44 (or the Express wrapper) for **music entities only**, and route **AI / search / build** through a pluggable provider you control — not Base44 AI credits or functions.

## Goals

1. Avoid paying Base44 large recurring fees for AI features or giving it full control of the product brain.
2. Offer a search-like surface for **music discovery** and **building things** (web apps, agents, tooling).
3. Ship as a **Chrome MV3 extension** (Chrome Web Store developer fee already paid).
4. Stay portable: swap LLM backends without rewriting the app.

## What Base44 is good for (and what it isn’t)

| Use Base44 for | Avoid Base44 for |
| --- | --- |
| Existing Track / Playlist / User entities | Chat, codegen, agent loops (`assistantChat`, invokeLLM, etc.) |
| Short-term music CRUD while you own the UX | Long-term “platform brain” or hosted AI credits |
| Fast entity API via `@base44/sdk` (already wrapped) | Auth/DB/AI lock-in if the product grows |

**Lock-in / cost summary:** Base44 is strong for prompt-to-app MVPs. Pricing is credit-based (message + integration credits; plans roughly free → ~$16–$160+/mo billed annually). Backend logic, managed DB, and platform AI sit behind their SDK — frontend export does not mean you own the server or AI stack. For MeloTunez, treat Base44 as a **temporary music data plane**, not the AI platform.

Option 3 SDK snippet (already in-repo via Express wrapper):

```js
createClient({
  appId: "6a8bbac67d8d3dfc43538a00",
  headers: { "api_key": "…" } // keep on server only
});
```

`melotunez-backend` already hides the key and exposes REST (`GET /api/tracks?q=`, playlists, users). Prefer that path from the dashboard and extension.

## Pluggable AI backends (recommended)

Use one **OpenAI-compatible** client interface. Select provider via env / extension options — never hardcode Base44 AI.

| Provider | Role | Notes |
| --- | --- | --- |
| **OpenRouter** | Default cloud gateway | One key → many models (Claude, GPT, Llama, etc.). Small platform fee; best “try many models” option. |
| **Groq** | Fast / cheap inference | Great latency; narrower model set; solid free-tier for experiments. |
| **Together** | Open-weight hosting | Predictable OSS model pricing; fine-tune friendly. |
| **Ollama / local** | Zero token cost, private | `http://localhost:11434/v1` — best for offline / privacy; needs local GPU/CPU. |
| **Anthropic / OpenAI direct** | Premium quality | Use when you want one vendor SLA; still behind the same adapter. |
| **Any OpenAI-compatible proxy** | Self-host / LiteLLM | Same `base_url` + `api_key` pattern. |

**Do not** call Base44 `assistantChat` / integration AI for product features going forward. Deprecate that route once the pluggable chat path exists.

Suggested config shape (backend or extension options):

```text
AI_PROVIDER=openrouter|groq|together|ollama|openai|anthropic
AI_BASE_URL=https://openrouter.ai/api/v1   # or provider default
AI_API_KEY=…                               # extension: chrome.storage.local
AI_MODEL=openai/gpt-4o-mini                # provider-specific id
```

## OpenManus vs OpenGrok (naming)

These are **different products**:

| Name | What it is | Fit for MeloTunez |
| --- | --- | --- |
| **[OpenManus](https://github.com/FoundationAgents/OpenManus)** | Open-source **AI agent** framework (plan → browse → tools → code). Multi-provider LLMs, MCP support. | **Yes** for “build web apps / agent tools” later (phase 4). |
| **[OpenGrok](https://oracle.github.io/opengrok/)** | Java **source-code search** / cross-reference engine (Oracle). Not an AI agent. | Useful only if you index large codebases for agents to search — optional later, not the music product core. |

If the goal is “search-like area that builds things,” lean **OpenManus-style agents** + your own UI. Use OpenGrok (or similar code search) only as a **tool** the agent can call when browsing big repos.

## Target architecture

```text
┌─────────────────────────────────────────────────────────┐
│  Chrome MV3 extension (melotunez-extension/)            │
│  side panel: Music | Build tabs                         │
│  options: API keys in chrome.storage.local              │
└───────────────┬─────────────────────┬───────────────────┘
                │                     │
                ▼                     ▼
     melotunez-backend           AI provider adapter
     (Express, Base44 music)     (OpenRouter / Ollama / …)
     GET /api/tracks?q=          chat + tools (no Base44 AI)
                │
                ▼
           Base44 entities
           (tracks/playlists/users only)
```

- **Music path:** extension / React dashboard → Express → Base44 entities.
- **AI / build path:** extension / dashboard → pluggable OpenAI-compatible API (keys local or server env).
- **Optional later:** OpenManus-like tool loop (filesystem, browser, scaffold web apps) behind the Build tab.

## Chrome extension shape (MV3)

| Piece | Purpose |
| --- | --- |
| `side_panel` (or popup) | Unified search UI: Music query + Build/app query tabs |
| `background` service worker | Open side panel, message routing, future alarms |
| `options` page | Provider, model, API key, music API base URL — **local storage only** |
| Content scripts | Optional later (inject helpers on builder pages) |

Music search should hit `GET {MUSIC_API_BASE}/api/tracks?q=` (default `http://localhost:3001`) when the Express backend is running. Document CORS / host permission for production URLs.

## Phased plan

| Phase | Deliverable | Status |
| --- | --- | --- |
| **1** | Music dashboard + Express Base44 wrapper | Done (`melotunez-frontend`, `melotunez-backend`) |
| **2** | AI search/chat via OpenRouter or Ollama (env-selected), not Base44 AI | Next |
| **3** | Chrome extension shell (side panel + options keys) | Scaffold in `melotunez-extension/` |
| **4** | OpenManus-like agent tools (build web apps, browse, code tools); optional OpenGrok for big-repo search | Later |

## Security notes

- Keep Base44 `api_key` on the **server** (Express). Do not add new secrets to the extension bundle.
- Extension AI keys live in `chrome.storage.local` via the options page.
- Prefer host permissions scoped to your music API origin.

## Related paths

- `melotunez-frontend/` — React music dashboard  
- `melotunez-backend/` — Express REST wrapper  
- `melotunez-extension/` — Chrome MV3 scaffold  
- PR: https://github.com/KryzenFlow/Dashboard-CavernWolf/pull/3  
