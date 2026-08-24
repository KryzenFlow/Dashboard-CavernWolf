/**
 * Rendering layer — now playing UI.
 *
 * Album art · metadata · chips · BMX grind bar animation.
 * Tuning fork icon mounts live here (via tuningFork.js).
 *
 * Scrubbing animates the grind bar; audio seek logic is in audio/player.js.
 */
(function initNowPlaying(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.updateNowPlaying = function updateNowPlaying(track) {
    const el = FrankiesWall.el;
    const { formatModeLabel } = FrankiesWall.dom;

    el.nowTitle.textContent = track.title;
    if (track.notes) {
      el.nowNote.textContent = track.notes;
    } else {
      const band = track.bands[0];
      const place = track.places[0] || "Frankies wall";
      el.nowNote.textContent = band
        ? `Playing: ${band} — ${track.title} (${place}, late night)`
        : `Playing: ${track.title} (${place})`;
    }

    el.nowTags.innerHTML = "";
    const chips = [
      ...track.bands.map((v) => ({ v, accent: false })),
      ...track.instruments.map((v) => ({ v, accent: false })),
      ...track.modes.map((v) => ({ v: formatModeLabel(v), accent: v === "mom_mode" })),
      ...track.vibes.map((v) => ({
        v: FrankiesWall.resolveVibeLabel(v),
        accent: v === "mom_smile",
      })),
      ...track.people.filter((p) => p === "Mom").map((v) => ({ v, accent: true })),
    ];
    for (const chip of chips.slice(0, 8)) {
      const span = document.createElement("span");
      span.className = "chip" + (chip.accent ? " accent" : "");
      span.textContent = chip.v;
      el.nowTags.appendChild(span);
    }

    if (track.coverDataUrl) {
      el.coverArt.src = track.coverDataUrl;
      el.coverArt.hidden = false;
      el.coverFallback.hidden = true;
    } else {
      el.coverArt.removeAttribute("src");
      el.coverArt.hidden = true;
      el.coverFallback.hidden = false;
    }
  };

  FrankiesWall.updateProgress = function updateProgress() {
    const el = FrankiesWall.el;
    const { formatTime } = FrankiesWall.dom;
    const a = el.audio;
    const dur = a.duration || 0;
    const cur = a.currentTime || 0;
    el.timeCurrent.textContent = formatTime(cur);
    el.timeDuration.textContent = formatTime(dur);
    if (!FrankiesWall.state.seeking && dur > 0) {
      const pct = (cur / dur) * 1000;
      el.seek.value = String(Math.round(pct));
      el.seek.style.setProperty("--progress", `${(cur / dur) * 100}%`);
    }
  };

  /** BMX grind bar — scrub preview + progress animation. */
  FrankiesWall.bindGrindBar = function bindGrindBar() {
    const el = FrankiesWall.el;
    const { formatTime } = FrankiesWall.dom;
    if (!el?.seek) return;

    el.seek.addEventListener("pointerdown", () => {
      FrankiesWall.state.seeking = true;
    });
    el.seek.addEventListener("pointerup", () => {
      FrankiesWall.state.seeking = false;
    });
    el.seek.addEventListener("input", () => {
      const dur = el.audio.duration || 0;
      const pct = Number(el.seek.value) / 1000;
      el.seek.style.setProperty("--progress", `${pct * 100}%`);
      if (dur > 0) el.timeCurrent.textContent = formatTime(dur * pct);
    });
    el.seek.addEventListener("change", () => {
      FrankiesWall.seekToRatio?.(Number(el.seek.value) / 1000);
      FrankiesWall.state.seeking = false;
    });
  };
})(typeof window !== "undefined" ? window : globalThis);
