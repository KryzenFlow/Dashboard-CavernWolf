import type { AgentPublic, AgentRole, PluginManifest, SystemStatus } from "./types";

export const API_BASE = (import.meta.env.VITE_HERMES_API || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  let body: Record<string, unknown> = {};
  try {
    body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
  } catch {
    body = { raw: text };
  }
  if (!response.ok) {
    const detail = body.detail ?? body.error ?? text ?? response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body as T;
}

export function listAgents() {
  return request<{ agents: AgentPublic[]; roles: AgentRole[] }>("/agents");
}

export function createAgent(payload: {
  role: AgentRole;
  name?: string;
  tools?: string[];
  plugins?: string[];
}) {
  return request<{ agent: AgentPublic }>("/agents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteAgent(id: string) {
  return request<{ deleted: boolean; id: string }>(`/agents/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export function routeAgent(id: string, task: string) {
  return request<{ agent_id: string; result: Record<string, unknown>; plan: Record<string, unknown> }>(
    `/agents/${encodeURIComponent(id)}/route`,
    {
      method: "POST",
      body: JSON.stringify({ task, message: task }),
    },
  );
}

export function fetchSystemStatus() {
  return request<SystemStatus>("/system/status");
}

export function fetchPlugins() {
  return request<{ plugins: PluginManifest[] }>("/plugins");
}
