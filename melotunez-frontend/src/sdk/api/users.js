/**
 * Option 3 — User helpers via Base44 SDK (browser).
 *
 * App components should keep using `src/api/users.js` (Express proxy).
 * SDK `list` signature is list(sort, limit, skip, fields) — not an options object.
 * Prefer entities.User.create; fall back to auth.inviteUser when create is rejected.
 */
import { base44 } from '../lib/base44.js';

function matchesQuery(user, q) {
  if (!q) return true;
  const term = String(q).toLowerCase().trim();
  if (!term) return true;
  return ['full_name', 'email', 'role'].some((field) =>
    String(user?.[field] ?? '')
      .toLowerCase()
      .includes(term),
  );
}

export async function getAllUsers(options = {}) {
  const { q, limit = 50, skip = 0, sort_by } = options;
  const sort = sort_by ?? '-created_date';
  const records = await base44.entities.User.list(sort, limit, skip);
  return (records || []).filter((user) => matchesQuery(user, q));
}

export async function getUserById(id) {
  return await base44.entities.User.get(id);
}

/**
 * Create a user. Prefer entities.User.create (works with api_key).
 * Fall back to auth.inviteUser when entity create is rejected.
 */
export async function createUser(data) {
  const email = data.email || data.user_email;
  const role = data.role || 'user';
  const full_name = data.full_name || '';

  try {
    return await base44.entities.User.create({ email, full_name, role });
  } catch {
    await base44.auth.inviteUser(email, role);
    const users = await base44.entities.User.filter({ email });
    const created = users?.[0];
    if (created?.id && full_name) {
      return base44.entities.User.update(created.id, { full_name });
    }
    return created ?? { email, role, full_name };
  }
}

export async function updateUser(id, data) {
  return await base44.entities.User.update(id, data);
}

export async function deleteUser(id) {
  await base44.entities.User.delete(id);
}
