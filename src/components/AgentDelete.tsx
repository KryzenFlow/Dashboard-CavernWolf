import type { AgentPublic, AgentRole } from "../types";

type Props = {
  agent: AgentPublic | null;
  agents: AgentPublic[];
  onDelete: (id: string) => void;
  busy?: boolean;
};

function isLastProtected(agent: AgentPublic, agents: AgentPublic[]): boolean {
  const role: AgentRole = agent.role;
  switch (role) {
    case "hermes":
      return agents.filter((item) => item.role === "hermes").length <= 1;
    case "claw_opus":
      return agents.filter((item) => item.role === "claw_opus").length <= 1;
    case "reasoning_analytical":
    case "reasoning_rapid":
    case "memory_ephemeral":
    case "memory_semantic":
    case "codex":
    case "grok":
    case "deepseek_architect":
      return false;
    default: {
      const unused: never = role;
      throw new Error(`unhandled agent role: ${unused}`);
    }
  }
}

export function AgentDelete({ agent, agents, onDelete, busy }: Props) {
  const locked = !agent || isLastProtected(agent, agents);
  const title = !agent
    ? "Select an agent"
    : locked
      ? "API refuses deleting the last Hermes or Claw Opus instance"
      : `Delete ${agent.name}`;

  return (
    <button
      type="button"
      className="btn danger agent-delete"
      disabled={busy || locked}
      title={title}
      onClick={() => {
        if (!agent || locked) return;
        if (window.confirm(`Delete agent ${agent.name}?`)) {
          onDelete(agent.id);
        }
      }}
    >
      Delete agent
    </button>
  );
}

export default AgentDelete;
