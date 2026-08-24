import { useEffect, useRef, useState } from 'react';

export default function AudioPlayer({ track, onClose }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setError(null);
    setPlaying(Boolean(track?.audio_url));
  }, [track?.id, track?.audio_url]);

  if (!track) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--color-line)] bg-[var(--color-ink)]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center">
        <div className="flex min-w-0 items-center gap-3 sm:w-64">
          {track.cover_url ? (
            <img
              src={track.cover_url}
              alt=""
              className="h-12 w-12 rounded-lg object-cover"
            />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--color-panel-2)] text-xs text-[var(--color-muted)]">
              Audio
            </div>
          )}
          <div className="min-w-0">
            <div className="truncate font-medium">{track.title}</div>
            <div className="truncate text-sm text-[var(--color-muted)]">{track.artist}</div>
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-1">
          <audio
            ref={audioRef}
            key={track.id}
            src={track.audio_url}
            controls
            autoPlay
            className="w-full"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onError={() => setError('Unable to play this audio URL')}
          />
          {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden text-xs text-[var(--color-muted)] sm:inline">
            {playing ? 'Playing' : 'Paused'}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-3 py-2 text-sm text-[var(--color-muted)] hover:bg-white/5 hover:text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
