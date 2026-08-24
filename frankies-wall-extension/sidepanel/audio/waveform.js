/**
 * Audio layer — optional waveform visualizer (Web Audio Analyser).
 */
(function initWaveform(global) {
  const FrankiesWall = (global.FrankiesWall = global.FrankiesWall || {});

  /** @type {AudioContext | null} */
  let audioContext = null;
  /** @type {MediaElementAudioSourceNode | null} */
  let mediaSource = null;
  /** @type {AnalyserNode | null} */
  let analyser = null;
  let rafId = null;

  function getContext() {
    const Ctx = global.AudioContext || global.webkitAudioContext;
    if (!Ctx) return null;
    if (!audioContext || audioContext.state === "closed") {
      audioContext = new Ctx();
    }
    return audioContext;
  }

  FrankiesWall.attachWaveformSource = function attachWaveformSource() {
    if (!FrankiesWall.state.waveformEnabled) return;
    const el = FrankiesWall.el;
    if (!el?.audio?.src || mediaSource) return;

    const ctx = getContext();
    if (!ctx) return;

    if (ctx.state === "suspended") void ctx.resume();

    try {
      mediaSource = ctx.createMediaElementSource(el.audio);
      analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.75;
      mediaSource.connect(analyser);
      analyser.connect(ctx.destination);
    } catch {
      mediaSource = null;
      analyser = null;
    }
  };

  FrankiesWall.drawWaveformFrame = function drawWaveformFrame() {
    const el = FrankiesWall.el;
    const canvas = el?.waveform;
    if (!canvas || canvas.hidden || !analyser) return;

    const ctx2d = canvas.getContext("2d");
    if (!ctx2d) return;

    const bufferLength = analyser.frequencyBinCount;
    const data = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(data);

    const { width, height } = canvas;
    ctx2d.clearRect(0, 0, width, height);
    ctx2d.lineWidth = 1.5;
    ctx2d.strokeStyle = "#c45c26";
    ctx2d.beginPath();

    const sliceWidth = width / bufferLength;
    let x = 0;
    for (let i = 0; i < bufferLength; i += 1) {
      const v = data[i] / 128;
      const y = (v * height) / 2;
      if (i === 0) ctx2d.moveTo(x, y);
      else ctx2d.lineTo(x, y);
      x += sliceWidth;
    }
    ctx2d.lineTo(width, height / 2);
    ctx2d.stroke();
  };

  FrankiesWall.startWaveform = function startWaveform() {
    if (!FrankiesWall.state.waveformEnabled) return;
    FrankiesWall.attachWaveformSource();
    if (rafId) return;

    const tick = () => {
      FrankiesWall.drawWaveformFrame();
      rafId = global.requestAnimationFrame(tick);
    };
    rafId = global.requestAnimationFrame(tick);
  };

  FrankiesWall.stopWaveform = function stopWaveform() {
    if (rafId) {
      global.cancelAnimationFrame(rafId);
      rafId = null;
    }
  };

  FrankiesWall.setWaveformEnabled = function setWaveformEnabled(enabled) {
    FrankiesWall.state.waveformEnabled = Boolean(enabled);
    const el = FrankiesWall.el;
    if (!el?.waveform || !el?.btnWaveform) return;

    el.waveform.hidden = !FrankiesWall.state.waveformEnabled;
    el.btnWaveform.classList.toggle("is-active", FrankiesWall.state.waveformEnabled);
    el.btnWaveform.setAttribute("aria-pressed", FrankiesWall.state.waveformEnabled ? "true" : "false");

    if (FrankiesWall.state.waveformEnabled) {
      FrankiesWall.resizeWaveformCanvas?.();
      FrankiesWall.attachWaveformSource();
      if (!el.audio.paused) FrankiesWall.startWaveform();
    } else {
      FrankiesWall.stopWaveform();
    }
  };

  FrankiesWall.resizeWaveformCanvas = function resizeWaveformCanvas() {
    const canvas = FrankiesWall.el?.waveform;
    if (!canvas || canvas.hidden) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = global.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.floor(rect.width * dpr));
    canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  };

  FrankiesWall.bindWaveform = function bindWaveform() {
    const el = FrankiesWall.el;
    if (!el?.waveform || !el?.btnWaveform) return;

    el.btnWaveform.addEventListener("click", () => {
      FrankiesWall.setWaveformEnabled(!FrankiesWall.state.waveformEnabled);
    });

    global.addEventListener("resize", () => FrankiesWall.resizeWaveformCanvas());
    FrankiesWall.setWaveformEnabled(FrankiesWall.state.waveformEnabled);
  };
})(typeof window !== "undefined" ? window : globalThis);
