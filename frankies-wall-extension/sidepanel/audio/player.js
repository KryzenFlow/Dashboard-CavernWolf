/**
 * Audio layer — playback engine.
 * Handles: play · pause · scrub · volume · track URLs.
 */
(function initPlayer(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.VOLUME_KEY = "frankiesWallVolume";
  FrankiesWall.DEFAULT_VOLUME = 0.85;

  FrankiesWall.revokeUrl = function revokeUrl(id) {
    const url = FrankiesWall.session.blobUrls.get(id);
    if (url) {
      URL.revokeObjectURL(url);
      FrankiesWall.session.blobUrls.delete(id);
    }
  };

  FrankiesWall.ensureBlobUrl = function ensureBlobUrl(id) {
    if (FrankiesWall.session.blobUrls.has(id)) {
      return FrankiesWall.session.blobUrls.get(id);
    }
    const file = FrankiesWall.session.sessionFiles.get(id);
    if (!file) return null;
    const url = URL.createObjectURL(file);
    FrankiesWall.session.blobUrls.set(id, url);
    return url;
  };

  FrankiesWall.resolveTrackUrl = function resolveTrackUrl(id) {
    const blobUrl = FrankiesWall.ensureBlobUrl(id);
    if (blobUrl) return blobUrl;

    const track = FrankiesWall.state.library.tracks.find((t) => t.id === id);
    if (!track?.file) return null;

    try {
      return chrome.runtime.getURL(FrankiesWall.normalizeCatalogPath(track.file));
    } catch {
      return null;
    }
  };

  FrankiesWall.applyVolume = function applyVolume(level) {
    const el = FrankiesWall.el;
    if (!el?.audio) return;
    const clamped = Math.min(1, Math.max(0, level));
    FrankiesWall.state.volume = clamped;
    el.audio.volume = clamped;
    if (el.volume) {
      el.volume.value = String(Math.round(clamped * 100));
      el.volume.style.setProperty("--volume", `${clamped * 100}%`);
    }
  };

  FrankiesWall.setVolume = function setVolume(level) {
    FrankiesWall.applyVolume(level);
    try {
      chrome.storage.local.set({ [FrankiesWall.VOLUME_KEY]: FrankiesWall.state.volume });
    } catch {
      /* storage unavailable */
    }
  };

  FrankiesWall.loadVolume = async function loadVolume() {
    try {
      const data = await chrome.storage.local.get(FrankiesWall.VOLUME_KEY);
      const stored = data[FrankiesWall.VOLUME_KEY];
      if (typeof stored === "number" && !Number.isNaN(stored)) {
        FrankiesWall.applyVolume(stored);
        return;
      }
    } catch {
      /* fall through */
    }
    FrankiesWall.applyVolume(FrankiesWall.DEFAULT_VOLUME);
  };

  FrankiesWall.syncPlayButton = function syncPlayButton() {
    const el = FrankiesWall.el;
    if (!el?.btnPlay || !el?.audio) return;
    FrankiesWall.setIsPlaying?.(!el.audio.paused);
  };

  FrankiesWall.pauseTrack = function pauseTrack() {
    const el = FrankiesWall.el;
    if (!el?.audio?.src) return;
    el.audio.pause();
    FrankiesWall.setIsPlaying?.(false);
  };

  FrankiesWall.togglePlay = async function togglePlay() {
    const el = FrankiesWall.el;
    if (!el?.audio) return;

    if (!el.audio.src) {
      const list = FrankiesWall.filteredTracks();
      const playable = list.find((t) => FrankiesWall.session.sessionFiles.has(t.id));
      if (playable) await FrankiesWall.playTrack(playable.id);
      else if (list.length) await FrankiesWall.playTrack(list[0].id);
      return;
    }

    if (el.audio.paused) {
      try {
        await el.audio.play();
        FrankiesWall.setIsPlaying?.(true);
        FrankiesWall.startWaveform?.();
      } catch {
        /* autoplay blocked */
      }
    } else {
      FrankiesWall.pauseTrack();
    }
  };

  FrankiesWall.seekToRatio = function seekToRatio(ratio) {
    const el = FrankiesWall.el;
    const dur = el?.audio?.duration || 0;
    if (dur <= 0) return;
    const clamped = Math.min(1, Math.max(0, ratio));
    el.audio.currentTime = dur * clamped;
    FrankiesWall.updateProgress?.();
  };

  FrankiesWall.playTrack = async function playTrack(id) {
    const el = FrankiesWall.el;
    const track = FrankiesWall.state.library.tracks.find((t) => t.id === id);
    if (!track) return;

    const url = FrankiesWall.resolveTrackUrl(id);
    if (!url) {
      el.nowTitle.textContent = track.title;
      el.nowNote.textContent = track.file
        ? `Add ${track.fileName} under the extension music/ folder, or re-import to play.`
        : "Metadata is saved, but the audio file isn’t in this session. Re-import the file or folder to play.";
      FrankiesWall.setCurrentTrack?.(id);
      FrankiesWall.updateNowPlaying?.(track);
      return;
    }

    FrankiesWall.setCurrentTrack?.(id);
    el.audio.src = url;
    FrankiesWall.applyVolume(FrankiesWall.state.volume ?? FrankiesWall.DEFAULT_VOLUME);

    try {
      await el.audio.play();
      FrankiesWall.setIsPlaying?.(true);
      FrankiesWall.attachWaveformSource?.();
      FrankiesWall.startWaveform?.();
    } catch {
      FrankiesWall.setIsPlaying?.(false);
    }

    FrankiesWall.updateNowPlaying?.(track);
    FrankiesWall.renderLibrary?.();
  };

  FrankiesWall.playRelative = function playRelative(delta) {
    const list = FrankiesWall.filteredTracks();
    if (!list.length) return;
    let idx = list.findIndex((t) => t.id === FrankiesWall.state.currentTrack);
    if (idx < 0) idx = 0;
    else idx = (idx + delta + list.length) % list.length;
    FrankiesWall.playTrack(list[idx].id);
  };

  FrankiesWall.bindTransport = function bindTransport() {
    const el = FrankiesWall.el;
    const { formatTime } = FrankiesWall.dom;

    el.btnPlay.addEventListener("click", () => {
      void FrankiesWall.togglePlay();
    });

    el.btnPrev.addEventListener("click", () => FrankiesWall.playRelative(-1));
    el.btnNext.addEventListener("click", () => FrankiesWall.playRelative(1));

    el.audio.addEventListener("timeupdate", () => FrankiesWall.updateProgress?.());
    el.audio.addEventListener("loadedmetadata", () => FrankiesWall.updateProgress?.());

    el.audio.addEventListener("ended", () => {
      FrankiesWall.setIsPlaying?.(false);
      FrankiesWall.stopWaveform?.();
      FrankiesWall.playRelative(1);
    });

    el.audio.addEventListener("play", () => {
      FrankiesWall.setIsPlaying?.(true);
      FrankiesWall.startWaveform?.();
    });

    el.audio.addEventListener("pause", () => {
      FrankiesWall.setIsPlaying?.(false);
      FrankiesWall.stopWaveform?.();
    });

    el.seek.addEventListener("pointerdown", () => {
      FrankiesWall.state.seeking = true;
    });
    el.seek.addEventListener("pointerup", () => {
      FrankiesWall.state.seeking = false;
    });
    el.seek.addEventListener("input", () => {
      const dur = el.audio.duration || 0;
      const pct = Number(el.seek.value) / 1000;
      el.seek.style.setProperty("--progress", `${pct * 100}%`);
      if (dur > 0) el.timeCurrent.textContent = formatTime(dur * pct);
    });
    el.seek.addEventListener("change", () => {
      FrankiesWall.seekToRatio(Number(el.seek.value) / 1000);
      FrankiesWall.state.seeking = false;
    });

    if (el.volume) {
      el.volume.addEventListener("input", () => {
        const level = Number(el.volume.value) / 100;
        el.volume.style.setProperty("--volume", `${level * 100}%`);
        FrankiesWall.applyVolume(level);
      });
      el.volume.addEventListener("change", () => {
        FrankiesWall.setVolume(Number(el.volume.value) / 100);
      });
    }
  };

  global.playTrack = FrankiesWall.playTrack;
})(typeof window !== "undefined" ? window : globalThis);
