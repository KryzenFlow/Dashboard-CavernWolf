/**
 * Utility layer — DOM creation helpers.
 */
(function initDom(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  FrankiesWall.dom = {
    $(id) {
      return document.getElementById(id);
    },

    formatTime(sec) {
      if (!Number.isFinite(sec) || sec < 0) return "0:00";
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60);
      return `${m}:${s.toString().padStart(2, "0")}`;
    },

    formatModeLabel(mode) {
      return mode.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    },

    fillCheckGrid(container, options, selected, labelFor) {
      if (!container) return;
      container.innerHTML = "";
      for (const opt of options) {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.value = opt;
        input.checked = selected.includes(opt);
        label.appendChild(input);
        label.appendChild(document.createTextNode(labelFor ? labelFor(opt) : opt));
        container.appendChild(label);
      }
    },

    readChecks(container) {
      if (!container) return [];
      return Array.from(container.querySelectorAll("input:checked")).map(
        (n) => /** @type {HTMLInputElement} */ (n).value
      );
    },

    readFileAsDataUrl(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(/** @type {string} */ (reader.result));
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
