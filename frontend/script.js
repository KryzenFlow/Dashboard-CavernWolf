/**
 * Hermes Studio Dashboard — static frontend
 * Connects to backend WebSocket + REST API (see backend/web_gateway)
 */

const API_BASE = window.HERMES_API_BASE || "http://localhost:8000";
const WS_URL = window.HERMES_WS_URL || "ws://localhost:8000/ws";

let ws = null;
let requestId = 0;
let sessionId = "web-1";
let streaming = false;
let selectedFile = null;
let studioConfig = { public: true, features: {} };

const $ = (id) => document.getElementById(id);

function setStatus(text, className = "") {
  const el = $("connection-status");
  el.textContent = text;
  el.className = `status ${className}`.trim();
}

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  $("chat-transcript").appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
}

function rpc(method, params = {}) {
  const id = `req-${++requestId}`;
  ws?.send(JSON.stringify({ jsonrpc: "2.0", id, method, params }));
  return id;
}

function connectWebSocket() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    setStatus("Connected", "connected");
    appendMessage("system", "Connected to Hermes gateway.");
    rpc("session.create", { session_key: sessionId });
  };

  ws.onmessage = (event) => {
    let msg;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    if (msg.method === "event") {
      const { type, payload } = msg.params || {};
      if (type === "message.delta" && payload?.text) {
        streaming = true;
        setStatus("Processing…", "active");
        const last = $("chat-transcript").lastElementChild;
        if (last?.classList.contains("assistant-stream")) {
          last.textContent += payload.text;
        } else {
          const div = document.createElement("div");
          div.className = "message assistant assistant-stream";
          div.textContent = payload.text;
          $("chat-transcript").appendChild(div);
        }
      }
      if (type === "message.complete") {
        streaming = false;
        setStatus("Connected", "connected");
        const last = $("chat-transcript").lastElementChild;
        if (last) last.classList.remove("assistant-stream");
      }
      return;
    }

    if (msg.result?.session_id) {
      sessionId = msg.result.session_id;
    }
    if (msg.result?.text) {
      appendMessage("assistant", msg.result.text);
    }
  };

  ws.onclose = () => {
    setStatus("Disconnected");
    appendMessage("system", "Disconnected. Retrying in 3s…");
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => setStatus("Connection error");
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadFiles() {
  try {
    const data = await api("/files?type=all");
    renderFileList("skills-list", data.files?.filter((f) => f.type === "skill") || [], "skill");
    renderFileList("memory-list", data.files?.filter((f) => f.type === "memory") || [], "memory");
  } catch (err) {
    console.error("loadFiles:", err);
  }
}

function renderFileList(listId, files, type) {
  const ul = $(listId);
  ul.innerHTML = "";
  files.forEach((file) => {
    const li = document.createElement("li");
    li.textContent = file.path;
    li.dataset.path = file.path;
    li.dataset.type = type;
    if (selectedFile?.path === file.path) li.classList.add("selected");
    li.addEventListener("click", () => selectFile(file));
    ul.appendChild(li);
  });
}

function selectFile(file) {
  selectedFile = file;
  $("editor-filename").textContent = file.path;
  $("code-editor").value = file.content || "";
  $("skill-editor").classList.remove("hidden");
  switchTab("skills");
  loadFiles();
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => {
    const active = t.dataset.tab === name;
    t.classList.toggle("active", active);
    t.setAttribute("aria-selected", active ? "true" : "false");
  });

  $("panel-chat").classList.toggle("hidden", name !== "chat");
  $("panel-projects").classList.toggle("hidden", name !== "projects");
  $("panel-memory").classList.toggle("hidden", name !== "memory");
  $("panel-git").classList.toggle("hidden", name !== "git");
  $("panel-skills").classList.toggle("hidden", name !== "skills");
}

