/**
 * Frankie's Wall seed catalog — drop matching MP3s under music/ in the extension folder.
 * Paths resolve via chrome.runtime.getURL (e.g. music/bush/glycerine.mp3).
 */
(function initCatalogTracks(global) {
  /** @type {CatalogTrack[]} */
  const tracks = [
    {
      id: "bush_glycerine",
      title: "Glycerine",
      artist: "Bush",
      file: "/music/bush/glycerine.mp3",
      instrument: "electric",
    },
    {
      id: "soundgarden_black_hole_sun",
      title: "Black Hole Sun",
      artist: "Soundgarden",
      file: "/music/soundgarden/black_hole_sun.mp3",
      instrument: "electric",
    },
    {
      id: "drew_sax_live_01",
      title: "Sax Live Recording",
      artist: "Drew",
      file: "/music/drew/sax_live_01.mp3",
      instrument: "sax",
    },
    {
      id: "drew_bass_riff_02",
      title: "Bass Riff",
      artist: "Drew",
      file: "/music/drew/bass_riff_02.mp3",
      instrument: "bass",
    },
  ];

  global.CATALOG_TRACKS = tracks;
})(typeof window !== "undefined" ? window : globalThis);
