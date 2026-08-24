export type AgentRole =
  | "hermes"
  | "reasoning_analytical"
  | "reasoning_rapid"
  | "memory_ephemeral"
  | "memory_semantic"
  | "codex"
  | "grok"
  | "deepseek_architect"
  | "claw_opus";

export type AgentPublic = {
  id: string;
  role: AgentRole;
  name: string;
  style: string;
  model?: string;
  tools: string[];
  plugins: string[];
  status: string;
  executes: boolean;
  description?: string;
};

export type SystemStatus = {
  agents: Array<{ id: string; name: string; role: AgentRole; status: string }>;
  agents_count: number;
  ports: { hermes: number; claw: number; studio_vite?: number };
  containers: string[];
  tailscale_ip: string | null;
  bind: string;
  claw_url: string;
  claw: { listening: boolean; halted: boolean | null };
  hermes: { ready: boolean };
  memory: { redis: boolean; vector: boolean };
  merkle_root?: string | null;
};

export type PluginManifest = {
  id: string;
  name: string;
  version?: string;
  description?: string;
  tools?: string[];
};

export type AgentsApi = {
  list: () => Promise<{ agents: AgentPublic[]; roles: AgentRole[] }>;
  create: (body: {
    role: AgentRole;
    name?: string;
    tools?: string[];
    plugins?: string[];
  }) => Promise<{ agent: AgentPublic }>;
  delete: (id: string) => Promise<{ deleted: boolean; id: string }>;
  route: (
    id: string,
    body: { task: string; context?: Record<string, unknown> },
  ) => Promise<{
    agent_id: string;
    result: {
      ok: boolean;
      kind: string;
      payload: unknown;
      route_to_claw: boolean;
      error: string | null;
    };
  }>;
  status: () => Promise<SystemStatus>;
};
