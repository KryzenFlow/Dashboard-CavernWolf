import { useEffect, useState } from 'react';
import { createUser, deleteUser, getAllUsers } from '../api/users.js';

const EMPTY_FORM = {
  email: '',
  full_name: '',
  role: 'user',
};

/**
 * User management via Express → Base44 (server holds api_key).
 * Create/delete use admin-capable server credentials (inviteUser / entity create).
 */
export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  async function loadUsers() {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllUsers({ limit: 200 });
      setUsers(data || []);
    } catch (err) {
      setError(err?.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createUser(form);
      setModalOpen(false);
      setForm(EMPTY_FORM);
      await loadUsers();
    } catch (err) {
      setError(err?.message || 'Failed to create user');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(user) {
    if (!window.confirm(`Delete user ${user.email}?`)) return;
    setError(null);
    try {
      await deleteUser(user.id);
      setUsers((prev) => prev.filter((item) => item.id !== user.id));
    } catch (err) {
      setError(err?.message || 'Failed to delete user');
    }
  }

  return (
    <section className="animate-fade-up space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-display text-3xl font-semibold tracking-tight">Users</h2>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            Invite and remove Base44 users through the Express API.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded-xl bg-[var(--color-accent)] px-4 py-2.5 text-sm font-semibold text-ink transition hover:brightness-110"
        >
          Create user
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-4 py-3 text-sm text-[var(--color-danger)]">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/70 p-10 text-center text-[var(--color-muted)] animate-pulse-soft">
          Loading users…
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)]/80">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-[var(--color-line)] text-[var(--color-muted)]">
              <tr>
                <th className="px-4 py-3 font-medium">Full name</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-10 text-center text-[var(--color-muted)]">
                    No users found.
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-[var(--color-line)]/70 hover:bg-white/5"
                  >
                    <td className="px-4 py-3 font-medium">{user.full_name || '—'}</td>
                    <td className="px-4 py-3 text-[var(--color-muted)]">{user.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-md px-2 py-1 text-xs font-medium ${
                          user.role === 'admin'
                            ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)]'
                            : 'bg-white/10 text-[var(--color-muted)]'
                        }`}
                      >
                        {user.role || 'user'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => handleDelete(user)}
                        className="text-xs text-[var(--color-danger)] hover:underline"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <form
            onSubmit={handleCreate}
            className="w-full max-w-md space-y-4 rounded-2xl border border-[var(--color-line)] bg-[var(--color-panel)] p-6"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold">Invite user</h3>
              <button type="button" onClick={() => setModalOpen(false)} className="text-[var(--color-muted)]">
                Close
              </button>
            </div>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Email *</span>
              <input
                required
                type="email"
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Full name</span>
              <input
                value={form.full_name}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, full_name: event.target.value }))
                }
                className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--color-muted)]">Role</span>
              <select
                value={form.role}
                onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}
                className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-panel-2)] px-3 py-2 outline-none focus:border-[var(--color-accent)]"
              >
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="rounded-xl border border-[var(--color-line)] px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-[var(--color-accent)] px-4 py-2 text-sm font-semibold text-ink disabled:opacity-60"
              >
                {saving ? 'Inviting…' : 'Invite user'}
              </button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
