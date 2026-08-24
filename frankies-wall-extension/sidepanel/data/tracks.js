/**
 * Metadata layer — seed catalog.
 *
 * export const tracks = [
 *   {
 *     id: "bush_glycerine",
 *     title: "Glycerine",
 *     artist: "Bush",
 *     file: "/music/bush/glycerine.mp3",
 *     instrument: "electric",
 *     vibe: "river_breeze"
 *   },
 *   {
 *     id: "drew_sax_live_01",
 *     title: "Sax Live Recording",
 *     artist: "Drew",
 *     file: "/music/drew/sax_live_01.mp3",
 *     instrument: "sax",
 *     vibe: "mom_smile"
 *   }
 * ];
 */
(function initCatalogTracks(global) {
  const tracks = [
    {
      id: "bush_glycerine",
      title: "Glycerine",
      artist: "Bush",
      file: "/music/bush/glycerine.mp3",
      instrument: "electric",
      vibe: "river_breeze",
    },
    {
      id: "drew_sax_live_01",
      title: "Sax Live Recording",
      artist: "Drew",
      file: "/music/drew/sax_live_01.mp3",
      instrument: "sax",
      vibe: "mom_smile",
    },
  ];

  global.tracks = tracks;
  global.CATALOG_TRACKS = tracks;
})(typeof window !== "undefined" ? window : globalThis);
