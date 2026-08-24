/**
 * Metadata — tag presets, story filters, wall dates.
 */
(function initTags(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.TAG_PRESETS = {
    bands: [
      "Bush",
      "Soundgarden",
      "Radiohead",
      "Collective Soul",
      "Skynyrd",
      "Guns N' Roses",
      "Pearl Jam",
      "Alice in Chains",
      "Nirvana",
      "Stone Temple Pilots",
    ],
    places: ["Toledo", "Promenade Park", "Frankies", "East Side Nights"],
    people: ["Mom", "Son", "Solo", "With Friends", "Drew"],
    instruments: ["sax", "electric", "bass", "drums", "vocals", "acoustic", "mixed"],
    modes: ["live", "studio", "mixed", "mom_mode"],
  };

  FrankiesWall.WALL_DATES = {
    Bush: "'95",
    Soundgarden: "'94",
    Radiohead: "'97",
    "Collective Soul": "'94",
    Skynyrd: "'77",
    "Guns N' Roses": "'91",
    "Pearl Jam": "'91",
    "Alice in Chains": "'92",
    Nirvana: "'91",
    "Stone Temple Pilots": "'92",
    Toledo: "home",
    "Promenade Park": "summer",
    Frankies: "nights",
    "East Side Nights": "forever",
    Mom: "♡",
    Son: "growin'",
    Solo: "alone",
    "With Friends": "crew",
  };

  FrankiesWall.STORY_FILTERS = [
    { id: "all", label: "All", hint: "Every track in your library" },
    { id: "electric", label: "Electric", instruments: ["electric"] },
    { id: "bass", label: "Bass", instruments: ["bass"] },
    { id: "sax", label: "Sax", instruments: ["sax"] },
    { id: "mixed", label: "Mixed", mixedInstruments: true, modes: ["mixed"] },
    { id: "live", label: "Live", modes: ["live"], vibes: ["live"] },
    { id: "studio", label: "Studio", modes: ["studio"], vibes: ["studio"] },
    { id: "mom_mode", label: "Mom Mode", momMode: true, modes: ["mom_mode"] },
  ];

  FrankiesWall.INSTRUMENT_FILTER_IDS = ["all", "electric", "bass", "sax", "mixed"];

  FrankiesWall.trackMatchesStoryFilter = function trackMatchesStoryFilter(track, filterId) {
    if (!filterId || filterId === "all") return true;
    const def = FrankiesWall.STORY_FILTERS.find((f) => f.id === filterId);
    if (!def) return true;

    const instruments = track.instruments || [];
    const modes = track.modes || [];
    const vibes = track.vibes || [];
    const people = track.people || [];

    if (def.momMode) {
      return (
        modes.includes("mom_mode") ||
        vibes.includes("Mom's Smile") ||
        people.includes("Mom") ||
        instruments.includes("sax")
      );
    }
    if (def.mixedInstruments && (instruments.length > 1 || instruments.includes("mixed"))) {
      return true;
    }

    const checks = [];
    if (def.instruments?.length) {
      checks.push(() => def.instruments.some((v) => instruments.includes(v)));
    }
    if (def.modes?.length) {
      checks.push(() => def.modes.some((v) => modes.includes(v)));
    }
    if (def.vibes?.length) {
      checks.push(() => def.vibes.some((v) => vibes.includes(v)));
    }
    if (def.people?.length) {
      checks.push(() => def.people.some((v) => people.includes(v)));
    }
    if (def.mixedInstruments) {
      checks.push(() => modes.includes("mixed"));
    }
    if (!checks.length) return true;
    return checks.some((fn) => fn());
  };

  FrankiesWall.storyFilterIdForTag = function storyFilterIdForTag(kind, value) {
    for (const def of FrankiesWall.STORY_FILTERS) {
      if (def.id === "all") continue;
      if (kind === "instruments" && def.instruments?.includes(value)) return def.id;
      if (kind === "modes" && def.modes?.includes(value)) return def.id;
      if (kind === "vibes" && def.vibes?.includes(value)) return def.id;
      if (kind === "people" && def.people?.includes(value)) return def.id;
      if (value === "mixed" && def.mixedInstruments) return def.id;
      if (value === "mom_mode" && def.momMode) return def.id;
      if (value === "Mom" && def.momMode) return def.id;
    }
    return null;
  };
})(typeof window !== "undefined" ? window : globalThis);
