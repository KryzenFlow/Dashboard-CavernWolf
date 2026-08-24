/**
 * Story filters — expand anytime by adding entries here.
 *
 * Each filter can match track tags (instruments, modes, vibes, people)
 * or use built-in rules (mixedInstruments, momMode).
 *
 * @typedef {object} StoryFilterDef
 * @property {string} id
 * @property {string} label
 * @property {string} [hint] tooltip for the library bar
 * @property {string[]} [instruments]
 * @property {string[]} [modes]
 * @property {string[]} [vibes]
 * @property {string[]} [people]
 * @property {boolean} [mixedInstruments]
 * @property {boolean} [momMode]
 */

(function initStoryFilters(global) {
  /** @type {StoryFilterDef[]} */
  const STORY_FILTERS = [
    { id: "all", label: "All", hint: "Every track in your library" },
    {
      id: "electric",
      label: "Electric",
      hint: "Electric guitar and amp tones",
      instruments: ["electric"],
    },
    {
      id: "bass",
      label: "Bass",
      hint: "Bass lines and low-end riffs",
      instruments: ["bass"],
    },
    {
      id: "sax",
      label: "Sax",
      hint: "Sax takes and horn sessions",
      instruments: ["sax"],
    },
    {
      id: "mixed",
      label: "Mixed",
      hint: "Multi-instrument or blended sessions",
      mixedInstruments: true,
      modes: ["mixed"],
    },
    {
      id: "live",
      label: "Live",
      hint: "Stage, room, or field recordings",
      modes: ["live"],
      vibes: ["live"],
    },
    {
      id: "studio",
      label: "Studio",
      hint: "Polished takes and desk sessions",
      modes: ["studio"],
      vibes: ["studio"],
    },
    {
      id: "mom_mode",
      label: "Mom Mode",
      hint: "Mom's Smile — warmth, sax, and center",
      momMode: true,
      modes: ["mom_mode"],
    },
  ];

  /** Tag presets for the Story sidebar + tag editor (add ids here as you grow). */
  const STORY_MODE_PRESETS = ["live", "studio", "mixed", "mom_mode"];

  /**
   * @param {{ instruments?: string[], modes?: string[], vibes?: string[], people?: string[] }} track
   * @param {string} filterId
   */
  function trackMatchesStoryFilter(track, filterId) {
    if (!filterId || filterId === "all") return true;

    const def = STORY_FILTERS.find((f) => f.id === filterId);
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

    if (def.mixedInstruments) {
      if (instruments.length > 1 || instruments.includes("mixed")) return true;
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
  }

  /**
   * Map a sidebar tag click to a story filter id when it aligns.
   * @param {string} kind
   * @param {string} value
   * @returns {string | null}
   */
  function storyFilterIdForTag(kind, value) {
    for (const def of STORY_FILTERS) {
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
  }

  global.STORY_FILTERS = STORY_FILTERS;
  global.STORY_MODE_PRESETS = STORY_MODE_PRESETS;
  global.trackMatchesStoryFilter = trackMatchesStoryFilter;
  global.storyFilterIdForTag = storyFilterIdForTag;
})(typeof window !== "undefined" ? window : globalThis);
