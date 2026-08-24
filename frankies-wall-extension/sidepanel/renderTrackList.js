/**
 * Simple track list render — load before sidepanel-app.js or call from filterByInstrument.
 *
 * @param {object[]} list
 */
function renderTrackList(list) {
  const container = document.getElementById("trackList");
  container.innerHTML = "";

  list.forEach((track) => {
    const item = document.createElement("div");
    item.className = "trackItem";
    const artist = track.artist || (track.bands && track.bands[0]) || "";
    item.textContent = `${track.title} — ${artist} (${track.instrument})`;
    item.dataset.id = track.id;
    item.addEventListener("click", () => {
      if (typeof window.playTrack === "function") {
        window.playTrack(track.id);
      }
    });
    container.appendChild(item);
  });

  const empty = document.getElementById("library-empty");
  if (empty) {
    empty.hidden = list.length > 0;
  }
}

if (typeof window !== "undefined") {
  window.renderTrackList = renderTrackList;
}
