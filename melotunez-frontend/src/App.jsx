import { useEffect, useState } from 'react';
import { getAllUsers } from './api/users.js';
import AudioPlayer from './components/AudioPlayer.jsx';
import Playlists from './components/Playlists.jsx';
import Tracks from './components/Tracks.jsx';
import Users from './components/Users.jsx';

const NAV = [
  { id: 'tracks', label: 'Tracks' },
  { id: 'playlists', label: 'Playlists' },
  { id: 'users', label: 'Users' },
];

export default function App() {
  const [view, setView] = useState('tracks');
  const [currentTrack, setCurrentTrack] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [bootError, setBootError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      try {
        const users = await getAllUsers({ limit: 50 });
        if (cancelled) return;
        const admin =
          users.find((user) => user.role === 'admin' || user._app_role === 'admin') ||
          users[0] ||
          null;
        setCurrentUser(admin);
      } catch (err) {
        if (!cancelled) {
          setBootError(err?.message || 'Could not reach Base44 API');
        }
      }
    }
    boot();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-full text-[var(--color-cream)]">
      <div className="mx-auto flex min-h-full max-w-7xl">
        <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-[var(--color-line)]/80 bg-[var(--color-panel)]/60 px-5 py-6 backdrop-blur-md">
          <div className="mb-10">
            <p className="font-display text-2xl font-bold tracking-tight text-[var(--color-accent)]">
              MeloTunez
            </p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">Streaming dashboard</p>
          </div>

          <nav className="flex flex-1 flex-col gap-1">
            {NAV.map((item) => {
              const active = view === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setView(item.id)}
                  className={`rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${
                    active
                      ? 'bg-[var(--color-accent)] text-ink shadow-[0_0_0_1px_rgba(61,214,198,0.35)]'
                      : 'text-[var(--color-muted)] hover:bg-white/5 hover:text-white'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="mt-auto rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)]/80 p-3 text-xs text-[var(--color-muted)]">
            {currentUser ? (
              <>
                <div className="font-medium text-[var(--color-cream)]">
                  {currentUser.full_name || currentUser.email}
                </div>
                <div className="mt-0.5">{currentUser.role || 'user'}</div>
              </>
            ) : (
              <div className="animate-pulse-soft">Connecting…</div>
            )}
          </div>
        </aside>

        <main className={`min-w-0 flex-1 px-6 py-8 sm:px-8 ${currentTrack ? 'pb-32' : 'pb-8'}`}>
          {bootError && (
            <div className="mb-6 rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
              {bootError}
            </div>
          )}

          {view === 'tracks' && <Tracks onPlayTrack={setCurrentTrack} />}
          {view === 'playlists' && <Playlists onPlayTrack={setCurrentTrack} />}
          {view === 'users' && <Users currentUser={currentUser} />}
        </main>
      </div>

      <AudioPlayer track={currentTrack} onClose={() => setCurrentTrack(null)} />
    </div>
  );
}
