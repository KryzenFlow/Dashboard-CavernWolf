import { useState } from 'react';
import { assistantChat } from '../api/assistant.js';

/**
 * Simple chat UI for Base44 functions.assistantChat via Express.
 */
export default function Assistant() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    const nextMessages = [...messages, { role: 'user', content: text }];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const result = await assistantChat({
        message: text,
        messages: nextMessages,
      });
      const reply =
        (typeof result === 'string' && result) ||
        result?.reply ||
        result?.message ||
        result?.response ||
        result?.data?.reply ||
        result?.data?.message ||
        JSON.stringify(result, null, 2);

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: String(reply) },
      ]);
    } catch (err) {
      setError(err?.message || 'Assistant request failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="animate-fade-up mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <h2 className="font-display text-3xl font-semibold tracking-tight">Assistant</h2>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Chat with the Base44 <code className="text-[var(--color-accent)]">assistantChat</code> function.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      <div className="min-h-[280px] space-y-3 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80 p-4">
        {messages.length === 0 ? (
          <p className="py-16 text-center text-sm text-[var(--color-muted)]">
            Ask about tracks, playlists, or the catalog.
          </p>
        ) : (
          messages.map((msg, index) => (
            <div
              key={`${msg.role}-${index}`}
              className={`rounded-xl px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'ml-8 bg-[var(--color-accent)]/15 text-[var(--color-cream)]'
                  : 'mr-8 bg-[var(--color-panel-2)] text-[var(--color-muted)]'
              }`}
            >
              <div className="mb-1 text-[10px] uppercase tracking-wide opacity-70">
                {msg.role}
              </div>
              <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
            </div>
          ))
        )}
        {loading && (
          <div className="text-sm text-[var(--color-muted)] animate-pulse-soft">
            Thinking…
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Message the assistant…"
          className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel)] px-4 py-2.5 text-sm outline-none ring-[var(--color-accent)] placeholder:text-[var(--color-muted)] focus:ring-2"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-ink disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </section>
  );
}
