import type { AgentPublic } from "../types";

type Props = {
  agents: AgentPublic[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  disabled?: boolean;
};

export function AgentPullDown({ agents, selectedId, onSelect, disabled }: Props) {
  return (
    <label className="agent-pulldown">
      <span className="pill">Talk to</span>
      <select
        value={selectedId ?? ""}
        disabled={disabled || agents.length === 0}
        onChange={(event) => onSelect(event.target.value)}
        aria-label="Agent selector"
      >
        {agents.length === 0 ? <option value="">No agents loaded</option> : null}
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name} ({agent.role})
            {agent.executes ? " · executor" : ""}
          </option>
        ))}
      </select>
    </label>
  );
}

export default AgentPullDown;
