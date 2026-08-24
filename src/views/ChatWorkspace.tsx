import { useState } from "react";
import type { AgentPublic } from "../types";
import { API_BASE, routeAgent } from "../api";

type ChatMessage = { role: "user" | "system"; text: string };

type Props = {
  selected: AgentPublic | null;
  onScore: (line: string) => void;
};

function wsUrl(apiBase: string): string {
  const base = (apiBase || "").replace(/\/$/, "");
  if (!base) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${location.host}/ws`;
  }
  return `${base.replace(/^http/, "ws")}/ws`;
}

function rpc(
  socket: WebSocket,
  method: string,
  params: Record<string, unknown>,
  id?: string,
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const reqId = id || `req-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const onMessage = (event: MessageEvent<string>) => {
      let msg: { id?: string; error?: { message?: string }; result?: Record<string, unknown> };
      try {
        msg = JSON.parse(event.data) as typeof msg;
      } catch {
        return;
      }
      if (msg.id === reqId) {
        socket.removeEventListener("message", onMessage);
        if (msg.error) reject(new Error(msg.error.message || JSON.stringify(msg.error)));
        else resolve(msg.result || {});
      }
    };
    socket.addEventListener("message", onMessage);
    socket.send(JSON.stringify({ jsonrpc: "2.0", id: reqId, method, params }));
  });
}

async function hermesToClaw(text: string, onScore: (line: string) => Promise<void> | void): Promise<string> {
  const url = wsUrl(API_BASE);
  const socket = new WebSocket(url);
  await new Promise<void>((resolve, reject) => {
    socket.onopen = () => resolve();
    socket.onerror = () => reject(new Error("WebSocket failed to open"));
  });
  let deltas = "";
  socket.addEventListener("message", (event: MessageEvent<string>) => {
    try {
      const msg = JSON.parse(event.data) as {
        method?: string;
        params?: { type?: string; payload?: { text?: string } };
      };
      if (msg.method === "event" && msg.params?.type === "message.delta") {
        deltas += msg.params.payload?.text || "";
      }
      if (msg.method === "event" && msg.params?.type === "error") {
        deltas += msg.params.payload?.text || "error";
      }
    } catch {
      /* ignore malformed frames */
    }
  });
  const created = await rpc(socket, "session.create", { session_key: `studio-${Date.now()}` });
  onScore(`[session] merkle=${String(created.merkle_root || "?")} agent=${String(created.agent || "claw-opus")}`);
  await rpc(socket, "message.send", {
    session_id: created.session_id,
    text,
    lifecycle_token: created.lifecycle_token,
  });
  socket.close();
  return deltas || "(Claw cycle complete — empty reply or halted)";
}

export function ChatWorkspace({ selected, onScore }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    const text = draft.trim();
    if (!text || !selected) return;
    setBusy(true);
    setMessages((prev) => [...prev, { role: "user", text }]);
    setDraft("");
    try {
      if (selected.role === "hermes" || selected.role === "claw_opus") {
        const reply = await hermesToClaw(text, onScore);
        setMessages((prev) => [...prev, { role: "system", text: reply }]);
        onScore(`[chat] hermes→claw complete`);
        return;
      }
      const result = await routeAgent(selected.id, text);
      const plan = result.plan || result.result || result;
      setMessages((prev) => [
        ...prev,
        { role: "system", text: typeof plan === "string" ? plan : JSON.stringify(plan, null, 2) },
      ]);
      onScore(`[route] ${selected.id} plan-only (no direct Claw)`);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [...prev, { role: "system", text: `Error: ${message}` }]);
      onScore(`[error] ${message}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2 className="panel-title">Chat Workspace · {selected?.name || "No agent"}</h2>
      <div className="chat-log">
        {messages.map((msg, idx) => (
          <div key={`${msg.role}-${idx}`} className={`bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="composer">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={
            selected?.role === "claw_opus"
              ? "Message Claw Opus (Hermes mediates the cycle)…"
              : "Message selected agent…"
          }
        />
        <div className="row">
          <button className="btn primary" type="button" disabled={busy || !selected} onClick={() => void send()}>
            {busy ? "Sending…" : "Send"}
          </button>
          <span className="pill">
            {selected?.role} · {selected?.model || selected?.style}
          </span>
        </div>
      </div>
    </section>
  );
}

export default ChatWorkspace;
