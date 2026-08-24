# doctor_amnesia.md — Amnesia Protocol

Agents and workers in this repo must not keep intermediate workspace bloat.

## Rules

1. When a task is **logged** (HMAC ledger / control decision), drop scratch
   notes, temp files, and chat cycle memory for that cycle.
2. Hermes already wipes `$HERMES_HOME/memory` and `sessions` on
   terminate-after-use. Do not recreate long-lived dumps beside them.
3. Claw Opus refuses a second `/chat` in the same process. Do not patch
   that away to "keep context."
4. Prefer MCP → Google Drive (or equivalent) for research dumps instead of
   committing them under `source/`, `docs/inbox/`, or the repo root.
5. Daily rebuild (UTC) is a full amnesia of Merkle leaves + ledger files
   (new genesis). Old tokens are invalid after rebuild — open a new parent
   session.

## Not amnesia

- Source code, skills intentionally saved via `/skill/save`, and this
  blueprint remain on disk.
- Audit ledger entries during a day are append-only until daily rebuild.
