# Clinic Portal Module

Split from the second section of the original Copilot export (BAA compliance + CockroachDB clinic workflows).

> Operates under the repo [Trust Discipline Framework](../soul.md). Load `soul.md` and `CI.md` before any clinic agent session.

## Contents

| Path | Purpose |
|------|---------|
| `compliance/BAA_CHECKLIST.md` | HIPAA/BAA vendor checklist |
| `schemas/clinic_chiropractor_001.sql` | Per-clinic siloed schema template |
| `docker-compose.sandbox.yml` | Local CockroachDB sandbox (mock data only) |
| `vscode/tasks.json` | VS Code Hermes agent launchers |

## Run sandbox database

```bash
cd clinic
docker compose -f docker-compose.sandbox.yml up
```

Admin UI: http://localhost:8080  
SQL port: `26257`

## Important

- Never commit production PHI schemas or credentials
- Use mock data only in the sandbox container (`restart: "no"` wipes data on stop)
