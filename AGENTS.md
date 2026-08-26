# AGENTS.md — Cloud & IDE Agent Onboarding

Every agent working in this repository must load root context before any task.

## Initialization order

1. Read **`soul.md`** — Trust Discipline Framework (constitution)
2. Read **`CI.md`** — Cognitive Interface (session lifecycle + behavioral rules)
3. Read **`.cursorrules`** — repository-specific operating instructions

## Non-negotiable

- soul.md is loaded **first** and governs all other instructions.
- CI.md never overrides soul.md — surface conflicts, do not resolve silently.
- Follow-through is auditable: use `app/security/merkle.py` for session audit trails.

## Quick reference

| Document | Question it answers |
|----------|---------------------|
| `soul.md` | What kind of system are we trying to be, and why? |
| `CI.md` | How does this system think, respond, escalate, and learn? |
| `app/security/merkle.py` | How is follow-through logged and verified? |

## Trust stages

Most work stays at **Stage 1 (Rule-Based)** — explicit rules, defined constraints.
Advance to Stage 2/3 only with demonstrated follow-through under audit.
