# Agent Stack Integration Specs

These 31 files document the multi-agent architecture for Dashboard-CavernWolf.
They cover backend services, frontend UI components, and infrastructure.

## Backend (Python/FastAPI)

| File | Topic |
|------|-------|
| agents_stack_..._1782506928683.docx | **Master merge plan** - Multi-agent Python stack merge into Dashboard-CavernWolf, unified docker-compose, UI design for agent management |
| agents_stack_..._1782507033963.docx | **FastAPI backend** - Complete runnable FastAPI with agent registry, hot-reload, CRUD endpoints |
| agents_stack_..._1782507039511.txt | **WebSocket backend** - Streaming chat, real-time logs, xterm.js terminal access |
| agents_stack_..._1782507163725.docx | **Terminal design** - xterm.js terminal, prompt chat interface, split view chat+logs |
| agents_stack_..._1782507166797.txt | **Terminal UX** - Full xterm.js design, prompt chat, split view for ops |
| agents_stack_..._1782507287889.txt | **Agent chaining + memory** - Workflow runner, Qdrant vector DB, Redis, LLaMA streaming |
| agents_stack_..._1782507294657.docx | **LLaMA + persistent memory** - Agent chaining, Qdrant/Redis integration, streaming chat |
| agents_stack_..._1782507455361.docx | **React frontend** - WorkflowBuilder (React Flow), ChatWithLogs, TerminalView components |
| agents_stack_..._1782507580512.docx | **Frontend integration** - React Flow workflow builder, WebSocket chat+logs, xterm.js |
| agents_stack_..._1782508479090.txt | **Agent Hub UI** - React AgentHub, AgentCard, AgentWizard, AgentConfigEditor, YAML editor |
| agents_stack_..._1782508979542.docx | **Auto-run enforcement** - Backend auto-run on boot, bulk toggle, audit logging |
| agents_stack_..._1782508984023.txt | **Auto-run UI** - Color-coded toggles, bulk buttons, Wizard + Editor integration |
| agents_stack_..._1782509038155.docx | **Auto-run complete** - Wizard Step 3, YAML editor, auto_run field round-trips |
| agents_stack_..._1782509048343.txt | **Auto-run schema** - auto_run field in AgentConfig, Wizard Step 3, YAML editor |
| agents_stack_..._1782509207677.docx | **Auto-run delay** - auto_run_delay field, staggered startup, UI numeric input |
| agents_stack_..._1782509345200.docx | **Auto-run delay backend** - Startup event with delay, threading, YAML config |
| agents_stack_..._1782509681906.docx | **Startup groups** - Gold-tier orchestration, startup_group field, token cost playbook |
| agents_stack_..._1782509687100.txt | **Token cost control** - Prompt compression, max_tokens, model routing, Redis cache, streaming cutoff |
| agents_stack_..._1782509975496.docx | **LLaMA optimized agent** - Qdrant retrieval, history compression, model routing, token caps |
| agents_stack_..._1782510104963.docx | **Cost-control UI** - Wizard Step 2 conditional fields for llama-optimized agents |
| agents_stack_..._1782510329008.docx | **Cost-control UI v2** - Same as above (duplicate), YAML editor tip for llama-optimized |
| agents_stack_..._1782510431494.docx | **Publishing checklist** - Color-coded toggle, bulk buttons, cost-control fields before release |
| agents_stack_..._1782510675565.docx | **Merged AgentHub.jsx** - Final combined component with color-coded toggle, bulk buttons |
| agents_stack_..._1782511093289.docx | **Docker compose override** - Full dev compose with backend, frontend, Qdrant, Redis, models |

## Early/Foundational (older timestamps)

| File | Topic |
|------|-------|
| agents_stack_..._1782481859509.txt | Early multi-agent stack design |
| agents_stack_..._1782485471587.txt | Agent registry + hot-reload design |
| agents_stack_..._1782486132133.txt | Agent lifecycle management |
| agents_stack_..._1782487332890.txt | Memory system design |
| agents_stack_..._1782488438288.txt | Orchestration pipeline |
| agents_stack_..._1782490039779.txt | Tool adapter agents |
| agents_stack_..._1782490044977.docx | Tool integration patterns |
| agents_stack_..._1782495000398.txt | Deployment + Docker setup |

## Summary

**Key components to merge into Dashboard-CavernWolf:**
1. Backend: Agent registry with hot-reload, auto-run, startup groups, workflow runner
2. Memory: Qdrant (vector DB) + Redis (cache) integration
3. LLaMA: Optimized agent with token cost control, model routing, prompt compression
4. Frontend: AgentHub (cards + wizard + YAML editor), WorkflowBuilder (React Flow), ChatWithLogs, TerminalView
5. Infrastructure: Docker compose with all services, WebSocket streaming

**Priority merge order:**
1. Backend agent registry + auto-run (foundation)
2. Memory system (Qdrant + Redis)
3. LLaMA optimized agent
4. Frontend AgentHub
5. WebSocket streaming + terminal
