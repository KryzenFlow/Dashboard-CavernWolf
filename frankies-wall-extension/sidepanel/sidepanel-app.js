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
    people: ["Mom", "Son", "Solo", "With Friends", "Drew"],
    instruments: ["sax", "electric", "bass", "drums", "vocals", "acoustic", "mixed"],
    vibes: [
      "Mom's Smile",
      "River Breeze",
      "fight & focus",
      "late night",
      "practice",
      "live",
      "studio",
    ],
  };

  const STORY_MODE_PRESETS = Array.isArray(window.STORY_MODE_PRESETS)
    ? window.STORY_MODE_PRESETS
    : ["live", "studio", "mixed", "mom_mode"];

  /** @type {StoryFilterDef[]} */
  const STORY_FILTERS = Array.isArray(window.STORY_FILTERS)
    ? window.STORY_FILTERS
    : [{ id: "all", label: "All" }];

  const matchStoryFilter =
    typeof window.trackMatchesStoryFilter === "function"
      ? window.trackMatchesStoryFilter
      : () => true;

  const storyFilterIdForTag =
    typeof window.storyFilterIdForTag === "function"
      ? window.storyFilterIdForTag
      : () => null;

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

  /** @type {string} */
  let instrumentFilter = "all";

  /** @type {string} */
  let storyFilter = "all";

  const INSTRUMENT_FILTER_IDS = new Set(["all", "electric", "bass", "sax", "mixed"]);

  /** @type {'library' | 'wall' | 'moms-smile'} */
  let currentView = "library";

  let seeking = false;

  /**
   * @typedef {object} CatalogTrack
   * @property {string} id
   * @property {string} title
   * @property {string} artist
   * @property {string} file
   * @property {string} instrument
   */

  /**
   * @typedef {object} TrackMeta
   * @property {string} id
   * @property {string} title
   * @property {string} fileName
   * @property {string} mimeType
   * @property {number} size
   * @property {string | null} [file] bundled path under extension root
   * @property {string[]} bands
   * @property {string[]} places
   * @property {string[]} people
   * @property {string[]} instruments
   * @property {string} instrument primary instrument for filter engine
   * @property {string[]} modes
   * @property {string[]} vibes
   * @property {string} notes
   * @property {string | null} coverDataUrl
   * @property {number} addedAt
   */

  /** @type {CatalogTrack[]} */
  const CATALOG_TRACKS = Array.isArray(window.CATALOG_TRACKS)
    ? window.CATALOG_TRACKS
    : [];

  const el = {
    bandTags: document.getElementById("band-tags"),
    placeTags: document.getElementById("place-tags"),
    peopleTags: document.getElementById("people-tags"),
    instrumentTags: document.getElementById("instrument-tags"),
    modeTags: document.getElementById("mode-tags"),
    vibeTags: document.getElementById("vibe-tags"),
    btnImportFiles: document.getElementById("btn-import-files"),
    btnImportFolder: document.getElementById("btn-import-folder"),
    fileInput: document.getElementById("file-input"),
    folderInput: document.getElementById("folder-input"),
    trackList: document.getElementById("track-list"),
    libraryEmpty: document.getElementById("library-empty"),
    libraryHeading: document.getElementById("library-heading"),
    btnClearFilter: document.getElementById("btn-clear-filter"),
    instrumentFilter: document.getElementById("instrumentFilter"),
    storyFilter: document.getElementById("storyFilter"),
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
    editModes: document.getElementById("edit-modes"),
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

  function formatModeLabel(mode) {
    return mode.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function resolveTrackInstrument(track) {
    if (track.instrument) return track.instrument;
    const list = track.instruments || [];
    if (list.length > 1 || list.includes("mixed")) return "mixed";
    return list[0] || "";
  }

  /**
   * @param {TrackMeta} track
   */
  function syncTrackInstrument(track) {
    track.instrument = resolveTrackInstrument(track);
  }

  /**
   * @param {Partial<TrackMeta>} track
   * @returns {TrackMeta}
   */
  function normalizeTrack(track) {
    const normalized = {
      id: track.id || uid(),
      title: track.title || "Untitled",
      fileName: track.fileName || "",
      mimeType: track.mimeType || "audio/*",
      size: track.size || 0,
      file: track.file ?? null,
      bands: track.bands || [],
      places: track.places || [],
      people: track.people || [],
      instruments: track.instruments || [],
      instrument: track.instrument || "",
      modes: track.modes || [],
      vibes: track.vibes || [],
      notes: track.notes || "",
      coverDataUrl: track.coverDataUrl ?? null,
      addedAt: track.addedAt || Date.now(),
    };
    syncTrackInstrument(normalized);
    return normalized;
  }
  function titleFromFileName(name) {
    return name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim() || name;
  }

  function basenameFromPath(path) {
    const parts = path.split("/");
    return parts[parts.length - 1] || path;
  }

  function normalizeCatalogPath(path) {
    return path.replace(/^\/+/, "");
  }

  /**
   * @param {CatalogTrack} catalog
   * @returns {TrackMeta}
   */
  function catalogToTrackMeta(catalog) {
    const fileName = basenameFromPath(catalog.file);
    const artist = catalog.artist?.trim() || "";
    const instrument = catalog.instrument?.trim() || "";
    /** @type {TrackMeta} */
    const meta = {
      id: catalog.id,
      title: catalog.title,
      fileName,
      mimeType: "audio/mpeg",
      size: 0,
      file: normalizeCatalogPath(catalog.file),
      bands: artist ? [artist] : [],
      places: [],
      people: artist === "Drew" ? ["Drew"] : [],
      instruments: instrument ? [instrument] : [],
      instrument,
      modes:
        catalog.id === "drew_sax_live_01" || catalog.id === "drew_bass_riff_02"
          ? ["live"]
          : ["studio"],
      vibes: instrument === "sax" ? ["Mom's Smile"] : [],
      notes: "",
      coverDataUrl: null,
      addedAt: Date.now(),
    };
    return meta;
  }

  /**
   * @param {string} fileName
   * @returns {CatalogTrack | undefined}
   */
  function findCatalogByFileName(fileName) {
    const lower = fileName.toLowerCase();
    return CATALOG_TRACKS.find((track) => {
      const base = basenameFromPath(track.file).toLowerCase();
      return base === lower;
    });
  }

  function mergeCatalogIntoLibrary() {
    if (!CATALOG_TRACKS.length) return false;
    let added = false;
    for (const catalog of CATALOG_TRACKS) {
      const existing = library.tracks.find((t) => t.id === catalog.id);
      if (existing) {
        if (!existing.file) existing.file = normalizeCatalogPath(catalog.file);
        if (!existing.bands.length && catalog.artist) {
          existing.bands = [catalog.artist];
        }
        if (!existing.instruments.length && catalog.instrument) {
          existing.instruments = [catalog.instrument];
          existing.instrument = catalog.instrument;
        }
        continue;
      }
      library.tracks.push(catalogToTrackMeta(catalog));
      added = true;
    }
    library.tracks.sort((a, b) => b.addedAt - a.addedAt);
    return added;
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
        library = { tracks: stored.tracks.map((t) => normalizeTrack(t)) };
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
        file: t.file || null,
        bands: t.bands,
        places: t.places,
        people: t.people,
        instruments: t.instruments,
        instrument: t.instrument,
        modes: t.modes,
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
   * Session import blob first, then bundled extension path from catalog.
   * @param {string} id
   * @returns {string | null}
   */
  function resolveTrackUrl(id) {
    const blobUrl = ensureBlobUrl(id);
    if (blobUrl) return blobUrl;

    const track = library.tracks.find((t) => t.id === id);
    if (!track?.file) return null;

    try {
      return chrome.runtime.getURL(normalizeCatalogPath(track.file));
    } catch {
      return null;
    }
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
      const catalogMatch = findCatalogByFileName(file.name);
      const id = catalogMatch?.id ?? uid();
      const existing = library.tracks.find((t) => t.id === id);

      /** @type {TrackMeta} */
      const meta = existing ?? {
        id,
        title: catalogMatch?.title ?? titleFromFileName(file.name),
        fileName: file.name,
        mimeType: file.type || "audio/*",
        size: file.size,
        file: catalogMatch ? normalizeCatalogPath(catalogMatch.file) : null,
        bands: catalogMatch?.artist ? [catalogMatch.artist] : [],
        places: [],
        people: catalogMatch?.artist === "Drew" ? ["Drew"] : [],
        instruments: catalogMatch?.instrument ? [catalogMatch.instrument] : [],
        instrument: catalogMatch?.instrument || "",
        modes: [],
        vibes:
          catalogMatch?.instrument === "sax" ? ["Mom's Smile"] : [],
        notes: "",
        coverDataUrl: null,
        addedAt: Date.now(),
      };

      meta.fileName = file.name;
      meta.mimeType = file.type || meta.mimeType || "audio/*";
      meta.size = file.size;
      syncTrackInstrument(meta);

      if (!existing) {
        library.tracks.unshift(meta);
      }

      revokeUrl(id);
      sessionFiles.set(id, file);
      ensureBlobUrl(id);
    }

    await saveLibrary();
    renderAll();
    el.nowNote.textContent = `Imported ${audioFiles.length} local track${audioFiles.length === 1 ? "" : "s"}. Tag them on the wall.`;
  }

  function setInstrumentFilter(value) {
    if (!INSTRUMENT_FILTER_IDS.has(value)) return;
    instrumentFilter = value;
    if (el.instrumentFilter) {
      el.instrumentFilter.querySelectorAll("button[data-instrument]").forEach((btn) => {
        const match = btn.getAttribute("data-instrument") === value;
        btn.classList.toggle("is-active", match);
        btn.setAttribute("aria-pressed", match ? "true" : "false");
      });
    }
  }

  function setStoryFilter(value) {
    if (!STORY_FILTERS.some((f) => f.id === value)) return;
    storyFilter = value;
    if (el.storyFilter) {
      el.storyFilter.querySelectorAll("button[data-story-filter]").forEach((btn) => {
        const match = btn.getAttribute("data-story-filter") === value;
        btn.classList.toggle("is-active", match);
        btn.setAttribute("aria-pressed", match ? "true" : "false");
      });
    }
  }

  function renderStoryFilterBar() {
    if (!el.storyFilter) return;
    el.storyFilter.innerHTML = "";
    const storyOnly = STORY_FILTERS.filter(
      (def) => !INSTRUMENT_FILTER_IDS.has(def.id)
    );
    for (const def of storyOnly) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.dataset.storyFilter = def.id;
      btn.textContent = def.label;
      if (def.hint) btn.title = def.hint;
      btn.addEventListener("click", () => {
        setStoryFilter(def.id);
        renderAll();
      });
      el.storyFilter.appendChild(btn);
    }
    setStoryFilter(storyFilter);
  }

  function getTracksBeforeInstrumentFilter() {
    let tracks = library.tracks.slice();

    if (currentView === "moms-smile") {
      tracks = tracks.filter((t) => matchStoryFilter(t, "mom_mode"));
    }

    if (storyFilter !== "all") {
      tracks = tracks.filter((t) => matchStoryFilter(t, storyFilter));
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
          case "modes":
            return t.modes.includes(value);
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

  /**
   * Instrument filter engine — simple, clean.
   * @param {string} instrument
   */
  function filterByInstrument(instrument) {
    if (!INSTRUMENT_FILTER_IDS.has(instrument)) return;
    setInstrumentFilter(instrument);

    const tracks = getTracksBeforeInstrumentFilter();
    let filtered;

    if (instrument === "all") {
      filtered = tracks;
    } else {
      filtered = tracks.filter((track) => track.instrument === instrument);
    }

    renderTrackList(filtered);
    updateLibraryHeading();
    renderSidebarTags();
  }

  function filteredTracks() {
    const tracks = getTracksBeforeInstrumentFilter();
    const applyFilter =
      typeof window.filterTracksByInstrument === "function"
        ? window.filterTracksByInstrument
        : (list, instrument) => {
            if (instrument === "all") return list;
            return list.filter((track) => track.instrument === instrument);
          };
    return applyFilter(tracks, instrumentFilter);
  }

  /**
   * @param {TrackMeta[]} tracks
   */
  function renderTrackList(tracks) {
    el.trackList.innerHTML = "";
    el.libraryEmpty.hidden = tracks.length > 0;

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
        track.instrument || track.instruments[0],
        ...track.modes.map(formatModeLabel),
        ...track.vibes.slice(0, 1),
      ].filter(Boolean);
      const needsFile = !sessionFiles.has(track.id) && !track.file;
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

  function updateLibraryHeading() {
    if (currentView === "moms-smile") {
      el.libraryHeading.textContent = "Mom's Smile";
    } else if (activeFilter) {
      el.libraryHeading.textContent =
        activeFilter.kind === "modes"
          ? formatModeLabel(activeFilter.value)
          : activeFilter.value;
    } else if (instrumentFilter !== "all") {
      const label =
        instrumentFilter.charAt(0).toUpperCase() + instrumentFilter.slice(1);
      el.libraryHeading.textContent = label;
    } else if (storyFilter !== "all") {
      const def = STORY_FILTERS.find((f) => f.id === storyFilter);
      el.libraryHeading.textContent = def?.label || "Library";
    } else {
      el.libraryHeading.textContent = "Library";
    }

    el.btnClearFilter.hidden = !activeFilter;
  }

  function renderSidebarTags() {
    /**
     * @param {HTMLElement | null} container
     * @param {string[]} names
     * @param {string} kind
     */
    function fill(container, names, kind, labelFor) {
      if (!container) return;
      container.innerHTML = "";
      names.forEach((name, i) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = labelFor ? labelFor(name) : name;
        btn.dataset.kind = kind;
        btn.dataset.value = name;
        const mappedStory = storyFilterIdForTag(kind, name);
        const mappedInstrument =
          kind === "instruments" && INSTRUMENT_FILTER_IDS.has(name) ? name : null;
        if (activeFilter?.kind === kind && activeFilter.value === name) {
          btn.classList.add("is-active");
        } else if (mappedInstrument && instrumentFilter === mappedInstrument) {
          btn.classList.add("is-active");
        } else if (mappedStory && storyFilter === mappedStory) {
          btn.classList.add("is-active");
        }
        btn.style.setProperty("--tilt", `${((i % 5) - 2) * 0.8}deg`);
        btn.addEventListener("click", () => {
          if (kind === "instruments" && INSTRUMENT_FILTER_IDS.has(name) && name !== "all") {
            if (instrumentFilter === name) {
              filterByInstrument("all");
            } else {
              activeFilter = null;
              filterByInstrument(name);
            }
            if (currentView === "wall") setView("library");
            else renderSidebarTags();
            return;
          }
          const storyId = storyFilterIdForTag(kind, name);
          if (storyId && !INSTRUMENT_FILTER_IDS.has(storyId)) {
            if (storyFilter === storyId) {
              setStoryFilter("all");
            } else {
              activeFilter = null;
              setStoryFilter(storyId);
            }
            if (currentView === "wall") setView("library");
            else renderAll();
            return;
          }
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
    fill(el.modeTags, STORY_MODE_PRESETS, "modes", formatModeLabel);
    fill(el.vibeTags, PRESETS.vibes, "vibes");
  }

  function renderLibrary() {
    updateLibraryHeading();
    renderTrackList(filteredTracks());
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
   * @param {(value: string) => string} [labelFor]
   */
  function fillCheckGrid(container, options, selected, labelFor) {
    if (!container) return;
    container.innerHTML = "";
    for (const opt of options) {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = opt;
      input.checked = selected.includes(opt);
      label.appendChild(input);
      label.appendChild(document.createTextNode(labelFor ? labelFor(opt) : opt));
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
    fillCheckGrid(el.editModes, STORY_MODE_PRESETS, track.modes, formatModeLabel);
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

    const url = resolveTrackUrl(id);
    if (!url) {
      el.nowTitle.textContent = track.title;
      el.nowNote.textContent = track.file
        ? `Add ${track.fileName} under the extension music/ folder, or re-import to play.`
        : "Metadata is saved, but the audio file isn’t in this session. Re-import the file or folder to play.";
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
      ...track.modes.map((v) => ({ v: formatModeLabel(v), accent: v === "mom_mode" })),
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

  renderStoryFilterBar();

  if (el.instrumentFilter) {
    el.instrumentFilter.querySelectorAll("button[data-instrument]").forEach((btn) => {
      btn.addEventListener("click", () => {
        filterByInstrument(btn.getAttribute("data-instrument") || "all");
      });
    });
    setInstrumentFilter(instrumentFilter);
  }

  window.filterByInstrument = filterByInstrument;

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
    track.modes = readChecks(el.editModes);
    track.vibes = readChecks(el.editVibes);
    syncTrackInstrument(track);

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
  function setTuningForkPlaying(playing) {
    document.querySelectorAll("[data-tuning-fork]").forEach((node) => {
      node.classList.toggle("is-playing", playing);
    });
  }

  const TUNING_FORK_META = window.TuningFork?.META || {
    meaning: "Center — Find Your Tone",
    origin: "Mom's polish and practical wisdom",
  };

  let forkStopTimer = null;

  function pulseTuningForkIcons(durationMs = 2000) {
    const pulseTargets = document.querySelectorAll(
      "[data-tuning-fork], #tuningForkBtn"
    );
    pulseTargets.forEach((node) => {
      node.classList.add("is-forking");
    });
    if (forkStopTimer) clearTimeout(forkStopTimer);
    forkStopTimer = setTimeout(() => {
      pulseTargets.forEach((node) => {
        node.classList.remove("is-forking");
      });
    }, durationMs);
  }

  // Wrap drop-in from components/playTuningFork.js with icon pulse
  const playTuningForkDropIn = window.playTuningFork;
  window.playTuningFork = function playTuningFork(duration = 2) {
    if (typeof playTuningForkDropIn === "function") {
      playTuningForkDropIn(duration);
    }
    pulseTuningForkIcons(duration * 1000);
  };

  if (window.TuningFork) {
    window.TuningFork.mountAll((placement) => {
      const sizeByPlacement = { logo: 28, art: 32, rail: 22 };
      return {
        size: sizeByPlacement[placement] ?? window.TuningFork.DEFAULT_PROPS.size,
        stroke: window.TuningFork.DEFAULT_PROPS.stroke,
        strokeWidth: window.TuningFork.DEFAULT_PROPS.strokeWidth,
        interactive: true,
        onClick: "playTuningFork",
        durationSeconds: 2,
        meaning: TUNING_FORK_META.meaning,
        origin: TUNING_FORK_META.origin,
      };
    });
  }

  // Fallback if mounts already bound via TuningFork.create (string onClick)
  document.querySelectorAll('[data-onclick="playTuningFork"]').forEach((node) => {
    if (node.dataset.forkBound === "1") return;
    node.dataset.forkBound = "1";
    node.setAttribute("data-meaning", TUNING_FORK_META.meaning);
    node.setAttribute("data-origin", TUNING_FORK_META.origin);
    node.setAttribute(
      "title",
      `${TUNING_FORK_META.meaning}\n${TUNING_FORK_META.origin}`
    );
    node.setAttribute(
      "aria-label",
      `${TUNING_FORK_META.meaning}. ${TUNING_FORK_META.origin}. Play A440 tuning fork.`
    );
    // create() already binds click when mounted; only re-bind orphan markup
    if (!node.closest("[data-tuning-fork-mount]")) {
      node.addEventListener("click", () => {
        const duration = Number(node.dataset.durationSeconds) || 2;
        window.playTuningFork(duration);
      });
    }
  });

  const logoMeaning = document.querySelector(".tuning-fork-meaning--logo");
  if (logoMeaning) {
    logoMeaning.textContent = TUNING_FORK_META.meaning;
  }

  el.audio.addEventListener("ended", () => {
    el.btnPlay.textContent = "▶";
    setTuningForkPlaying(false);
    playRelative(1);
  });
  el.audio.addEventListener("play", () => {
    el.btnPlay.textContent = "❚❚";
    setTuningForkPlaying(true);
  });
  el.audio.addEventListener("pause", () => {
    el.btnPlay.textContent = "▶";
    setTuningForkPlaying(false);
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
  loadLibrary().then(async () => {
    const catalogAdded = mergeCatalogIntoLibrary();
    if (catalogAdded) {
      await saveLibrary();
    }
    renderAll();
    if (library.tracks.length) {
      const hasBundled = library.tracks.some((t) => t.file);
      el.nowNote.textContent = hasBundled
        ? "Catalog loaded. Bundled tracks play from music/ — imports override for this session."
        : "Tags restored. Re-import audio files to play — metadata stayed local.";
    }
  });
})();
