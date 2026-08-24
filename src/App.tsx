import { useCallback, useEffect, useMemo, useState } from "react";
import { createAgent, deleteAgent, fetchPlugins, fetchSystemStatus, listAgents } from "./api";
import { AgentBuilder } from "./components/AgentBuilder";
import { AgentDelete } from "./components/AgentDelete";
import { AgentPullDown } from "./components/AgentPullDown";
import { SystemStatusBar } from "./components/SystemStatusBar";
import { ChatWorkspace } from "./views/ChatWorkspace";
import PluginsArea from "./components/PluginsArea";
import ScorecardTerminal from "./views/ScorecardTerminal";
import type { AgentPublic, AgentRole, PluginManifest, SystemStatus } from "./types";

export default function App() {
  const [agents, setAgents] = useState<AgentPublic[]>([]);
  const [roles, setRoles] = useState<AgentRole[]>([]);
  const [selectedId, setSelectedId] = useState("hermes");
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [plugins, setPlugins] = useState<PluginManifest[]>([]);
  const [scoreLog, setScoreLog] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const selected = useMemo(
    () => agents.find((agent) => agent.id === selectedId) || null,
    [agents, selectedId],
  );

  const buildableRoles = useMemo(
    () => (roles.length ? roles.filter((role) => role !== "claw_opus") : undefined),
    [roles],
  );

  const refresh = useCallback(async () => {
    try {
      const [agentResp, statusResp, pluginResp] = await Promise.all([
        listAgents(),
        fetchSystemStatus(),
        fetchPlugins().catch(() => ({ plugins: [] as PluginManifest[] })),
      ]);
      setAgents(agentResp.agents || []);
      setRoles(agentResp.roles || []);
      setStatus(statusResp);
      setPlugins(pluginResp.plugins || []);
      setError("");
      setScoreLog((prev) => [
        ...prev.slice(-40),
        `[${new Date().toISOString()}] agents=${(agentResp.agents || []).length} claw=${statusResp?.claw?.listening}`,
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function onDelete(agentId: string) {
    setBusy(true);
    try {
      await deleteAgent(agentId);
      if (selectedId === agentId) setSelectedId("hermes");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onCreate(payload: {
    role: AgentRole;
    name?: string;
    tools: string[];
    plugins: string[];
  }) {
    setBusy(true);
    try {
      await createAgent(payload);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand">Hermes Studio Dash</div>
        <AgentPullDown agents={agents} selectedId={selectedId} onSelect={setSelectedId} />
        <AgentDelete agent={selected} agents={agents} onDelete={(id) => void onDelete(id)} busy={busy} />
        <button className="btn" type="button" onClick={() => void refresh()}>
          Refresh
        </button>
        {error ? <span className="pill bad">{error}</span> : null}
      </header>

      <div className="main-grid">
        <aside className="side">
          <AgentBuilder roles={buildableRoles} onCreate={(payload) => void onCreate(payload)} />
          <h2 className="panel-title">Plugins</h2>
          <PluginsArea plugins={plugins} />
        </aside>

        <main className="workspace">
          <ChatWorkspace
            selected={selected}
            onScore={(line) => setScoreLog((prev) => [...prev.slice(-80), line])}
          />
        </main>

        <aside className="scorecard">
          <h2 className="panel-title">Scorecard Terminal</h2>
          <ScorecardTerminal lines={scoreLog} status={status} />
        </aside>
      </div>

      <SystemStatusBar status={status} error={error || null} />
    </div>
  );
}
