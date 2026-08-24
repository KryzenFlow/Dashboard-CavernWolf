/**
 * Utilities — filtering engine.
 */
(function initFilters(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.filterTracksByInstrument = function filterTracksByInstrument(tracks, instrument) {
    if (instrument === "all") return tracks;
    return tracks.filter((track) => track.instrument === instrument);
  };

  FrankiesWall.getTracksBeforeInstrumentFilter = function getTracksBeforeInstrumentFilter() {
    const { state } = FrankiesWall;
    let tracks = state.library.tracks.slice();

    if (state.currentView === "moms-smile") {
      tracks = tracks.filter((t) => FrankiesWall.trackMatchesStoryFilter(t, "mom_mode"));
    }
    if (state.storyFilter !== "all") {
      tracks = tracks.filter((t) => FrankiesWall.trackMatchesStoryFilter(t, state.storyFilter));
    }
    if (state.activeFilter) {
      const { kind, value } = state.activeFilter;
      tracks = tracks.filter((t) => {
        switch (kind) {
          case "bands":
            return t.bands.includes(value);
          case "places":
            return t.places.includes(value);
          case "people":
            return t.people.includes(value);
          case "instruments":
            return t.instruments.includes(value);
          case "modes":
            return t.modes.includes(value);
          case "vibes":
            return t.vibes.includes(value);
          default:
            return true;
        }
      });
    }
    return tracks;
  };

  FrankiesWall.filteredTracks = function filteredTracks() {
    return FrankiesWall.filterTracksByInstrument(
      FrankiesWall.getTracksBeforeInstrumentFilter(),
      FrankiesWall.state.instrumentFilter
    );
  };

  FrankiesWall.filterByInstrument = function filterByInstrument(instrument) {
    const ids = new Set(FrankiesWall.INSTRUMENT_FILTER_IDS);
    if (!ids.has(instrument)) return;

    FrankiesWall.state.instrumentFilter = instrument;
    FrankiesWall.setInstrumentFilterUi(instrument);

    const tracks = FrankiesWall.getTracksBeforeInstrumentFilter();
    let filtered;
    if (instrument === "all") {
      filtered = tracks;
    } else {
      filtered = tracks.filter((track) => track.instrument === instrument);
    }

    FrankiesWall.renderTrackList(filtered);
    FrankiesWall.updateLibraryHeading();
    FrankiesWall.renderSidebarTags();
  };

  global.filterTracksByInstrument = FrankiesWall.filterTracksByInstrument;
  global.filterByInstrument = FrankiesWall.filterByInstrument;
})(typeof window !== "undefined" ? window : globalThis);
