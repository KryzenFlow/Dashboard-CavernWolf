/**
 * ES module listener (for bundlers / type="module" pages):
 *
 *   import { playTuningFork } from "./sidepanel.js";
 *   document.getElementById("tuningForkBtn").addEventListener("click", () => {
 *     playTuningFork(2);
 *   });
 */
import { playTuningFork } from "./sidepanel.js";

const btn = document.getElementById("tuningForkBtn");
if (btn && btn.dataset.listenerBound !== "1") {
  btn.dataset.listenerBound = "1";
  btn.addEventListener("click", () => {
    playTuningFork(2);
  });
}
