# Setup scripts

## One-command bootstrap (recommended)

**Windows (PowerShell):**

```powershell
cd E:\Dashboard-CavernWolf
powershell -ExecutionPolicy Bypass -File .\scripts\setup_stack.ps1
```

**Linux / macOS / Git Bash:**

```bash
cd /path/to/Dashboard-CavernWolf
bash scripts/setup_stack.sh
```

These scripts:

1. Create any missing folders (`backend/agents/`, `agent_claw/`, `templates/`, etc.)
2. Copy `.env.example` → `.env` if needed
3. Validate `docker compose config`
4. Run `docker compose up --build`

They **do not** overwrite existing Python code — your Hermes brain stack stays intact.

## Bing / Code Genie minimal script vs this repo

A minimal `setup_stack.sh` from Code Genie creates a **basic** backend (SQLite only, no Hermes Studio, no Redis/Chroma brain). **This repository is the production version** with:

| Feature | Minimal bootstrap | Dashboard-CavernWolf |
|---------|-------------------|----------------------|
| Hermes Studio UI | No | Yes (`frontend/`, port 3000) |
| Brain (STM/LTM) | SQLite only | Redis + Chroma + SQLite |
| SOUL.md identity | No | Yes |
| LlamaIndex orchestration | No | Yes (`backend/agents/`) |
| GitHub CI / Pages | No | Yes (`.github/workflows/`) |
| LLaMA without model file | Fails | Works (`llama_stub` + `LLM_PROVIDER=mock`) |

Use the scripts in **this folder** for the full stack. Do not replace `backend/main.py` with the minimal Bing template.

## Manual steps

```powershell
cp .env.example .env
docker compose up --build
```

Real local LLaMA (optional):

1. Put a `.gguf` file in `./models/`
2. Set `LLM_PROVIDER=llama` in `.env`
3. `docker compose --profile llama-local up --build`
