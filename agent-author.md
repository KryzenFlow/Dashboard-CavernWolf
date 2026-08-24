# Agent authoring

How an agent (or operator) adds an extension in this repo without a false
environment. Hermes is the orchestrator. Claw Opus is the only worker that
runs the work.

## 1. Preconditions

- `HERMES_SUPERVISOR_HMAC_KEY` and `OPENCLAW_GATEWAY_URL` are real (Bitwarden
  at runtime). Empty / `mock` / `dev-change-me` values refuse to boot.
- A parent session exists (`session.create` over `/ws`). The returned
  `lifecycle_token` is already in the Merkle tree.
- You are not asking a child to call Claw or Hermes. Children only have
  `tool:ask_parent`.

## 2. Write the skill on disk

Hermes persists skills under `$HERMES_HOME/skills`. Use the parent token.

```http
POST /skill/save
X-Lifecycle-Token: <parent token JSON>
Content-Type: application/json

{
  "path": "skills/my_extension.py",
  "language": "python",
  "content": "def run(input_text: str) -> str:\n    return input_text.strip()\n"
}
```

Path confinement blocks `..`, absolute paths, and destructive command
patterns. Doberman blocks private-key blobs. Fail closed — do not retry with
a mock path.

## 3. Syntax-check (no mock pass)

```http
POST /skill/test
X-Lifecycle-Token: <parent token JSON>
Content-Type: application/json

{"path":"skills/my_extension.py","code":"<same source>"}
```

This is `compile(...)`. A greeting stub is not injected if the tree is empty.

## 4. Ask Claw through Hermes

Do not POST to `claw-opus` from the Studio or from a child. Send a parent
chat message; Hermes gates it, then Claw calls the real OpenClaw gateway.

```javascript
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: "req-2",
  method: "message.send",
  params: {
    session_id,
    lifecycle_token,
    text: "Review skills/my_extension.py and keep the change fail-closed.",
  },
}));
```

If Claw is down, the gateway is unset, or the Merkle root is missing, the
UI gets an `error` event. Hermes does not invent a reply.

## 5. Cycle end

On `message.complete` (or WebSocket disconnect) Hermes:

1. Halts the docked Claw daemon (`POST /internal/halt` → process exit).
2. Wipes `$HERMES_HOME/memory` and `sessions` (tmpfs in compose).
3. Leaves Merkle genesis in place until the daily rebuild.

Claw will not accept a second `/chat` in the same process (`cycle already
used`). Compose `restart: unless-stopped` brings up an empty daemon that
must see a live root again.

## 6. Daily rebuild

UTC hour `CLAW_DAILY_REBUILD_HOUR_UTC` (default 4) or:

```http
POST /control/daily-rebuild
X-Lifecycle-Token: <parent token with orch:ask_hermes>
```

New Merkle genesis, empty ledger, Claw halt. Old tokens are not in the new
tree. Open a new parent session.

## 7. What not to author

- Mock agents, echo servers, or `HERMES_MOCK=1`.
- Child tokens with `orch:ask_hermes`, `claw:invoke`, or `ws:message.send`.
- Git commit/push from the dashboard.
- Long-lived Claw memory files. Stacked memory is why Claw stops listening.
