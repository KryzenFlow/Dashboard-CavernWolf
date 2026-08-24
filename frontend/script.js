/**
 * Hermes Studio Dashboard — static frontend
 * Connects to backend WebSocket + REST API (see backend/web_gateway)
 */

const API_BASE = window.HERMES_API_BASE || (location.port === "3000" ? "http://127.0.0.1:8000" : "");
const WS_URL =
  window.HERMES_WS_URL ||
  (API_BASE
    ? API_BASE.replace(/^http/, "ws") + "/ws"
    : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);

let ws = null;
let requestId = 0;
let sessionId = "web-1";
let lifecycleToken = null;
let didInitAfterAuth = false;
let loadFilesIntervalId = null;
let streaming = false;
let selectedFile = null;

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
    appendMessage("system", "Connected to Hermes. Agent: Claw Opus.");
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
      if (type === "error" && payload?.text) {
        appendMessage("system", payload.text);
        streaming = false;
        setStatus("Connected", "connected");
        return;
      }
      if (type === "message.complete") {
        streaming = false;
        setStatus("Connected", "connected");
        const last = $("chat-transcript").lastElementChild;
        if (last) last.classList.remove("assistant-stream");
      }
      return;
    }

    if (msg.result?.session_id) sessionId = msg.result.session_id;
    if (msg.result?.lifecycle_token && !didInitAfterAuth) {
      lifecycleToken = msg.result.lifecycle_token;
      didInitAfterAuth = true;
      loadFiles();
      loadGitStatus();
      // Polling skills list makes the editor feel alive.
      if (loadFilesIntervalId) clearInterval(loadFilesIntervalId);
      loadFilesIntervalId = setInterval(loadFiles, 5000);
    }
    if (msg.result?.text) {
      appendMessage("assistant", msg.result.text);
    }
  };

  ws.onclose = () => {
    setStatus("Disconnected");
    appendMessage("system", "Disconnected. Retrying in 3s…");
    lifecycleToken = null;
    didInitAfterAuth = false;
    if (loadFilesIntervalId) clearInterval(loadFilesIntervalId);
    loadFilesIntervalId = null;
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => setStatus("Connection error");
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (lifecycleToken) headers["X-Lifecycle-Token"] = JSON.stringify(lifecycleToken);
  const res = await fetch(`${API_BASE}${path}`, {
    headers,
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
    $("git-status").textContent = "Git status unavailable";
  }
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

$("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("chat-input");
  const text = input.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN || !lifecycleToken) return;
  appendMessage("user", text);
  rpc("message.send", { session_id: sessionId, text, lifecycle_token: lifecycleToken });
  input.value = "";
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
    lifecycle_token: lifecycleToken,
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

connectWebSocket();
