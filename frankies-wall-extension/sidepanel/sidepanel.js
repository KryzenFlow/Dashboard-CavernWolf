/**
 * Frankie's Wall — 6-layer sidepanel orchestrator.
 *
 * UI · State · Audio · Metadata · Rendering · Utilities
 * Pure JS + CSS + HTML. No framework.
 */
(function bootFrankiesWall() {
  "use strict";

  const FW = window.FrankiesWall;

  FW.el = {
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
    trackList: document.getElementById("trackList"),
    libraryEmpty: document.getElementById("library-empty"),
    libraryHeading: document.getElementById("library-heading"),
    btnClearFilter: document.getElementById("btn-clear-filter"),
    instrumentFilter: document.getElementById("instrumentFilter"),
    vibeFilter: document.getElementById("vibeFilter"),
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
    volume: document.getElementById("volume"),
    waveform: document.getElementById("waveform"),
    btnWaveform: document.getElementById("btn-waveform"),
    seek: document.getElementById("seek"),
    timeCurrent: document.getElementById("time-current"),
    timeDuration: document.getElementById("time-duration"),
    audio: document.getElementById("audio"),
  };

  FW.renderStoryFilterBar();
  FW.bindInstrumentFilter();
  FW.bindVibeFilter();
  FW.bindTransport();
  FW.bindWaveform();
  FW.bindUi();
  FW.initTuningFork();

  void FW.loadVolume().then(() =>
    FW.loadLibrary().then(async () => {
      const catalogAdded = FW.mergeCatalogIntoLibrary();
      if (catalogAdded) await FW.saveLibrary();
      FW.renderAll();
      if (FW.state.library.tracks.length) {
        const hasBundled = FW.state.library.tracks.some((t) => t.file);
        FW.el.nowNote.textContent = hasBundled
          ? "Catalog loaded. Bundled tracks play from music/ — imports override for this session."
          : "Tags restored. Re-import audio files to play — metadata stayed local.";
      }
    })
  );
})();
