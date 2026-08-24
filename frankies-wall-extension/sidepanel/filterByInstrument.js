/**
 * Instrument filter engine — simple, clean.
 *
 *   filterByInstrument("sax");  // filters library.tracks and re-renders list
 *
 * @param {object[]} tracks
 * @param {string} instrument
 * @returns {object[]}
 */
function filterTracksByInstrument(tracks, instrument) {
  if (instrument === "all") {
    return tracks;
  }
  return tracks.filter((track) => track.instrument === instrument);
}

if (typeof window !== "undefined") {
  window.filterTracksByInstrument = filterTracksByInstrument;
}
