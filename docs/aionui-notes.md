# AionUi notes (reference only)

Upstream: [iOfficeAI/AionUi](https://github.com/iOfficeAI/AionUi) · License: **Apache-2.0** · Site: [aionui.com](https://www.aionui.com)

Local shallow clone (optional, **not** committed): `/workspace/vendor/AionUi`

```bash
mkdir -p vendor
git clone --depth 1 https://github.com/iOfficeAI/AionUi.git vendor/AionUi
```

## What it is

AionUi is an open-source **desktop “Cowork” app** for AI agents: built-in agent engine, multi-agent ACP backends (Claude Code, Codex, Hermes, OpenClaw, Gemini CLI, …), MCP tools, assistants/skills, preview of agent outputs, scheduled cron, and remote WebUI / chat channels.

It is a **general AI agent / office automation UI**, not a music streaming product. Relevance to MeloTunez is mainly **stack + module layout** (how they split agent / chat / preview / settings / workspace), not domain fit.

## Stack (matches the Function Development Spec template)

| Piece | AionUi |
| --- | --- |
| Shell | Electron **37** (`electron-vite`) |
| UI | React **19** + TypeScript |
| Components | **Arco Design** (`@arco-design/web-react`) |
| CSS | **UnoCSS** (+ CSS Modules) |
| Local DB | **better-sqlite3** |
| Package manager | **bun** |
| Backend (dev) | Separate **AionCore** (Rust) binary `aioncore` |

## How to run

**End users:** download from [Releases](https://github.com/iOfficeAI/AionUi/releases) or `brew install aionui` → paste any LLM API key → cowork.

**Developers** (two repos; see [development.md](https://github.com/iOfficeAI/AionUi/blob/main/docs/contributing/development.md)):

```bash
# 1) Build AionCore backend
git clone https://github.com/iOfficeAI/AionCore.git
cd AionCore && cargo install --path crates/aionui-app --locked
export PATH="$HOME/.cargo/bin:$PATH"

# 2) Start Electron UI
git clone https://github.com/iOfficeAI/AionUi.git
cd AionUi && bun install && bun run start
```

Also: `bun run webui` for browser-based mode (no Electron window).

## Architecture (map to the template domains)

Electron processes (never mix APIs):

| Process | Path | Role |
| --- | --- | --- |
| Main | `packages/desktop/src/process/` | Node/Electron: IPC bridge, SQLite, skills, backend launch |
| Preload | `packages/desktop/src/preload/` | `contextBridge` IPC |
| Renderer | `packages/desktop/src/renderer/` | React UI only (no Node) |

Rough map to **agent / dialog / preview / settings / workspace**:

| Template concept | AionUi location |
| --- | --- |
| **Dialog** (chat) | `renderer/pages/conversation/` (+ `components/chat/`) |
| **Agent** | `renderer/components/agent/`, hooks, ACP platforms under conversation; main-process agent backends via AionCore / ACP |
| **Preview** | `renderer/pages/conversation/Preview/` (agent file/output preview) |
| **Settings** | `renderer/pages/settings/` (LLM providers, skills, agents, appearance, …) |
| **Workspace** | `renderer/components/workspace/`, workspace utils; shared folder for team mode |

Other product areas (not in a minimal music app): **teams**, **cron**, **remote channels**, **pet**, office assistants (PPT/Word/Excel).

Monorepo packages: `desktop`, `web-host`, `web-cli`, `shared-scripts`.

## vs MeloTunez (this repo)

| | MeloTunez (current) | AionUi |
| --- | --- | --- |
| Surface | Web dashboard + **Chrome MV3** side panel | Electron desktop (+ optional WebUI) |
| Domain | Music entities (Base44 via Express) + cheap pluggable AI | Multi-agent cowork / office / codegen |
| AI | OpenRouter / Groq / Ollama adapter; avoid Base44 AI | Full agent engine + 30+ LLM platforms + CLI agents |
| Complexity | Small Express + Vite React + extension scaffold | Large Electron + Rust core + multi-agent |

MeloTunez goals (Chrome store, music discovery, cheap AI, no Base44 AI lock-in) are **orthogonal** to AionUi’s product. Forking AionUi would pull a huge agent desktop shell you do not need for phases 1–3.

## Options

| Option | Meaning | When |
| --- | --- | --- |
| **A** | Keep MeloTunez web + extension; use AionUi only as **prompt/spec/style** reference (module naming, IPC patterns, Arco/UnoCSS if you ever go desktop) | Default for music + extension path |
| **B** | Fork AionUi as the desktop shell and graft music into it | Only if primary UX becomes local multi-agent cowork + files — not for Chrome-first music |
| **C** | **Hybrid:** ship web dashboard + extension now; revisit AionUi (or a thin Electron shell) later for local agent/build tools | Best if you might want desktop agents in phase 4 without blocking phases 2–3 |

**Default recommendation: C with A’s near-term behavior** — finish pluggable AI + extension; do not fork AionUi into this PR. Optionally keep `vendor/AionUi` gitignored for local reading.

## Clone command (do not vendor-commit upstream)

```bash
git clone --depth 1 https://github.com/iOfficeAI/AionUi.git vendor/AionUi
# optional sparse: docs + packages/desktop only
```

`vendor/` is gitignored so the MeloTunez PR stays focused.
