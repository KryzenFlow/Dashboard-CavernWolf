/**
 * Rendering — now playing + BMX rail transport.
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
      ...track.vibes.map((v) => ({ v, accent: v === "Mom's Smile" })),
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

  FrankiesWall.bindTransport = function bindTransport() {
    const el = FrankiesWall.el;
    const { formatTime } = FrankiesWall.dom;

    el.btnPlay.addEventListener("click", async () => {
      if (!el.audio.src) {
        const list = FrankiesWall.filteredTracks();
        const playable = list.find((t) => FrankiesWall.session.sessionFiles.has(t.id));
        if (playable) await FrankiesWall.playTrack(playable.id);
        else if (list.length) await FrankiesWall.playTrack(list[0].id);
        return;
      }
      if (el.audio.paused) {
        try {
          await el.audio.play();
          el.btnPlay.textContent = "❚❚";
        } catch {
          /* autoplay blocked */
        }
      } else {
        el.audio.pause();
        el.btnPlay.textContent = "▶";
      }
    });

    el.btnPrev.addEventListener("click", () => FrankiesWall.playRelative(-1));
    el.btnNext.addEventListener("click", () => FrankiesWall.playRelative(1));

    el.audio.addEventListener("timeupdate", FrankiesWall.updateProgress);
    el.audio.addEventListener("loadedmetadata", FrankiesWall.updateProgress);

    el.audio.addEventListener("ended", () => {
      el.btnPlay.textContent = "▶";
      FrankiesWall.setTuningForkPlaying(false);
      FrankiesWall.playRelative(1);
    });
    el.audio.addEventListener("play", () => {
      el.btnPlay.textContent = "❚❚";
      FrankiesWall.setTuningForkPlaying(true);
    });
    el.audio.addEventListener("pause", () => {
      el.btnPlay.textContent = "▶";
      FrankiesWall.setTuningForkPlaying(false);
    });

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
      const dur = el.audio.duration || 0;
      if (dur > 0) {
        el.audio.currentTime = (Number(el.seek.value) / 1000) * dur;
      }
      FrankiesWall.state.seeking = false;
    });
  };
})(typeof window !== "undefined" ? window : globalThis);
