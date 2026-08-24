/**
 * Wire #instrumentFilter buttons → filterByInstrument (load after sidepanel-app.js).
 */
document.querySelectorAll("#instrumentFilter button").forEach((btn) => {
  btn.addEventListener("click", () => {
    const instrument = btn.getAttribute("data-instrument");
    filterByInstrument(instrument);
  });
});
