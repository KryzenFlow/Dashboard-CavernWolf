/**
 * Full drop-in: A440 tuning fork tone (local Web Audio, no network).
 * @param {number} [duration=2]
 */
function playTuningFork(duration = 2) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  // Standard tuning pitch A4 = 440 Hz
  oscillator.frequency.value = 440;

  // Smooth fade-out
  gainNode.gain.setValueAtTime(1, audioContext.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(
    0.001,
    audioContext.currentTime + duration
  );

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);

  oscillator.start();
  oscillator.stop(audioContext.currentTime + duration);
}

window.playTuningFork = playTuningFork;

// ES module export (import { playTuningFork } from "./components/playTuningFork.js")
export { playTuningFork };
