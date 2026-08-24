/**
 * No modules — global playTuningFork (default 2 seconds).
 *
 *   document.getElementById("tuningForkBtn").addEventListener("click", () => {
 *     playTuningFork();
 *   });
 *
 * Load after: playTuningFork.js → sidepanel-app.js (optional pulse wrap)
 */
(function initTuningForkListener() {
  const btn = document.getElementById("tuningForkBtn");
  if (!btn || btn.dataset.listenerBound === "1") return;
  btn.dataset.listenerBound = "1";

  btn.addEventListener("click", () => {
    if (typeof window.playTuningFork === "function") {
      window.playTuningFork();
    }
  });
})();
