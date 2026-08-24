/**
 * A440 tuning fork — pure Web Audio, no samples, no dependencies.
 * Musicians use this pitch to calibrate before playing.
 *
 * @param {number} [duration=2] Ring length in seconds (smooth exponential fade-out).
 */
(function initPlayTuningFork(global) {
  const A440_HZ = 440;
  const PEAK_GAIN = 0.42;
  const ATTACK_SECONDS = 0.012;

  /** @type {AudioContext | null} */
  let sharedContext = null;

  function getAudioContext() {
    const Ctx = global.AudioContext || global.webkitAudioContext;
    if (!Ctx) return null;
    if (!sharedContext || sharedContext.state === "closed") {
      sharedContext = new Ctx();
    }
    return sharedContext;
  }

  function playTuningFork(duration = 2) {
    const audioContext = getAudioContext();
    if (!audioContext) return;

    const safeDuration = Math.max(0.25, Number(duration) || 2);
    const startTime = audioContext.currentTime;
    const stopTime = startTime + safeDuration;

    if (audioContext.state === "suspended") {
      void audioContext.resume();
    }

    const fundamental = audioContext.createOscillator();
    fundamental.type = "sine";
    fundamental.frequency.value = A440_HZ;

    // Tuning forks ring nearly pure; a whisper of the octave adds realism.
    const overtone = audioContext.createOscillator();
    overtone.type = "sine";
    overtone.frequency.value = A440_HZ * 2;

    const forkGain = audioContext.createGain();
    const overtoneGain = audioContext.createGain();

    forkGain.gain.setValueAtTime(0.0001, startTime);
    forkGain.gain.linearRampToValueAtTime(PEAK_GAIN, startTime + ATTACK_SECONDS);
    forkGain.gain.exponentialRampToValueAtTime(0.0001, stopTime);

    overtoneGain.gain.setValueAtTime(0.0001, startTime);
    overtoneGain.gain.linearRampToValueAtTime(PEAK_GAIN * 0.06, startTime + ATTACK_SECONDS);
    overtoneGain.gain.exponentialRampToValueAtTime(0.0001, stopTime);

    fundamental.connect(forkGain);
    overtone.connect(overtoneGain);
    forkGain.connect(audioContext.destination);
    overtoneGain.connect(audioContext.destination);

    fundamental.start(startTime);
    overtone.start(startTime);
    fundamental.stop(stopTime);
    overtone.stop(stopTime);

    fundamental.onended = () => {
      fundamental.disconnect();
      overtone.disconnect();
      forkGain.disconnect();
      overtoneGain.disconnect();
    };
  }

  global.playTuningFork = playTuningFork;
})(typeof window !== "undefined" ? window : globalThis);
