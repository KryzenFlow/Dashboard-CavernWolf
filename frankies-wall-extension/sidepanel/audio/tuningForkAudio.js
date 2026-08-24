/**
 * Audio — A440 tuning fork (pure Web Audio).
 */
(function initTuningForkAudio(global) {
  function playTuningFork(duration = 2) {
    const AudioCtx = global.AudioContext || global.webkitAudioContext;
    if (!AudioCtx) return;

    const safeDuration = Math.max(0.25, Number(duration) || 2);
    const audioContext = new AudioCtx();

    if (audioContext.state === "suspended") {
      void audioContext.resume();
    }

    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.frequency.value = 440; // A4 standard
    gainNode.gain.setValueAtTime(1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
      0.001,
      audioContext.currentTime + safeDuration
    );

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.start();
    oscillator.stop(audioContext.currentTime + safeDuration);
  }

  global.playTuningFork = playTuningFork;

  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});
  FrankiesWall.playTuningFork = playTuningFork;
})(typeof window !== "undefined" ? window : globalThis);
