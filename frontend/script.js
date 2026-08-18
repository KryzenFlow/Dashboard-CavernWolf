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
  $("panel-search").classList.toggle("hidden", name !== "search");
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

$("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("chat-input");
  const text = input.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
  appendMessage("user", text);
  rpc("message.send", { session_id: sessionId, text });
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

function showSearchError(message) {
  const el = $("search-error");
  el.textContent = message;
  el.classList.remove("hidden");
}

function hideSearchError() {
  $("search-error").classList.add("hidden");
  $("search-error").textContent = "";
}

function renderSearchResults(data) {
  const container = $("search-results");
  container.innerHTML = "";
  const items = data.grounding?.generic || [];
  if (!items.length) {
    container.innerHTML = '<p class="search-empty">No grounding snippets returned.</p>';
    return;
  }

  const meta = document.createElement("p");
  meta.className = "search-meta";
  meta.textContent = `${data.result_count} source${data.result_count === 1 ? "" : "s"} from Brave LLM Context`;
  container.appendChild(meta);

  items.forEach((item) => {
    const article = document.createElement("article");
    article.className = "search-card";

    const heading = document.createElement("h3");
    const link = document.createElement("a");
    link.href = item.url || "#";
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = item.title || item.url || "Untitled";
    heading.appendChild(link);

    const urlLine = document.createElement("p");
    urlLine.className = "search-url";
    urlLine.textContent = item.url || "";

    const snippets = document.createElement("div");
    snippets.className = "search-snippets";
    (item.snippets || []).forEach((snippet) => {
      const p = document.createElement("p");
      p.textContent = snippet;
      snippets.appendChild(p);
    });

    article.appendChild(heading);
    article.appendChild(urlLine);
    article.appendChild(snippets);
    container.appendChild(article);
  });

  if (data.context) {
    const actions = document.createElement("div");
    actions.className = "search-actions";
    const sendBtn = document.createElement("button");
    sendBtn.type = "button";
    sendBtn.className = "btn-action";
    sendBtn.textContent = "Send context to chat";
    sendBtn.addEventListener("click", () => {
      const query = $("search-query").value.trim();
      const text = `Use this Brave Search LLM context to answer: ${query}\n\n${data.context}`;
      appendMessage("user", `Grounded search: ${query}`);
      rpc("message.send", { session_id: sessionId, text });
      switchTab("chat");
    });
    actions.appendChild(sendBtn);
    container.appendChild(actions);
  }
}

async function loadSearchStatus() {
  const el = $("search-status");
  try {
    const data = await api("/search/status");
    if (data.configured) {
      el.textContent = "Brave Search is configured. Queries use /res/v1/llm/context.";
      el.classList.remove("warning");
    } else {
      el.textContent =
        "Set BRAVE_SEARCH_API_KEY on the backend to enable Brave LLM Context search.";
      el.classList.add("warning");
    }
  } catch {
    el.textContent = "Search API unavailable. Is the backend running?";
    el.classList.add("warning");
  }
}

$("search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = $("search-query").value.trim();
  if (!query) return;
  hideSearchError();
  const btn = $("btn-search");
  btn.disabled = true;
  $("search-results").innerHTML = '<p class="search-empty">Searching…</p>';
  try {
    const params = new URLSearchParams({ q: query, count: "20" });
    const data = await api(`/search/llm-context?${params.toString()}`);
    renderSearchResults(data);
  } catch (err) {
    $("search-results").innerHTML = "";
    let message = err.message || "Search failed";
    try {
      const parsed = JSON.parse(message);
      if (typeof parsed.detail === "string") {
        message = parsed.detail;
      } else if (parsed.detail?.error) {
        message = parsed.detail.error;
      }
    } catch {
      const match = message.match(/"error"\s*:\s*"([^"]+)"/);
      if (match) message = match[1];
    }
    showSearchError(message);
  } finally {
    btn.disabled = false;
  }
});

connectWebSocket();
loadFiles();
loadGitStatus();
loadSearchStatus();
setInterval(loadFiles, 5000);
