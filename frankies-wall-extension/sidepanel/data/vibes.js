/**
 * Metadata — vibes (honor your sessions on the wall).
 */
(function initVibes(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.VIBES = [
    "Mom's Smile",
    "River Breeze",
    "fight & focus",
    "late night",
    "practice",
    "live",
    "studio",
  ];
})(typeof window !== "undefined" ? window : globalThis);
