# Examples

Practical calls against this repo. Hermes orchestrates. Claw Opus is the only
agent. There is no mock backend and no echo fallback.

## Tools

### Parent session (Studio → Hermes)

```javascript
ws.send(JSON.stringify({
  jsonrpc: "2.0",
  id: "req-1",
  method: "session.create",
  params: { session_key: "studio" },
}));
```

Hermes returns a parent `lifecycle_token` bound into the Merkle tree. REST
calls must send it:

```http
GET /files?type=all
X-Lifecycle-Token: {"tree_id":"...","merkle_root":"...","sig":"..."}
```

```http
POST /skill/save
X-Lifecycle-Token: {...}
Content-Type: application/json

{"path":"skills/hello.py","content":"def run(x):\n    return x\n","language":"python"}
```

Git commit/push are not dashboard tools. `GET /git/status` is read-only.

### Child tokens (attenuated)

Children ask the parent. They cannot inherit orchestrator or Claw caps.

```python
from web_gateway.security.token import issue_child_token, issue_token

parent = issue_token(
    tree_id="t1",
    agent_id="parent-1",
    capabilities=["tool:grant_child", "tool:ask_parent", "orch:ask_hermes"],
    ttl_seconds=120,
    merkle_root=live_root,
    role="parent",
)
child = issue_child_token(parent, ["tool:ask_parent"], ttl=30)
# issue_child_token(..., ["orch:ask_hermes"]) raises SecurityError
```

### Claw Opus (Hermes → worker)

Only Hermes calls Claw. The worker requires a live Merkle root and a real
OpenClaw gateway.

```http
POST http://claw-opus:9000/chat
Content-Type: application/json

{
  "text": "summarize skills/hello.py",
  "session_id": "<parent session>",
  "merkle_root": "<current_root()>",
  "lifecycle_token": { }
}
```

Missing `OPENCLAW_GATEWAY_URL` or a missing Merkle root is a halt, not a fake reply.

## Hooks

Deterministic gates run before any worker or model. They never ask Claw for
permission.

```python
from web_gateway.security.supervisor_gates import validate_and_gate

verdict, reason = validate_and_gate(
    payload={"session_id": sid, "text": text, "merkle_root": live_root},
    token=lifecycle_token,
    action="ws:message.send",
    agent_name=agent_id,
    session_id=sid,
)
if verdict != "PASS":
    # BLOCK — no Claw call
    ...
```

Order: token + Merkle membership → path confinement → Doberman `pre_exec`.
Claw-daemon role must present the **live** root; mismatch terminates the
docked daemon.

Doberman hook (fail-closed, no model):

```python
from web_gateway.security.doberman_hook_ai import pre_exec

pre_exec(payload, agent_name=agent_id, session_id=sid, lifecycle_token=token)
# "PASS" | "BLOCK"
```

## Events

Studio WebSocket events from Hermes:

| Event | Meaning |
|-------|---------|
| `message.start` | Claw cycle started |
| `message.delta` | Real Claw text (never invented by Hermes) |
| `message.complete` | Cycle done; daemon is then halted and memory wiped |
| `error` | Claw unavailable or blocked — shown as system text, not as Claw |

```json
{"jsonrpc":"2.0","method":"event","params":{"type":"message.complete","payload":{"session_id":"..."}}}
```

Control plane:

```http
GET /control/status
```

```json
{"agent":"claw-opus","halted":false,"merkle_root":"..."}
```

`POST /control/daily-rebuild` (parent cap `orch:ask_hermes`) issues a new
Merkle genesis and wipes ledger/memory.

## Complete extension (skill on disk)

Skills are files under `$HERMES_HOME/skills`. There is no mock catalog.

```python
# skills/review_diff.py
def run(diff_text: str) -> str:
    return diff_text
```

Save via `/skill/save`, syntax-check via `/skill/test` (`compile`, not a fake
pass). Ask Claw from Studio with a parent `message.send` after the gates pass.

After the reply, Hermes calls `terminate_after_use`: Claw exits, cycle memory
is wiped, a fresh daemon may re-auth to the live root. Do not stack sessions
in memory files — Claw will refuse a second chat in the same process.
