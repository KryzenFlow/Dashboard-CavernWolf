/**
 * Frankie's Wall — local-only personal music player.
 * Plays user-selected local audio only. No streaming, no cloud upload.
 */

(() => {
  "use strict";

  const STORAGE_KEY = "frankiesWallLibrary";

  const PRESETS = {
    bands: [
      "Bush",
      "Soundgarden",
      "Radiohead",
      "Collective Soul",
      "Skynyrd",
      "Guns N' Roses",
      "Pearl Jam",
      "Alice in Chains",
      "Nirvana",
      "Stone Temple Pilots",
    ],
    places: ["Toledo", "Promenade Park", "Frankies", "East Side Nights"],
    people: ["Mom", "Son", "Solo", "With Friends"],
    instruments: ["sax", "electric", "bass", "drums", "vocals", "acoustic"],
    vibes: ["Mom's Smile", "River Breeze", "fight & focus", "late night", "practice"],
  };

  const WALL_DATES = {
    Bush: "'95",
    Soundgarden: "'94",
    Radiohead: "'97",
    "Collective Soul": "'94",
    Skynyrd: "'77",
    "Guns N' Roses": "'91",
    "Pearl Jam": "'91",
    "Alice in Chains": "'92",
    Nirvana: "'91",
    "Stone Temple Pilots": "'92",
    Toledo: "home",
    "Promenade Park": "summer",
    Frankies: "nights",
    "East Side Nights": "forever",
    Mom: "♡",
    Son: "growin'",
    Solo: "alone",
    "With Friends": "crew",
  };

  /** @type {{ tracks: TrackMeta[] }} */
  let library = { tracks: [] };

  /** @type {Map<string, string>} id -> object URL */
  const blobUrls = new Map();

  /** @type {Map<string, File>} id -> File (session) */
  const sessionFiles = new Map();

  /** @type {string | null} */
  let currentId = null;

  /** @type {{ kind: string, value: string } | null} */
  let activeFilter = null;

  /** @type {'library' | 'wall' | 'moms-smile'} */
  let currentView = "library";

  let seeking = false;

  /**
   * @typedef {object} TrackMeta
   * @property {string} id
   * @property {string} title
   * @property {string} fileName
   * @property {string} mimeType
   * @property {number} size
   * @property {string[]} bands
   * @property {string[]} places
   * @property {string[]} people
   * @property {string[]} instruments
   * @property {string[]} vibes
   * @property {string} notes
   * @property {string | null} coverDataUrl
   * @property {number} addedAt
   */

  const el = {
    bandTags: document.getElementById("band-tags"),
    placeTags: document.getElementById("place-tags"),
    peopleTags: document.getElementById("people-tags"),
    instrumentTags: document.getElementById("instrument-tags"),
    vibeTags: document.getElementById("vibe-tags"),
    btnImportFiles: document.getElementById("btn-import-files"),
    btnImportFolder: document.getElementById("btn-import-folder"),
    fileInput: document.getElementById("file-input"),
    folderInput: document.getElementById("folder-input"),
    trackList: document.getElementById("track-list"),
    libraryEmpty: document.getElementById("library-empty"),
    libraryHeading: document.getElementById("library-heading"),
    btnClearFilter: document.getElementById("btn-clear-filter"),
    viewLibrary: document.getElementById("view-library"),
    viewWall: document.getElementById("view-wall"),
    graffitiGrid: document.getElementById("graffiti-grid"),
    viewEdit: document.getElementById("view-edit"),
    tagForm: document.getElementById("tag-form"),
    editId: document.getElementById("edit-id"),
    editTitle: document.getElementById("edit-title"),
    editNotes: document.getElementById("edit-notes"),
    editBands: document.getElementById("edit-bands"),
    editPlaces: document.getElementById("edit-places"),
    editPeople: document.getElementById("edit-people"),
    editInstruments: document.getElementById("edit-instruments"),
    editVibes: document.getElementById("edit-vibes"),
    editCover: document.getElementById("edit-cover"),
    btnCloseEdit: document.getElementById("btn-close-edit"),
    btnRemoveTrack: document.getElementById("btn-remove-track"),
    coverArt: document.getElementById("cover-art"),
    coverFallback: document.getElementById("cover-fallback"),
    nowTitle: document.getElementById("now-title"),
    nowNote: document.getElementById("now-note"),
    nowTags: document.getElementById("now-tags"),
    btnPrev: document.getElementById("btn-prev"),
    btnPlay: document.getElementById("btn-play"),
    btnNext: document.getElementById("btn-next"),
    seek: document.getElementById("seek"),
    timeCurrent: document.getElementById("time-current"),
    timeDuration: document.getElementById("time-duration"),
    audio: document.getElementById("audio"),
  };

  function uid() {
    return `t_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function titleFromFileName(name) {
    return name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim() || name;
  }

  function isAudioFile(file) {
    if (file.type && file.type.startsWith("audio/")) return true;
    return /\.(mp3|wav|ogg|m4a|aac|flac|opus|webm)$/i.test(file.name);
  }

  function formatTime(sec) {
    if (!Number.isFinite(sec) || sec < 0) return "0:00";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  }

  async function loadLibrary() {
    try {
      const data = await chrome.storage.local.get(STORAGE_KEY);
      const stored = data[STORAGE_KEY];
      if (stored && Array.isArray(stored.tracks)) {
        library = { tracks: stored.tracks };
      }
    } catch {
      library = { tracks: [] };
    }
  }

  async function saveLibrary() {
    const payload = {
      tracks: library.tracks.map((t) => ({
        id: t.id,
        title: t.title,
        fileName: t.fileName,
        mimeType: t.mimeType,
        size: t.size,
        bands: t.bands,
        places: t.places,
        people: t.people,
        instruments: t.instruments,
        vibes: t.vibes,
        notes: t.notes,
        coverDataUrl: t.coverDataUrl,
        addedAt: t.addedAt,
      })),
    };
    await chrome.storage.local.set({ [STORAGE_KEY]: payload });
  }

  function revokeUrl(id) {
    const url = blobUrls.get(id);
    if (url) {
      URL.revokeObjectURL(url);
      blobUrls.delete(id);
    }
  }

  function ensureBlobUrl(id) {
    if (blobUrls.has(id)) return blobUrls.get(id);
    const file = sessionFiles.get(id);
    if (!file) return null;
    const url = URL.createObjectURL(file);
    blobUrls.set(id, url);
    return url;
  }

  /**
   * @param {File[]} files
   */
  async function importFiles(files) {
    const audioFiles = files.filter(isAudioFile);
    if (!audioFiles.length) {
      el.nowNote.textContent = "No audio files found in that selection.";
      return;
    }

    for (const file of audioFiles) {
      const id = uid();
      /** @type {TrackMeta} */
      const meta = {
        id,
        title: titleFromFileName(file.name),
        fileName: file.name,
        mimeType: file.type || "audio/*",
        size: file.size,
        bands: [],
        places: [],
        people: [],
        instruments: [],
        vibes: [],
        notes: "",
        coverDataUrl: null,
        addedAt: Date.now(),
      };
      library.tracks.unshift(meta);
      sessionFiles.set(id, file);
      ensureBlobUrl(id);
    }

    await saveLibrary();
    renderAll();
    el.nowNote.textContent = `Imported ${audioFiles.length} local track${audioFiles.length === 1 ? "" : "s"}. Tag them on the wall.`;
  }

  function filteredTracks() {
    let tracks = library.tracks.slice();

    if (currentView === "moms-smile") {
      tracks = tracks.filter(
        (t) =>
          t.vibes.includes("Mom's Smile") ||
          t.people.includes("Mom") ||
          t.instruments.includes("sax")
      );
    }

    if (activeFilter) {
      const { kind, value } = activeFilter;
      tracks = tracks.filter((t) => {
        switch (kind) {
          case "bands":
            return t.bands.includes(value);
          case "places":
            return t.places.includes(value);
          case "people":
            return t.people.includes(value);
          case "instruments":
            return t.instruments.includes(value);
          case "vibes":
            return t.vibes.includes(value);
          default: {
            const _exhaustive = kind;
            void _exhaustive;
            return true;
          }
        }
      });
    }

    return tracks;
  }

  function renderSidebarTags() {
    /**
     * @param {HTMLElement | null} container
     * @param {string[]} names
     * @param {string} kind
     */
    function fill(container, names, kind) {
      if (!container) return;
      container.innerHTML = "";
      names.forEach((name, i) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = name;
        btn.dataset.kind = kind;
        btn.dataset.value = name;
        if (activeFilter?.kind === kind && activeFilter.value === name) {
          btn.classList.add("is-active");
        }
        btn.style.setProperty("--tilt", `${((i % 5) - 2) * 0.8}deg`);
        btn.addEventListener("click", () => {
          if (activeFilter?.kind === kind && activeFilter.value === name) {
            activeFilter = null;
          } else {
            activeFilter = { kind, value: name };
            if (currentView === "wall") setView("library");
          }
          renderAll();
        });
        li.appendChild(btn);
        container.appendChild(li);
      });
    }

    fill(el.bandTags, PRESETS.bands, "bands");
    fill(el.placeTags, PRESETS.places, "places");
    fill(el.peopleTags, PRESETS.people, "people");
    fill(el.instrumentTags, PRESETS.instruments, "instruments");
    fill(el.vibeTags, PRESETS.vibes, "vibes");
  }

  function renderLibrary() {
    const tracks = filteredTracks();
    el.trackList.innerHTML = "";
    el.libraryEmpty.hidden = tracks.length > 0;

    if (currentView === "moms-smile") {
      el.libraryHeading.textContent = "Mom's Smile";
    } else if (activeFilter) {
      el.libraryHeading.textContent = activeFilter.value;
    } else {
      el.libraryHeading.textContent = "Library";
    }

    el.btnClearFilter.hidden = !activeFilter;

    for (const track of tracks) {
      const li = document.createElement("li");
      li.className = "track-item" + (track.id === currentId ? " is-playing" : "");
      li.dataset.id = track.id;

      const main = document.createElement("div");
      const name = document.createElement("p");
      name.className = "track-name";
      name.textContent = track.title;
      const meta = document.createElement("p");
      meta.className = "track-meta";
      const bits = [
        ...track.bands,
        ...track.instruments,
        ...track.vibes.slice(0, 1),
      ];
      const needsFile = !sessionFiles.has(track.id);
      meta.textContent = bits.length
        ? bits.join(" · ") + (needsFile ? " · re-import file to play" : "")
        : needsFile
          ? "tags empty · re-import file to play"
          : track.fileName;

      main.appendChild(name);
      main.appendChild(meta);

      const actions = document.createElement("div");
      actions.className = "track-actions";
      const tagBtn = document.createElement("button");
      tagBtn.type = "button";
      tagBtn.className = "btn tiny ghost";
      tagBtn.textContent = "Tag";
      tagBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        openEdit(track.id);
      });
      actions.appendChild(tagBtn);

      li.appendChild(main);
      li.appendChild(actions);
      li.addEventListener("click", () => playTrack(track.id));
      el.trackList.appendChild(li);
    }
  }

  function renderGraffiti() {
    el.graffitiGrid.innerHTML = "";
    const tiles = [
      ...PRESETS.bands.map((n) => ({ name: n, kind: "bands", type: "band" })),
      ...PRESETS.places.map((n) => ({ name: n, kind: "places", type: "place" })),
      ...PRESETS.people.map((n) => ({ name: n, kind: "people", type: "people" })),
    ];

    for (const tile of tiles) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `graffiti-tile ${tile.type}`;
      const name = document.createElement("span");
      name.className = "graffiti-name";
      name.textContent = tile.name;
      const date = document.createElement("span");
      date.className = "graffiti-date";
      date.textContent = WALL_DATES[tile.name] || "—";
      btn.appendChild(name);
      btn.appendChild(date);
      btn.addEventListener("click", () => {
        activeFilter = { kind: tile.kind, value: tile.name };
        setView("library");
        renderAll();
      });
      el.graffitiGrid.appendChild(btn);
    }
  }

  /**
   * @param {HTMLElement | null} container
   * @param {string[]} options
   * @param {string[]} selected
   */
  function fillCheckGrid(container, options, selected) {
    if (!container) return;
    container.innerHTML = "";
    for (const opt of options) {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = opt;
      input.checked = selected.includes(opt);
      label.appendChild(input);
      label.appendChild(document.createTextNode(opt));
      container.appendChild(label);
    }
  }

  /**
   * @param {HTMLElement | null} container
   * @returns {string[]}
   */
  function readChecks(container) {
    if (!container) return [];
    return Array.from(container.querySelectorAll("input:checked")).map(
      (n) => /** @type {HTMLInputElement} */ (n).value
    );
  }

  function openEdit(id) {
    const track = library.tracks.find((t) => t.id === id);
    if (!track) return;
    el.editId.value = track.id;
    el.editTitle.value = track.title;
    el.editNotes.value = track.notes || "";
    fillCheckGrid(el.editBands, PRESETS.bands, track.bands);
    fillCheckGrid(el.editPlaces, PRESETS.places, track.places);
    fillCheckGrid(el.editPeople, PRESETS.people, track.people);
    fillCheckGrid(el.editInstruments, PRESETS.instruments, track.instruments);
    fillCheckGrid(el.editVibes, PRESETS.vibes, track.vibes);
    el.editCover.value = "";
    el.viewEdit.hidden = false;
  }

  function closeEdit() {
    el.viewEdit.hidden = true;
  }

  /**
   * @param {string} id
   */
  async function playTrack(id) {
    const track = library.tracks.find((t) => t.id === id);
    if (!track) return;

    const url = ensureBlobUrl(id);
    if (!url) {
      el.nowTitle.textContent = track.title;
      el.nowNote.textContent =
        "Metadata is saved, but the audio file isn’t in this session. Re-import the file or folder to play.";
      updateNowPlaying(track);
      return;
    }

    currentId = id;
    el.audio.src = url;
    try {
      await el.audio.play();
      el.btnPlay.textContent = "❚❚";
    } catch {
      el.btnPlay.textContent = "▶";
    }
    updateNowPlaying(track);
    renderLibrary();
  }

  /**
   * @param {TrackMeta} track
   */
  function updateNowPlaying(track) {
    el.nowTitle.textContent = track.title;
    if (track.notes) {
      el.nowNote.textContent = track.notes;
    } else {
      const band = track.bands[0];
      const place = track.places[0] || "Frankies wall";
      el.nowNote.textContent = band
        ? `Playing: ${band} — ${track.title} (${place}, late night)`
        : `Playing: ${track.title} (${place})`;
    }

    el.nowTags.innerHTML = "";
    const chips = [
      ...track.bands.map((v) => ({ v, accent: false })),
      ...track.instruments.map((v) => ({ v, accent: false })),
      ...track.vibes.map((v) => ({
        v,
        accent: v === "Mom's Smile",
      })),
      ...track.people.filter((p) => p === "Mom").map((v) => ({ v, accent: true })),
    ];
    for (const chip of chips.slice(0, 8)) {
      const span = document.createElement("span");
      span.className = "chip" + (chip.accent ? " accent" : "");
      span.textContent = chip.v;
      el.nowTags.appendChild(span);
    }

    if (track.coverDataUrl) {
      el.coverArt.src = track.coverDataUrl;
      el.coverArt.hidden = false;
      el.coverFallback.hidden = true;
    } else {
      el.coverArt.removeAttribute("src");
      el.coverArt.hidden = true;
      el.coverFallback.hidden = false;
    }
  }

  function playRelative(delta) {
    const list = filteredTracks();
    if (!list.length) return;
    let idx = list.findIndex((t) => t.id === currentId);
    if (idx < 0) idx = 0;
    else idx = (idx + delta + list.length) % list.length;
    playTrack(list[idx].id);
  }

  function setView(view) {
    currentView = view;
    document.querySelectorAll(".view-btn").forEach((btn) => {
      const isActive = btn.getAttribute("data-view") === view;
      btn.classList.toggle("is-active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    if (view === "wall") {
      el.viewLibrary.hidden = true;
      el.viewWall.hidden = false;
      el.viewLibrary.classList.remove("is-active");
      el.viewWall.classList.add("is-active");
    } else {
      el.viewWall.hidden = true;
      el.viewLibrary.hidden = false;
      el.viewWall.classList.remove("is-active");
      el.viewLibrary.classList.add("is-active");
      if (view === "moms-smile") {
        activeFilter = null;
      }
    }
    closeEdit();
    renderAll();
  }

  function renderAll() {
    renderSidebarTags();
    renderLibrary();
    renderGraffiti();
  }

  function updateProgress() {
    const a = el.audio;
    const dur = a.duration || 0;
    const cur = a.currentTime || 0;
    el.timeCurrent.textContent = formatTime(cur);
    el.timeDuration.textContent = formatTime(dur);
    if (!seeking && dur > 0) {
      const pct = (cur / dur) * 1000;
      el.seek.value = String(Math.round(pct));
      el.seek.style.setProperty("--progress", `${(cur / dur) * 100}%`);
    }
  }

  function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(/** @type {string} */ (reader.result));
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });
  }

  // —— Events ——

  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const view = btn.getAttribute("data-view");
      if (view === "library" || view === "wall" || view === "moms-smile") {
        setView(view);
      }
    });
  });

  el.btnClearFilter.addEventListener("click", () => {
    activeFilter = null;
    renderAll();
  });

  el.btnImportFiles.addEventListener("click", async () => {
    if (window.showOpenFilePicker) {
      try {
        const handles = await window.showOpenFilePicker({
          multiple: true,
          types: [
            {
              description: "Audio",
              accept: {
                "audio/*": [".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".opus"],
              },
            },
          ],
        });
        const files = [];
        for (const h of handles) {
          files.push(await h.getFile());
        }
        await importFiles(files);
        return;
      } catch (err) {
        if (err && err.name === "AbortError") return;
      }
    }
    el.fileInput.click();
  });

  el.btnImportFolder.addEventListener("click", async () => {
    if (window.showDirectoryPicker) {
      try {
        const dir = await window.showDirectoryPicker();
        const files = [];
        for await (const entry of dir.values()) {
          if (entry.kind === "file") {
            const file = await entry.getFile();
            if (isAudioFile(file)) files.push(file);
          }
        }
        await importFiles(files);
        return;
      } catch (err) {
        if (err && err.name === "AbortError") return;
      }
    }
    el.folderInput.click();
  });

  el.fileInput.addEventListener("change", async () => {
    const files = Array.from(el.fileInput.files || []);
    el.fileInput.value = "";
    await importFiles(files);
  });

  el.folderInput.addEventListener("change", async () => {
    const files = Array.from(el.folderInput.files || []);
    el.folderInput.value = "";
    await importFiles(files);
  });

  el.btnCloseEdit.addEventListener("click", closeEdit);

  el.tagForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = el.editId.value;
    const track = library.tracks.find((t) => t.id === id);
    if (!track) return;

    track.title = el.editTitle.value.trim() || track.title;
    track.notes = el.editNotes.value.trim();
    track.bands = readChecks(el.editBands);
    track.places = readChecks(el.editPlaces);
    track.people = readChecks(el.editPeople);
    track.instruments = readChecks(el.editInstruments);
    track.vibes = readChecks(el.editVibes);

    const coverFile = el.editCover.files && el.editCover.files[0];
    if (coverFile && coverFile.type.startsWith("image/")) {
      try {
        track.coverDataUrl = await readFileAsDataUrl(coverFile);
      } catch {
        /* keep previous cover */
      }
    }

    await saveLibrary();
    closeEdit();
    if (currentId === id) updateNowPlaying(track);
    renderAll();
  });

  el.btnRemoveTrack.addEventListener("click", async () => {
    const id = el.editId.value;
    library.tracks = library.tracks.filter((t) => t.id !== id);
    revokeUrl(id);
    sessionFiles.delete(id);
    if (currentId === id) {
      currentId = null;
      el.audio.removeAttribute("src");
      el.audio.load();
      el.nowTitle.textContent = "Nothing queued";
      el.nowNote.textContent = "Import your recordings to start the wall.";
      el.nowTags.innerHTML = "";
      el.coverArt.hidden = true;
      el.coverFallback.hidden = false;
      el.btnPlay.textContent = "▶";
    }
    await saveLibrary();
    closeEdit();
    renderAll();
  });

  el.btnPlay.addEventListener("click", async () => {
    if (!el.audio.src) {
      const list = filteredTracks();
      const playable = list.find((t) => sessionFiles.has(t.id));
      if (playable) {
        await playTrack(playable.id);
      } else if (list.length) {
        await playTrack(list[0].id);
      }
      return;
    }
    if (el.audio.paused) {
      try {
        await el.audio.play();
        el.btnPlay.textContent = "❚❚";
      } catch {
        /* autoplay blocked */
      }
    } else {
      el.audio.pause();
      el.btnPlay.textContent = "▶";
    }
  });

  el.btnPrev.addEventListener("click", () => playRelative(-1));
  el.btnNext.addEventListener("click", () => playRelative(1));

  el.audio.addEventListener("timeupdate", updateProgress);
  el.audio.addEventListener("loadedmetadata", updateProgress);
  el.audio.addEventListener("ended", () => {
    el.btnPlay.textContent = "▶";
    playRelative(1);
  });
  el.audio.addEventListener("play", () => {
    el.btnPlay.textContent = "❚❚";
  });
  el.audio.addEventListener("pause", () => {
    el.btnPlay.textContent = "▶";
  });

  el.seek.addEventListener("pointerdown", () => {
    seeking = true;
  });
  el.seek.addEventListener("pointerup", () => {
    seeking = false;
  });
  el.seek.addEventListener("input", () => {
    const dur = el.audio.duration || 0;
    const pct = Number(el.seek.value) / 1000;
    el.seek.style.setProperty("--progress", `${pct * 100}%`);
    if (dur > 0) {
      el.timeCurrent.textContent = formatTime(dur * pct);
    }
  });
  el.seek.addEventListener("change", () => {
    const dur = el.audio.duration || 0;
    if (dur > 0) {
      el.audio.currentTime = (Number(el.seek.value) / 1000) * dur;
    }
    seeking = false;
  });

  // Boot
  loadLibrary().then(() => {
    renderAll();
    if (library.tracks.length) {
      el.nowNote.textContent =
        "Tags restored. Re-import audio files to play — metadata stayed local.";
    }
  });
})();