async function loadGitStatus() {
  try {
    const data = await api("/git/status");
    $("git-status").textContent = data.status || "Clean working tree";
    const warn = $("git-warning");
    if (data.uncommitted > 0) {
      warn.textContent = `📝 ${data.uncommitted} uncommitted`;
      warn.classList.remove("hidden");
    } else {
      warn.classList.add("hidden");
    }
  } catch {
    $("git-status").textContent = "Git status unavailable (mock mode?)";
  }
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("chat-input");
  const text = input.value.trim();
  if (!text) return;

  appendMessage("user", text);
  input.value = "";

  if (text.toLowerCase().startsWith("/action ")) {
    try {
      const body = JSON.parse(text.slice(8));
      const result = await api("/action", { method: "POST", body: JSON.stringify(body) });
      appendMessage("assistant", JSON.stringify(result, null, 2));
    } catch (err) {
      appendMessage("system", `Action failed: ${err.message}`);
    }
    return;
  }

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    try {
      const result = await api("/reason", { method: "POST", body: JSON.stringify({ query: text }) });
      appendMessage("assistant", result.answer || JSON.stringify(result));
    } catch (err) {
      appendMessage("system", `Reason failed: ${err.message}`);
    }
    return;
  }

  rpc("message.send", { session_id: sessionId, text });
});

$("btn-save-skill").addEventListener("click", async () => {
  if (!selectedFile) return;
  try {
    const result = await api("/skill/save", {
      method: "POST",
      body: JSON.stringify({
        path: selectedFile.path,
        content: $("code-editor").value,
        language: selectedFile.language || "python",
      }),
    });
    appendMessage("system", result.success ? "✅ Skill saved" : `❌ ${result.error}`);
    loadFiles();
  } catch (err) {
    appendMessage("system", `Save failed: ${err.message}`);
  }
});

$("btn-test-skill").addEventListener("click", async () => {
  if (!selectedFile) return;
  try {
    const result = await api("/skill/test", {
      method: "POST",
      body: JSON.stringify({ path: selectedFile.path, code: $("code-editor").value }),
    });
    const el = $("test-results");
    el.classList.remove("hidden", "passed", "failed");
    el.classList.add(result.failed === 0 ? "passed" : "failed");
    el.textContent =
      result.failed === 0
        ? `✅ All ${result.passed} tests passed`
        : `❌ ${result.failed} failed, ${result.passed} passed`;
  } catch (err) {
    appendMessage("system", `Test failed: ${err.message}`);
  }
});

$("btn-improve-skill").addEventListener("click", () => {
  const code = $("code-editor").value;
  rpc("message.send", {
    session_id: sessionId,
    text: `Please review and improve this skill:\n\n\`\`\`python\n${code}\n\`\`\``,
  });
  switchTab("chat");
});

$("btn-new-skill").addEventListener("click", () => {
  const name = `skills/new_skill_${Date.now()}.py`;
  selectFile({
    path: name,
    type: "skill",
    language: "python",
    content: '"""New Hermes skill."""\n\ndef run(input_text: str) -> str:\n    return input_text\n',
  });
});

$("btn-git-commit").addEventListener("click", async () => {
  try {
    const result = await api("/git/commit", { method: "POST", body: JSON.stringify({ message: "Studio update" }) });
    appendMessage("system", result.success ? "Committed" : result.error);
    loadGitStatus();
  } catch (err) {
    appendMessage("system", err.message);
  }
});

$("btn-git-push").addEventListener("click", async () => {
  try {
    const result = await api("/git/push", { method: "POST", body: "{}" });
    appendMessage("system", result.success ? "Pushed to remote" : result.error);
  } catch (err) {
    appendMessage("system", err.message);
  }
});

async function loadStudioConfig() {
  try {
    studioConfig = await api("/studio/config");
    applyStudioConfig();
  } catch (err) {
    console.warn("studio config:", err);
  }
}

function applyStudioConfig() {
  const internal = !studioConfig.public;
  document.querySelectorAll('.tab[data-tab="memory"], .tab[data-tab="skills"], .tab[data-tab="git"]').forEach((tab) => {
    tab.classList.toggle("hidden", !internal);
  });
  const badge = $("studio-mode-badge");
  if (badge) {
    badge.textContent = internal ? "Internal" : "Public";
    badge.className = internal ? "mode-badge internal" : "mode-badge public";
  }
}

async function runCliCommand(command, args) {
  const name = $("project-name")?.value?.trim() || "mysite";
  const template = $("project-template")?.value || "static-site";
  const resolved = args.map((a) => a.replace(/\bmysite\b/g, name).replace(/static-site/g, template));
  setProjectOutput(`Running: hermes-cli ${command} ${resolved.join(" ")}\n`);
  try {
    const result = await api("/studio/cli/run", {
      method: "POST",
      body: JSON.stringify({ command, args: resolved }),
    });
    setProjectOutput(`Running: hermes-cli ${command} ${resolved.join(" ")}\n${result.output || JSON.stringify(result, null, 2)}`);
  } catch (err) {
    setProjectOutput(err.message);
  }
}

