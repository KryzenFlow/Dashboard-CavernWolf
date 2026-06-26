const API = window.OPS_API_BASE || "http://localhost:8000";

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function $(id) {
  return document.getElementById(id);
}

async function loadBleeds() {
  const data = await api("/ops/bleeds");
  const sel = $("ops-bleed");
  sel.innerHTML = "";
  data.bleeds.forEach((b) => {
    const opt = document.createElement("option");
    opt.value = b.id;
    opt.textContent = b.label;
    if (b.is_active) opt.selected = true;
    sel.appendChild(opt);
  });
  renderActive(data.active);
}

function renderActive(active) {
  $("ops-description").textContent = active.description || active.pitch || "";
  const pains = $("ops-pains");
  pains.innerHTML = "";
  (active.pain_points || []).forEach((p) => {
    const li = document.createElement("li");
    li.textContent = p;
    pains.appendChild(li);
  });
}

$("ops-bleed").addEventListener("change", async () => {
  const data = await api("/ops/bleed/select", {
    method: "POST",
    body: JSON.stringify({ bleed_id: $("ops-bleed").value }),
  });
  renderActive(data.active);
});

$("btn-seo").addEventListener("click", async () => {
  $("ops-seo-output").textContent = "Generating…";
  try {
    const mapRaw = $("ops-map").value.trim();
    let map;
    try {
      map = JSON.parse(mapRaw);
    } catch {
      map = mapRaw;
    }
    const result = await api("/ops/seo", {
      method: "POST",
      body: JSON.stringify({ zip: $("ops-zip").value.trim(), map }),
    });
    $("ops-seo-output").textContent = result.output || JSON.stringify(result, null, 2);
    loadJobs();
  } catch (err) {
    $("ops-seo-output").textContent = err.message;
  }
});

async function loadJobs() {
  const data = await api("/ops/jobs");
  const ul = $("ops-jobs");
  ul.innerHTML = "";
  (data.jobs || []).forEach((j) => {
    const li = document.createElement("li");
    li.textContent = `#${j.id} ${j.bleed_id} ${j.zip_code || ""} — ${j.status} (${j.job_type})`;
    ul.appendChild(li);
  });
}

$("btn-refresh-jobs").addEventListener("click", loadJobs);

loadBleeds()
  .then(() => {
    $("ops-status").textContent = "Connected";
    return loadJobs();
  })
  .catch((err) => {
    $("ops-status").textContent = "Error — set STUDIO_MODE=internal on backend";
    console.error(err);
  });
