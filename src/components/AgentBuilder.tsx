import { useState } from "react";
import type { AgentRole } from "../types";

const BUILDABLE_ROLES: AgentRole[] = [
  "hermes",
  "reasoning_analytical",
  "reasoning_rapid",
  "memory_ephemeral",
  "memory_semantic",
  "codex",
  "grok",
  "deepseek_architect",
];

type Props = {
  roles?: AgentRole[];
  onCreate: (body: {
    role: AgentRole;
    name?: string;
    tools: string[];
    plugins: string[];
  }) => void;
};

export function AgentBuilder({ roles = BUILDABLE_ROLES, onCreate }: Props) {
  const [role, setRole] = useState<AgentRole>("codex");
  const [name, setName] = useState("");
  const [tools, setTools] = useState("");
  const [plugins, setPlugins] = useState("");

  return (
    <form
      className="agent-builder"
      onSubmit={(event) => {
        event.preventDefault();
        onCreate({
          role,
          name: name.trim() || undefined,
          tools: tools.split(",").map((s) => s.trim()).filter(Boolean),
          plugins: plugins.split(",").map((s) => s.trim()).filter(Boolean),
        });
      }}
    >
      <h2>Agent Builder</h2>
      <p>Assign tools/plugins. Specialists propose; only Hermes routes to Claw Opus.</p>
      <label>
        Role
        <select value={role} onChange={(e) => setRole(e.target.value as AgentRole)}>
          {roles.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </label>
      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="optional" />
      </label>
      <label>
        Tools
        <input value={tools} onChange={(e) => setTools(e.target.value)} placeholder="comma-separated" />
      </label>
      <label>
        Plugins
        <input value={plugins} onChange={(e) => setPlugins(e.target.value)} placeholder="comma-separated" />
      </label>
      <button type="submit">Create agent</button>
    </form>
  );
}
