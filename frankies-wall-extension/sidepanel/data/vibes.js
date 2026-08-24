/**
 * Metadata — vibe ids (catalog) ↔ wall labels (UI).
 */
(function initVibes(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  /** @type {Record<string, string>} */
  FrankiesWall.VIBE_BY_ID = {
    mom_smile: "Mom's Smile",
    river_breeze: "River Breeze",
    fight_focus: "fight & focus",
    late_night: "late night",
    practice: "practice",
    live: "live",
    studio: "studio",
  };

  FrankiesWall.VIBES = Object.values(FrankiesWall.VIBE_BY_ID);

  FrankiesWall.resolveVibeLabel = function resolveVibeLabel(vibe) {
    if (!vibe) return null;
    return FrankiesWall.VIBE_BY_ID[vibe] || vibe;
  };

  FrankiesWall.resolveVibeId = function resolveVibeId(labelOrId) {
    if (!labelOrId) return null;
    if (FrankiesWall.VIBE_BY_ID[labelOrId]) return labelOrId;
    const entry = Object.entries(FrankiesWall.VIBE_BY_ID).find(([, label]) => label === labelOrId);
    return entry ? entry[0] : null;
  };

  FrankiesWall.catalogVibesToLabels = function catalogVibesToLabels(catalog) {
    const label = FrankiesWall.resolveVibeLabel(catalog.vibe);
    return label ? [label] : catalog.vibes || [];
  };
})(typeof window !== "undefined" ? window : globalThis);
