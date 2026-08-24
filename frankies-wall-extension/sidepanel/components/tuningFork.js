/**
 * TuningFork — resonance / center / alignment (phronesis in code)
 *
 * Geometry:
 * <svg viewBox="0 0 64 64">
 *   <path d="M20 10 v25 a12 12 0 0 0 24 0 v-25"
 *         fill="none" stroke="black" stroke-width="4"/>
 *   <line x1="32" y1="35" x2="32" y2="54"
 *         stroke="black" stroke-width="4"/>
 * </svg>
 *
 * Spec:
 * {
 *   "component": "TuningFork",
 *   "props": {
 *     "size": 32,
 *     "stroke": "#000",
 *     "strokeWidth": 2,
 *     "interactive": true,
 *     "onClick": "playTuningFork",
 *     "durationSeconds": 2
 *   },
 *   "meta": {
 *     "meaning": "Center — Find Your Tone",
 *     "origin": "Mom's polish and practical wisdom"
 *   }
 * }
 *
 * Equivalent:
 *   <button onClick={() => playTuningFork()}>Tuning Fork</button>
 *
 * Placements: logo (top-left) · art (Now Playing) · rail (BMX grind bar)
 */
(function initTuningForkComponent(global) {
  const META = {
    meaning: "Center — Find Your Tone",
    origin: "Mom's polish and practical wisdom",
  };

  const DEFAULT_PROPS = {
    size: 32,
    stroke: "#000",
    strokeWidth: 2,
    interactive: true,
    onClick: "playTuningFork",
    durationSeconds: 2,
    meaning: META.meaning,
    origin: META.origin,
    placement: "default",
  };

  const PLACEMENT_CLASS = {
    logo: "tuning-fork--logo",
    art: "tuning-fork--art",
    rail: "tuning-fork--rail",
    default: "",
  };

  function createSvg(props) {
    // #000 → currentColor so the fork reads on the dark Frankie's wall
    const strokeColor = props.stroke === "#000" ? "currentColor" : props.stroke;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "tuning-fork-svg");
    svg.setAttribute("viewBox", "0 0 64 64");
    svg.setAttribute("fill", "none");
    svg.setAttribute("width", String(props.size));
    svg.setAttribute("height", String(props.size));
    svg.setAttribute("aria-hidden", "true");

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", "M20 10 v25 a12 12 0 0 0 24 0 v-25");
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", strokeColor);
    path.setAttribute("stroke-width", String(props.strokeWidth));
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("stroke-linejoin", "round");

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", "32");
    line.setAttribute("y1", "35");
    line.setAttribute("x2", "32");
    line.setAttribute("y2", "54");
    line.setAttribute("stroke", strokeColor);
    line.setAttribute("stroke-width", String(props.strokeWidth));
    line.setAttribute("stroke-linecap", "round");

    svg.append(path, line);
    return svg;
  }

  /**
   * Resolve onClick prop like React:
   *   onClick={() => playTuningFork()}
   * or string name "playTuningFork" → window.playTuningFork(durationSeconds)
   */
  function bindClick(root, merged) {
    if (!merged.interactive) return;

    const duration =
      Number(merged.durationSeconds) > 0
        ? Number(merged.durationSeconds)
        : DEFAULT_PROPS.durationSeconds;

    root.dataset.durationSeconds = String(duration);

    root.addEventListener("click", () => {
      if (typeof merged.onClick === "function") {
        merged.onClick(duration);
        return;
      }
      const name =
        typeof merged.onClick === "string" ? merged.onClick : "playTuningFork";
      const handler = global[name];
      if (typeof handler === "function") {
        Promise.resolve(handler(duration)).catch(() => {});
      }
    });
  }

  /**
   * @param {Partial<typeof DEFAULT_PROPS> & { onClick?: string | ((duration?: number) => void) }} props
   * @returns {HTMLElement}
   */
  function create(props = {}) {
    const merged = { ...DEFAULT_PROPS, ...props };
    const placementClass = PLACEMENT_CLASS[merged.placement] || PLACEMENT_CLASS.default;

    const root = document.createElement(merged.interactive ? "button" : "div");
    if (merged.interactive) {
      root.type = "button";
    }
    root.className = ["tuning-fork-icon", placementClass].filter(Boolean).join(" ");
    root.dataset.component = "TuningFork";
    root.dataset.tuningFork = "true";
    root.dataset.meaning = merged.meaning;
    root.dataset.origin = merged.origin;
    if (merged.interactive) {
      const handlerName =
        typeof merged.onClick === "string" ? merged.onClick : "playTuningFork";
      root.dataset.onclick = handlerName;
    }

    const tip = `${merged.meaning}\n${merged.origin}`;
    root.title = tip;
    root.setAttribute(
      "aria-label",
      merged.interactive
        ? `${merged.meaning}. ${merged.origin}. Play A440 tuning fork.`
        : `${merged.meaning}. ${merged.origin}.`
    );
    root.style.width = `${merged.size}px`;
    root.style.height = `${merged.size}px`;
    root.style.color = merged.stroke === "#000" ? "var(--ink)" : merged.stroke;

    root.appendChild(createSvg(merged));
    bindClick(root, merged);

    return root;
  }

  /** Mount into `[data-tuning-fork-mount="logo|art|rail"]` slots. */
  function mountAll(getPropsForPlacement) {
    document.querySelectorAll("[data-tuning-fork-mount]").forEach((slot) => {
      const placement = slot.dataset.tuningForkMount || "default";
      const extra =
        typeof getPropsForPlacement === "function"
          ? getPropsForPlacement(placement)
          : {};
      slot.replaceChildren(create({ placement, ...extra }));
    });
  }

  global.TuningFork = {
    META,
    DEFAULT_PROPS,
    create,
    mountAll,
  };

  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});
  let forkStopTimer = null;

  FrankiesWall.setTuningForkPlaying = function setTuningForkPlaying(playing) {
    FrankiesWall.setIsPlaying?.(playing);
  };

  FrankiesWall.pulseTuningForkIcons = function pulseTuningForkIcons(durationMs = 2000) {
    FrankiesWall.setTuningForkActive?.(true);
    const pulseTargets = document.querySelectorAll("[data-tuning-fork], #tuningForkBtn");
    pulseTargets.forEach((node) => node.classList.add("is-forking"));
    if (forkStopTimer) clearTimeout(forkStopTimer);
    forkStopTimer = setTimeout(() => {
      pulseTargets.forEach((node) => node.classList.remove("is-forking"));
      FrankiesWall.setTuningForkActive?.(false);
    }, durationMs);
  };

  FrankiesWall.initTuningFork = function initTuningFork() {
    const playDropIn = global.playTuningFork;
    global.playTuningFork = function playTuningForkWrapped(duration = 2) {
      if (typeof playDropIn === "function") playDropIn(duration);
      FrankiesWall.pulseTuningForkIcons(duration * 1000);
    };

    const meta = global.TuningFork.META;
    global.TuningFork.mountAll((placement) => {
      const sizeByPlacement = { logo: 28, art: 32, rail: 22 };
      return {
        size: sizeByPlacement[placement] ?? global.TuningFork.DEFAULT_PROPS.size,
        stroke: global.TuningFork.DEFAULT_PROPS.stroke,
        strokeWidth: global.TuningFork.DEFAULT_PROPS.strokeWidth,
        interactive: true,
        onClick: "playTuningFork",
        durationSeconds: 2,
        meaning: meta.meaning,
        origin: meta.origin,
      };
    });

    const forkBtn = document.getElementById("tuningForkBtn");
    if (forkBtn && forkBtn.dataset.listenerBound !== "1") {
      forkBtn.dataset.listenerBound = "1";
      forkBtn.addEventListener("click", () => global.playTuningFork(2));
    }

    const logoMeaning = document.querySelector(".tuning-fork-meaning--logo");
    if (logoMeaning) logoMeaning.textContent = meta.meaning;
  };
})(window);
