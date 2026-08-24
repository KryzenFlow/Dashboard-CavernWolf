import { useEffect, useState } from 'react'
import AudioPlayer from './components/AudioPlayer.jsx'
import Assistant from './components/Assistant.jsx'
import Playlists from './components/Playlists.jsx'
import Tracks from './components/Tracks.jsx'
import Users from './components/Users.jsx'
import { apiRequest } from './lib/http.js'

const NAV = [
  { id: 'tracks', label: 'Tracks' },
  { id: 'playlists', label: 'Playlists' },
  { id: 'users', label: 'Users' },
  { id: 'assistant', label: 'Assistant' },
]

export default function App() {
  const [view, setView] = useState('tracks')
  const [currentTrack, setCurrentTrack] = useState(null)
  const [apiStatus, setApiStatus] = useState(null)
  const [bootError, setBootError] = useState(null)
  const [bootLoading, setBootLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function boot() {
      setBootLoading(true)
      setBootError(null)
      try {
        const health = await apiRequest('/api/health')
        if (!cancelled) setApiStatus(health)
      } catch (err) {
        if (!cancelled) {
          setApiStatus(null)
          setBootError(
            err?.message ||
              'Could not reach MeloTunez API. Start melotunez-backend on port 3001.',
          )
        }
      } finally {
        if (!cancelled) setBootLoading(false)
      }
    }
    boot()
    return () => {
      cancelled = true
    }
  }, [])

  function renderView() {
    switch (view) {
      case 'tracks':
        return <Tracks onPlayTrack={setCurrentTrack} />
      case 'playlists':
        return <Playlists onPlayTrack={setCurrentTrack} />
      case 'users':
        return <Users />
      case 'assistant':
        return <Assistant />
      default: {
        const _exhaustive = view
        return (
          <div className="text-[var(--color-muted)]">
            Unknown view: {String(_exhaustive)}
          </div>
        )
      }
    }
  }

  return (
    <div className="min-h-full text-[var(--color-cream)]">
      <div className="mx-auto flex min-h-full max-w-7xl">
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-[var(--color-line)]/80 bg-[var(--color-panel)]/60 px-5 py-6 backdrop-blur-md md:flex">
          <div className="mb-10">
            <p className="font-display text-2xl font-bold tracking-tight text-[var(--color-accent)]">
              MeloTunez
            </p>
            <p className="mt-1 text-xs text-[var(--color-muted)]">Streaming dashboard</p>
          </div>

          <nav className="flex flex-1 flex-col gap-1">
            {NAV.map((item) => {
              const active = view === item.id
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
              )
            })}
          </nav>

          <div className="mt-auto rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)]/80 p-3 text-xs text-[var(--color-muted)]">
            {bootLoading ? (
              <div className="animate-pulse-soft">Connecting…</div>
            ) : apiStatus?.ok ? (
              <>
                <div className="font-medium text-[var(--color-cream)]">API connected</div>
                <div className="mt-0.5">via Express → Base44</div>
              </>
            ) : (
              <div>API offline</div>
            )}
          </div>
        </aside>

        <main className={`min-w-0 flex-1 px-4 py-6 sm:px-8 sm:py-8 ${currentTrack ? 'pb-32' : 'pb-8'}`}>
          <div className="mb-6 flex items-center justify-between gap-3 md:hidden">
            <p className="font-display text-xl font-bold text-[var(--color-accent)]">MeloTunez</p>
            <div className="flex gap-1 overflow-x-auto rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] p-1">
              {NAV.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setView(item.id)}
                  className={`shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium ${
                    view === item.id
                      ? 'bg-[var(--color-accent)] text-ink'
                      : 'text-[var(--color-muted)]'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {bootError && (
            <div className="mb-6 rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
              {bootError}
            </div>
          )}

          {renderView()}
        </main>
      </div>

      <AudioPlayer track={currentTrack} onClose={() => setCurrentTrack(null)} />
    </div>
  )
}
