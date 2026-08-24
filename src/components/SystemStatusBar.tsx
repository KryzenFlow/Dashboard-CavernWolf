import type { SystemStatus } from "../types";

type Props = {
  status: SystemStatus | null;
  error?: string | null;
};

export function SystemStatusBar({ status, error }: Props) {
  const agentSummary = status?.agents.length
    ? status.agents.map((agent) => `${agent.name}:${agent.status}`).join(" · ")
    : "agents —";
  const ports = status
    ? `ports hermes:${status.ports.hermes} claw:${status.ports.claw}`
    : "ports —";
  const containers = status?.containers.length
    ? `containers ${status.containers.join(", ")}`
    : "containers none reported";
  const ts = status?.tailscale_ip ? `tailscale ${status.tailscale_ip}` : "tailscale ip unknown";
  const claw = status?.claw.listening ? "claw listening" : "claw halted/unknown";

  return (
    <footer className="system-status-bar status-bar" role="status" aria-live="polite">
      <span className={`pill ${status?.claw.listening ? "ok" : "bad"}`}>{claw}</span>
      <span className="pill">Hermes {status?.hermes.ready ? "ready" : "…"}</span>
      <span title={agentSummary}>agents {status?.agents_count ?? 0}</span>
      <span>{ports}</span>
      <span title={containers}>{containers}</span>
      <span>{ts}</span>
      <span className={`pill ${status?.memory.redis ? "ok" : "warn"}`}>
        redis {status?.memory.redis ? "up" : "n/a"}
      </span>
      <span className={`pill ${status?.memory.vector ? "ok" : "warn"}`}>
        vector {status?.memory.vector ? "up" : "n/a"}
      </span>
      {error ? <span className="status-error pill bad">{error}</span> : null}
    </footer>
  );
}

export default SystemStatusBar;
