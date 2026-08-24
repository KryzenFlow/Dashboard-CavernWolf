/**
 * Metadata — vibes. My soul encoded into data.
 *
 * export const vibes = ["river_breeze", "fight_focus", "build_repair", "mom_smile"];
 */
(function initVibes(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  const vibes = ["river_breeze", "fight_focus", "build_repair", "mom_smile"];

  global.vibes = vibes;

  /** @type {Record<string, string>} */
  FrankiesWall.VIBE_BY_ID = {
    river_breeze: "River Breeze",
    fight_focus: "Fight & Focus",
    build_repair: "Build & Repair",
    mom_smile: "Mom's Smile",
  };

  FrankiesWall.VIBE_IDS = vibes;
  FrankiesWall.VIBES = vibes;

  FrankiesWall.resolveVibeLabel = function resolveVibeLabel(vibe) {
    if (!vibe) return null;
    return FrankiesWall.VIBE_BY_ID[vibe] || vibe.replace(/_/g, " ");
  };

  FrankiesWall.resolveVibeId = function resolveVibeId(labelOrId) {
    if (!labelOrId) return null;
    if (FrankiesWall.VIBE_BY_ID[labelOrId]) return labelOrId;
    const entry = Object.entries(FrankiesWall.VIBE_BY_ID).find(([, label]) => label === labelOrId);
    return entry ? entry[0] : null;
  };

  FrankiesWall.catalogVibesToTrackVibes = function catalogVibesToTrackVibes(catalog) {
    if (catalog.vibe) return [catalog.vibe];
    if (Array.isArray(catalog.vibes)) return catalog.vibes;
    return [];
  };
})(typeof window !== "undefined" ? window : globalThis);
