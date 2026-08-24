/**
 * Rendering — Frankie's Wall tag selector, graffiti, library chrome.
 */
(function initFrankiesWall(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.getPresets = function getPresets() {
    return {
      ...FrankiesWall.TAG_PRESETS,
      vibes: FrankiesWall.VIBE_IDS || [],
    };
  };

  FrankiesWall.setInstrumentFilterUi = function setInstrumentFilterUi(value) {
    const bar = FrankiesWall.el.instrumentFilter;
    if (!bar) return;
    bar.querySelectorAll("button[data-instrument]").forEach((btn) => {
      const match = btn.getAttribute("data-instrument") === value;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-pressed", match ? "true" : "false");
    });
  };

  FrankiesWall.setVibeFilterUi = function setVibeFilterUi(value) {
    const bar = FrankiesWall.el.vibeFilter;
    if (!bar) return;
    bar.querySelectorAll("button[data-vibe]").forEach((btn) => {
      const match = btn.getAttribute("data-vibe") === value;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-pressed", match ? "true" : "false");
    });
  };

  FrankiesWall.filterByVibe = function filterByVibe(vibe) {
    FrankiesWall.state.vibeFilter = vibe || "all";
    FrankiesWall.setVibeFilterUi(FrankiesWall.state.vibeFilter);
    FrankiesWall.renderLibrary();
    FrankiesWall.renderSidebarTags();
  };

  FrankiesWall.setStoryFilter = function setStoryFilter(value) {
    if (!FrankiesWall.STORY_FILTERS.some((f) => f.id === value)) return;
    FrankiesWall.state.storyFilter = value;
    const bar = FrankiesWall.el.storyFilter;
    if (!bar) return;
    bar.querySelectorAll("button[data-story-filter]").forEach((btn) => {
      const match = btn.getAttribute("data-story-filter") === value;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-pressed", match ? "true" : "false");
    });
  };

  FrankiesWall.renderStoryFilterBar = function renderStoryFilterBar() {
    const el = FrankiesWall.el;
    if (!el.storyFilter) return;
    const instrumentIds = new Set(FrankiesWall.INSTRUMENT_FILTER_IDS);
    el.storyFilter.innerHTML = "";
    for (const def of FrankiesWall.STORY_FILTERS.filter((f) => !instrumentIds.has(f.id))) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.dataset.storyFilter = def.id;
      btn.textContent = def.label;
      if (def.hint) btn.title = def.hint;
      btn.addEventListener("click", () => {
        FrankiesWall.setStoryFilter(def.id);
        FrankiesWall.renderAll();
      });
      el.storyFilter.appendChild(btn);
    }
    FrankiesWall.setStoryFilter(FrankiesWall.state.storyFilter);
  };

  FrankiesWall.updateLibraryHeading = function updateLibraryHeading() {
    const el = FrankiesWall.el;
    const { state } = FrankiesWall;
    const { formatModeLabel } = FrankiesWall.dom;

    if (state.currentView === "moms-smile") {
      el.libraryHeading.textContent = "Mom's Smile";
    } else if (state.activeFilter) {
      el.libraryHeading.textContent =
        state.activeFilter.kind === "modes"
          ? formatModeLabel(state.activeFilter.value)
          : state.activeFilter.value;
    } else if (state.instrumentFilter !== "all") {
      const label =
        state.instrumentFilter.charAt(0).toUpperCase() + state.instrumentFilter.slice(1);
      el.libraryHeading.textContent = label;
    } else if (state.vibeFilter !== "all") {
      el.libraryHeading.textContent = FrankiesWall.resolveVibeLabel(state.vibeFilter);
    } else if (state.storyFilter !== "all") {
      const def = FrankiesWall.STORY_FILTERS.find((f) => f.id === state.storyFilter);
      el.libraryHeading.textContent = def?.label || "Library";
    } else {
      el.libraryHeading.textContent = "Library";
    }
    el.btnClearFilter.hidden = !state.activeFilter;
  };

  FrankiesWall.renderSidebarTags = function renderSidebarTags() {
    const el = FrankiesWall.el;
    const PRESETS = FrankiesWall.getPresets();
    const { formatModeLabel } = FrankiesWall.dom;
    const { state } = FrankiesWall;
    const instrumentIds = new Set(FrankiesWall.INSTRUMENT_FILTER_IDS);

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
        const mappedStory = FrankiesWall.storyFilterIdForTag(kind, name);
        const mappedInstrument =
          kind === "instruments" && instrumentIds.has(name) ? name : null;
        if (state.activeFilter?.kind === kind && state.activeFilter.value === name) {
          btn.classList.add("is-active");
        } else if (mappedInstrument && state.instrumentFilter === mappedInstrument) {
          btn.classList.add("is-active");
        } else if (kind === "vibes" && state.vibeFilter === name) {
          btn.classList.add("is-active");
        } else if (mappedStory && state.storyFilter === mappedStory) {
          btn.classList.add("is-active");
        }
        btn.style.setProperty("--tilt", `${((i % 5) - 2) * 0.8}deg`);
        btn.addEventListener("click", () => {
          if (kind === "instruments" && instrumentIds.has(name) && name !== "all") {
            if (state.instrumentFilter === name) FrankiesWall.filterByInstrument("all");
            else {
              state.activeFilter = null;
              FrankiesWall.filterByInstrument(name);
            }
            if (state.currentView === "wall") FrankiesWall.setView("library");
            else FrankiesWall.renderSidebarTags();
            return;
          }
          if (kind === "vibes") {
            if (state.vibeFilter === name) FrankiesWall.filterByVibe("all");
            else {
              state.activeFilter = null;
              FrankiesWall.filterByVibe(name);
            }
            if (state.currentView === "wall") FrankiesWall.setView("library");
            else FrankiesWall.renderSidebarTags();
            return;
          }
          const storyId = FrankiesWall.storyFilterIdForTag(kind, name);
          if (storyId && !instrumentIds.has(storyId)) {
            if (state.storyFilter === storyId) FrankiesWall.setStoryFilter("all");
            else {
              state.activeFilter = null;
              FrankiesWall.setStoryFilter(storyId);
            }
            if (state.currentView === "wall") FrankiesWall.setView("library");
            else FrankiesWall.renderAll();
            return;
          }
          if (state.activeFilter?.kind === kind && state.activeFilter.value === name) {
            state.activeFilter = null;
          } else {
            state.activeFilter = { kind, value: name };
            if (state.currentView === "wall") FrankiesWall.setView("library");
          }
          FrankiesWall.renderAll();
        });
        li.appendChild(btn);
        container.appendChild(li);
      });
    }

    fill(el.bandTags, PRESETS.bands, "bands");
    fill(el.placeTags, PRESETS.places, "places");
    fill(el.peopleTags, PRESETS.people, "people");
    fill(el.instrumentTags, PRESETS.instruments, "instruments");
    fill(el.modeTags, PRESETS.modes, "modes", formatModeLabel);
    fill(el.vibeTags, PRESETS.vibes, "vibes", (id) => FrankiesWall.resolveVibeLabel(id));
  };

  FrankiesWall.renderGraffiti = function renderGraffiti() {
    const el = FrankiesWall.el;
    const PRESETS = FrankiesWall.getPresets();
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
      date.textContent = FrankiesWall.WALL_DATES[tile.name] || "—";
      btn.appendChild(name);
      btn.appendChild(date);
      btn.addEventListener("click", () => {
        FrankiesWall.state.activeFilter = { kind: tile.kind, value: tile.name };
        FrankiesWall.setView("library");
        FrankiesWall.renderAll();
      });
      el.graffitiGrid.appendChild(btn);
    }
  };

  FrankiesWall.openEdit = function openEdit(id) {
    const el = FrankiesWall.el;
    const PRESETS = FrankiesWall.getPresets();
    const { fillCheckGrid, formatModeLabel } = FrankiesWall.dom;
    const track = FrankiesWall.state.library.tracks.find((t) => t.id === id);
    if (!track) return;
    el.editId.value = track.id;
    el.editTitle.value = track.title;
    el.editNotes.value = track.notes || "";
    fillCheckGrid(el.editBands, PRESETS.bands, track.bands);
    fillCheckGrid(el.editPlaces, PRESETS.places, track.places);
    fillCheckGrid(el.editPeople, PRESETS.people, track.people);
    fillCheckGrid(el.editInstruments, PRESETS.instruments, track.instruments);
    fillCheckGrid(el.editModes, PRESETS.modes, track.modes, formatModeLabel);
    fillCheckGrid(el.editVibes, PRESETS.vibes, track.vibes, (id) =>
      FrankiesWall.resolveVibeLabel(id)
    );
    el.editCover.value = "";
    el.viewEdit.hidden = false;
  };

  FrankiesWall.closeEdit = function closeEdit() {
    FrankiesWall.el.viewEdit.hidden = true;
  };

  FrankiesWall.setView = function setView(view) {
    FrankiesWall.state.currentView = view;
    const el = FrankiesWall.el;
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
      if (view === "moms-smile") FrankiesWall.state.activeFilter = null;
    }
    FrankiesWall.closeEdit();
    FrankiesWall.renderAll();
  };

  FrankiesWall.renderAll = function renderAll() {
    FrankiesWall.renderSidebarTags();
    FrankiesWall.renderLibrary();
    FrankiesWall.renderGraffiti();
  };

  FrankiesWall.importFiles = async function importFiles(files) {
    const el = FrankiesWall.el;
    const audioFiles = files.filter(FrankiesWall.isAudioFile);
    if (!audioFiles.length) {
      el.nowNote.textContent = "No audio files found in that selection.";
      return;
    }
    for (const file of audioFiles) {
      const catalogMatch = FrankiesWall.findCatalogByFileName(file.name);
      const id = catalogMatch?.id ?? FrankiesWall.uid();
      const existing = FrankiesWall.state.library.tracks.find((t) => t.id === id);
      const meta = existing ?? {
        id,
        title: catalogMatch?.title ?? FrankiesWall.titleFromFileName(file.name),
        artist: catalogMatch?.artist ?? "",
        fileName: file.name,
        mimeType: file.type || "audio/*",
        size: file.size,
        file: catalogMatch ? FrankiesWall.normalizeCatalogPath(catalogMatch.file) : null,
        bands: catalogMatch?.artist ? [catalogMatch.artist] : [],
        people: catalogMatch?.artist === "Drew" ? ["Drew"] : [],
        instruments: catalogMatch?.instrument ? [catalogMatch.instrument] : [],
        instrument: catalogMatch?.instrument || "",
        modes: [],
        vibes: catalogMatch?.vibe
          ? [catalogMatch.vibe]
          : catalogMatch?.vibes || [],
        notes: "",
        coverDataUrl: null,
        addedAt: Date.now(),
      };
      meta.fileName = file.name;
      meta.mimeType = file.type || meta.mimeType || "audio/*";
      meta.size = file.size;
      FrankiesWall.syncTrackInstrument(meta);
      if (!existing) FrankiesWall.state.library.tracks.unshift(meta);
      FrankiesWall.revokeUrl(id);
      FrankiesWall.session.sessionFiles.set(id, file);
      FrankiesWall.ensureBlobUrl(id);
    }
    await FrankiesWall.saveLibrary();
    FrankiesWall.renderAll();
    el.nowNote.textContent = `Imported ${audioFiles.length} local track${audioFiles.length === 1 ? "" : "s"}. Tag them on the wall.`;
  };

  FrankiesWall.bindInstrumentFilter = function bindInstrumentFilter() {
    document.querySelectorAll("#instrumentFilter button[data-instrument]").forEach((btn) => {
      btn.addEventListener("click", () => {
        FrankiesWall.filterByInstrument(btn.getAttribute("data-instrument"));
      });
    });
    FrankiesWall.setInstrumentFilterUi(FrankiesWall.state.instrumentFilter);
  };

  FrankiesWall.bindVibeFilter = function bindVibeFilter() {
    document.querySelectorAll("#vibeFilter button[data-vibe]").forEach((btn) => {
      btn.addEventListener("click", () => {
        FrankiesWall.filterByVibe(btn.getAttribute("data-vibe"));
      });
    });
    FrankiesWall.setVibeFilterUi(FrankiesWall.state.vibeFilter);
  };

  FrankiesWall.bindUi = function bindUi() {
    const el = FrankiesWall.el;

    document.querySelectorAll(".view-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const view = btn.getAttribute("data-view");
        if (view === "library" || view === "wall" || view === "moms-smile") {
          FrankiesWall.setView(view);
        }
      });
    });

    el.btnClearFilter.addEventListener("click", () => {
      FrankiesWall.state.activeFilter = null;
      FrankiesWall.renderAll();
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
          for (const h of handles) files.push(await h.getFile());
          await FrankiesWall.importFiles(files);
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
              if (FrankiesWall.isAudioFile(file)) files.push(file);
            }
          }
          await FrankiesWall.importFiles(files);
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
      await FrankiesWall.importFiles(files);
    });

    el.folderInput.addEventListener("change", async () => {
      const files = Array.from(el.folderInput.files || []);
      el.folderInput.value = "";
      await FrankiesWall.importFiles(files);
    });

    el.btnCloseEdit.addEventListener("click", FrankiesWall.closeEdit);

    el.tagForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const id = el.editId.value;
      const track = FrankiesWall.state.library.tracks.find((t) => t.id === id);
      if (!track) return;
      const { readChecks, readFileAsDataUrl } = FrankiesWall.dom;
      track.title = el.editTitle.value.trim() || track.title;
      track.notes = el.editNotes.value.trim();
      track.bands = readChecks(el.editBands);
      track.places = readChecks(el.editPlaces);
      track.people = readChecks(el.editPeople);
      track.instruments = readChecks(el.editInstruments);
      track.modes = readChecks(el.editModes);
      track.vibes = readChecks(el.editVibes);
      track.artist = track.bands[0] || track.artist || "";
      FrankiesWall.syncTrackInstrument(track);
      const coverFile = el.editCover.files && el.editCover.files[0];
      if (coverFile && coverFile.type.startsWith("image/")) {
        try {
          track.coverDataUrl = await readFileAsDataUrl(coverFile);
        } catch {
          /* keep cover */
        }
      }
      await FrankiesWall.saveLibrary();
      FrankiesWall.closeEdit();
      if (FrankiesWall.state.currentTrack === id) FrankiesWall.updateNowPlaying(track);
      FrankiesWall.renderAll();
    });

    el.btnRemoveTrack.addEventListener("click", async () => {
      const id = el.editId.value;
      FrankiesWall.state.library.tracks = FrankiesWall.state.library.tracks.filter(
        (t) => t.id !== id
      );
      FrankiesWall.revokeUrl(id);
      FrankiesWall.session.sessionFiles.delete(id);
      if (FrankiesWall.state.currentTrack === id) {
        FrankiesWall.setCurrentTrack?.(null);
        FrankiesWall.setIsPlaying?.(false);
        el.audio.removeAttribute("src");
        el.audio.load();
        el.nowTitle.textContent = "Nothing queued";
        el.nowNote.textContent = "Import your recordings to start the wall.";
        el.nowTags.innerHTML = "";
        el.coverArt.hidden = true;
        el.coverFallback.hidden = false;
        el.btnPlay.textContent = "▶";
      }
      await FrankiesWall.saveLibrary();
      FrankiesWall.closeEdit();
      FrankiesWall.renderAll();
    });
  };
})(typeof window !== "undefined" ? window : globalThis);
