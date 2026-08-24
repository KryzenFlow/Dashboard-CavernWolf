/**
 * Metadata — library persistence + track normalization.
 */
(function initStorage(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.STORAGE_KEY = "frankiesWallLibrary";

  FrankiesWall.state = FrankiesWall.state || {
    library: { tracks: [] },
    currentId: null,
    activeFilter: null,
    instrumentFilter: "all",
    vibeFilter: "all",
    storyFilter: "all",
    currentView: "library",
    seeking: false,
    volume: 0.85,
    waveformEnabled: false,
  };

  FrankiesWall.session = FrankiesWall.session || {
    blobUrls: new Map(),
    sessionFiles: new Map(),
  };

  FrankiesWall.uid = function uid() {
    return `t_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
  };

  FrankiesWall.resolveTrackInstrument = function resolveTrackInstrument(track) {
    if (track.instrument) return track.instrument;
    const list = track.instruments || [];
    if (list.length > 1 || list.includes("mixed")) return "mixed";
    return list[0] || "";
  };

  FrankiesWall.syncTrackInstrument = function syncTrackInstrument(track) {
    track.instrument = FrankiesWall.resolveTrackInstrument(track);
  };

  FrankiesWall.normalizeTrack = function normalizeTrack(track) {
    const normalized = {
      id: track.id || FrankiesWall.uid(),
      title: track.title || "Untitled",
      artist: track.artist || track.bands?.[0] || "",
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
    FrankiesWall.syncTrackInstrument(normalized);
    return normalized;
  };

  FrankiesWall.basenameFromPath = function basenameFromPath(path) {
    const parts = path.split("/");
    return parts[parts.length - 1] || path;
  };

  FrankiesWall.normalizeCatalogPath = function normalizeCatalogPath(path) {
    return path.replace(/^\/+/, "");
  };

  FrankiesWall.catalogToTrackMeta = function catalogToTrackMeta(catalog) {
    const fileName = FrankiesWall.basenameFromPath(catalog.file);
    const artist = catalog.artist?.trim() || "";
    const instrument = catalog.instrument?.trim() || "";
    const vibes = FrankiesWall.catalogVibesToTrackVibes
      ? FrankiesWall.catalogVibesToTrackVibes(catalog)
      : catalog.vibe
        ? [catalog.vibe]
        : catalog.vibes || [];

    return FrankiesWall.normalizeTrack({
      id: catalog.id,
      title: catalog.title,
      artist,
      fileName,
      mimeType: "audio/mpeg",
      size: 0,
      file: FrankiesWall.normalizeCatalogPath(catalog.file),
      bands: artist ? [artist] : [],
      people: artist === "Drew" ? ["Drew"] : [],
      instruments: instrument ? [instrument] : [],
      instrument,
      modes: catalog.id.includes("live") ? ["live"] : ["studio"],
      vibes,
    });
  };

  FrankiesWall.findCatalogByFileName = function findCatalogByFileName(fileName) {
    const catalog = global.CATALOG_TRACKS || [];
    const lower = fileName.toLowerCase();
    return catalog.find((track) => {
      const base = FrankiesWall.basenameFromPath(track.file).toLowerCase();
      return base === lower;
    });
  };

  FrankiesWall.mergeCatalogIntoLibrary = function mergeCatalogIntoLibrary() {
    const catalog = global.CATALOG_TRACKS || [];
    if (!catalog.length) return false;
    let added = false;
    for (const entry of catalog) {
      const existing = FrankiesWall.state.library.tracks.find((t) => t.id === entry.id);
      if (existing) {
        if (!existing.file) existing.file = FrankiesWall.normalizeCatalogPath(entry.file);
        if (!existing.bands.length && entry.artist) existing.bands = [entry.artist];
        if (!existing.instruments.length && entry.instrument) {
          existing.instruments = [entry.instrument];
          existing.instrument = entry.instrument;
        }
        continue;
      }
      FrankiesWall.state.library.tracks.push(FrankiesWall.catalogToTrackMeta(entry));
      added = true;
    }
    FrankiesWall.state.library.tracks.sort((a, b) => b.addedAt - a.addedAt);
    return added;
  };

  FrankiesWall.loadLibrary = async function loadLibrary() {
    try {
      const data = await chrome.storage.local.get(FrankiesWall.STORAGE_KEY);
      const stored = data[FrankiesWall.STORAGE_KEY];
      if (stored && Array.isArray(stored.tracks)) {
        FrankiesWall.state.library = {
          tracks: stored.tracks.map((t) => FrankiesWall.normalizeTrack(t)),
        };
      }
    } catch {
      FrankiesWall.state.library = { tracks: [] };
    }
  };

  FrankiesWall.saveLibrary = async function saveLibrary() {
    const payload = {
      tracks: FrankiesWall.state.library.tracks.map((t) => ({
        id: t.id,
        title: t.title,
        artist: t.artist || t.bands?.[0] || "",
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
    await chrome.storage.local.set({ [FrankiesWall.STORAGE_KEY]: payload });
  };

  FrankiesWall.titleFromFileName = function titleFromFileName(name) {
    return name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim() || name;
  };

  FrankiesWall.isAudioFile = function isAudioFile(file) {
    if (file.type && file.type.startsWith("audio/")) return true;
    return /\.(mp3|wav|ogg|m4a|aac|flac|opus|webm)$/i.test(file.name);
  };
})(typeof window !== "undefined" ? window : globalThis);
