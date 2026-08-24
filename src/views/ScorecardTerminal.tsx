import type { SystemStatus } from "../types";

type Props = {
  lines: string[];
  status: SystemStatus | null;
};

export default function ScorecardTerminal({ lines, status }: Props) {
  const header = [
    "=== Hermes Studio Scorecard ===",
    `claw.listening=${status?.claw.listening ?? "n/a"}`,
    `merkle=${status?.merkle_root || "n/a"}`,
    `agents=${status?.agents_count ?? "n/a"}`,
    "--------------------------------",
  ].join("\n");
  const body = lines.length ? lines.join("\n") : "(awaiting events)";
  return <pre className="term">{`${header}\n${body}`}</pre>;
}
