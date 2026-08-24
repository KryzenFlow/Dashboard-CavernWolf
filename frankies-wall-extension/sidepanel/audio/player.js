/**
 * Audio — local playback engine.
 */
(function initPlayer(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

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
      FrankiesWall.updateNowPlaying(track);
      return;
    }

    FrankiesWall.state.currentId = id;
    el.audio.src = url;
    try {
      await el.audio.play();
      el.btnPlay.textContent = "❚❚";
    } catch {
      el.btnPlay.textContent = "▶";
    }
    FrankiesWall.updateNowPlaying(track);
    FrankiesWall.renderLibrary();
  };

  FrankiesWall.playRelative = function playRelative(delta) {
    const list = FrankiesWall.filteredTracks();
    if (!list.length) return;
    let idx = list.findIndex((t) => t.id === FrankiesWall.state.currentId);
    if (idx < 0) idx = 0;
    else idx = (idx + delta + list.length) % list.length;
    FrankiesWall.playTrack(list[idx].id);
  };

  global.playTrack = FrankiesWall.playTrack;
})(typeof window !== "undefined" ? window : globalThis);
