# Desktop reference exports

These files were copied from:

`OneDrive\Desktop\New Project Workspace\Data for Dashboard all loose files and some have Vellorae`

## Do not paste into live code

| File | Status |
|------|--------|
| `FastAPI application for Hermes web.txt` | **Outdated** — has old `HERMES_MOCK` default `"1"`. Use `backend/web_gateway/app.py` in the repo instead. |
| `Hermes Studio as a safe, customer-facing dashboard.txt` | **Implemented** — Express/Bing version; repo uses FastAPI + `studio_security.py`. |
| `setupstack.sh` | **Superseded** — minimal bootstrap. Use `scripts/setup_stack.ps1` + root `docker-compose.yml`. |
| `*agent_r_*.txt`, `Folder Structure.txt`, etc. | **Reference only** — architecture notes from chat exports. |

## What to use instead

| Goal | Use in repo |
|------|-------------|
| Public customer dashboard | `frontend/` + `STUDIO_MODE=public` |
| Private Agent Ops | `ops_dashboard/` + `STUDIO_MODE=internal` |
| Switch vertical / bleed | `shared/workflows/bleed-manifest.yaml` + `ACTIVE_BLEED` |
| Vellorae clinic agency | `bleeds.vellorae` in manifest + `backend/agents/prompts/vellorae_clinic.txt` |
| Bootstrap stack | `docker compose up --build` from repo root |

Re-sync from Desktop:

```powershell
.\scripts\sync_desktop_reference.ps1
```