async function loadBleeds() {
  const project = $("project-name")?.value?.trim() || "mysite";
  try {
    const data = await api(`/studio/bleeds?project=${encodeURIComponent(project)}`);
    renderBleeds(data);
  } catch (err) {
    console.warn("bleeds:", err);
  }
}

function renderBleeds(data) {
  const sel = $("bleed-select");
  if (!sel || !data.bleeds) return;

  sel.innerHTML = "";
  data.bleeds.forEach((b) => {
    const opt = document.createElement("option");
    opt.value = b.id;
    opt.textContent = b.label;
    if (b.is_active) opt.selected = true;
    sel.appendChild(opt);
  });

  if (data.active) {
    const tpl = $("project-template");
    const prof = $("deploy-profile");
    if (tpl && data.active.template) tpl.value = data.active.template;
    if (prof && data.active.deploy_profile) prof.value = data.active.deploy_profile;

    const pitch = $("bleed-pitch");
    if (pitch) {
      if (data.active.pitch) {
        pitch.textContent = data.active.pitch;
        pitch.classList.remove("hidden");
      } else {
        pitch.classList.add("hidden");
      }
    }

    const pains = $("bleed-pain-points");
    if (pains) {
      pains.innerHTML = "";
      const points = data.active.pain_points || [];
      if (points.length) {
        pains.classList.remove("hidden");
        points.forEach((p) => {
          const li = document.createElement("li");
          li.textContent = p;
          pains.appendChild(li);
        });
      } else {
        pains.classList.add("hidden");
      }
    }
  }

  renderQuickActions(data.quick_actions || []);
}

function renderQuickActions(actions) {
  const wrap = $("quick-actions-buttons");
  if (!wrap) return;
  wrap.innerHTML = "";
  actions.forEach((action) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-action";
    btn.textContent = action.label;
    btn.addEventListener("click", () => runCliCommand(action.command, action.args));
    wrap.appendChild(btn);
  });
}

$("bleed-select")?.addEventListener("change", async () => {
  const bleedId = $("bleed-select").value;
  const project = $("project-name")?.value?.trim() || "mysite";
  try {
    const data = await api("/studio/bleed/select", {
      method: "POST",
      body: JSON.stringify({ bleed_id: bleedId, project }),
    });
    renderBleeds(data);
  } catch (err) {
    setProjectOutput(err.message);
  }
});

$("project-name")?.addEventListener("change", () => loadBleeds());

function setProjectOutput(text) {
  const el = $("project-output");
  if (el) el.textContent = typeof text === "string" ? text : JSON.stringify(text, null, 2);
}

$("btn-new-website")?.addEventListener("click", async () => {
  const name = $("project-name").value.trim() || "mysite";
  const template = $("project-template").value;
  setProjectOutput("Scaffolding…");
  try {
    const result = await api("/studio/new-website", {
      method: "POST",
      body: JSON.stringify({ template, name }),
    });
    setProjectOutput(result);
    appendMessage("system", `Website scaffolded: ${name}`);
  } catch (err) {
    setProjectOutput(err.message);
  }
});

$("btn-deploy-profile")?.addEventListener("click", async () => {
  const project = $("project-name").value.trim() || "mysite";
  const template = $("project-template").value;
  const profile = $("deploy-profile").value;
  setProjectOutput(`Deploying with profile: ${profile}…`);
  try {
    const result = await api("/studio/deploy", {
      method: "POST",
      body: JSON.stringify({ profile, project, template }),
    });
    setProjectOutput(result);
  } catch (err) {
    setProjectOutput(err.message);
  }
});

async function loadDeployProfiles() {
  try {
    const data = await api("/studio/profiles");
    const sel = $("deploy-profile");
    if (!sel || !data.profiles?.length) return;
    sel.innerHTML = "";
    data.profiles.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.ready ? p.label : `${p.label} (needs ${p.missing_env.join(", ")})`;
      if (p.is_default) opt.selected = true;
      sel.appendChild(opt);
    });
  } catch {
    /* keep static options */
  }
}

connectWebSocket();
loadStudioConfig();
loadBleeds();
loadFiles();
loadGitStatus();
loadDeployProfiles();
setInterval(loadFiles, 5000);
