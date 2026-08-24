/**
 * Rendering layer — track list UI.
 *
 * Renders filtered tracks from filters.js into #trackList.
 */
(function initTrackList(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.renderTrackList = function renderTrackList(list) {
    const container = document.getElementById("trackList");
    container.innerHTML = "";

    list.forEach((track) => {
      const item = document.createElement("div");
      item.className = "trackItem";
      const artist = track.artist || (track.bands && track.bands[0]) || "";
      item.textContent = `${track.title} — ${artist} (${track.instrument})`;
      item.dataset.id = track.id;
      if (track.id === FrankiesWall.state.currentTrack) {
        item.classList.add("is-playing");
      }
      item.addEventListener("click", () => {
        FrankiesWall.playTrack(track.id);
      });
      container.appendChild(item);
    });

    const empty = document.getElementById("library-empty");
    if (empty) empty.hidden = list.length > 0;
  };

  FrankiesWall.renderLibrary = function renderLibrary() {
    FrankiesWall.updateLibraryHeading?.();
    FrankiesWall.renderTrackList(FrankiesWall.filteredTracks());
  };

  global.renderTrackList = FrankiesWall.renderTrackList;
})(typeof window !== "undefined" ? window : globalThis);
