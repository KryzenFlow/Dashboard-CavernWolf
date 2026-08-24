/**
 * TuningFork — visual resonance / center / alignment (phronesis in code)
 *
 * Base44-style spec:
 * {
 *   "component": "TuningFork",
 *   "props": {
 *     "size": 32,
 *     "stroke": "#000",
 *     "strokeWidth": 2,
 *     "interactive": true
 *   }
 * }
 */
(function initTuningForkComponent(global) {
  const DEFAULT_PROPS = {
    size: 32,
    stroke: "#000",
    strokeWidth: 2,
    interactive: true,
    meaning: "Mom's Center — Find Your Tone",
    placement: "default",
  };

  const PLACEMENT_CLASS = {
    logo: "tuning-fork--logo",
    art: "tuning-fork--art",
    rail: "tuning-fork--rail",
    default: "",
  };

  function createSvg(props) {
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
   * @param {Partial<typeof DEFAULT_PROPS> & { onClick?: () => void }} props
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
    if (merged.interactive) {
      root.dataset.onclick = "playTuningFork";
    }
    root.dataset.meaning = merged.meaning;
    root.title = merged.meaning;
    root.setAttribute(
      "aria-label",
      merged.interactive
        ? `${merged.meaning}. Play A440 tuning fork.`
        : merged.meaning
    );
    root.style.width = `${merged.size}px`;
    root.style.height = `${merged.size}px`;
    if (merged.stroke === "#000") {
      root.style.color = "var(--ink)";
    } else {
      root.style.color = merged.stroke;
    }

    root.appendChild(createSvg(merged));

    if (merged.interactive && typeof merged.onClick === "function") {
      root.addEventListener("click", () => {
        merged.onClick();
      });
    }

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
    DEFAULT_PROPS,
    create,
    mountAll,
  };
})(window);
