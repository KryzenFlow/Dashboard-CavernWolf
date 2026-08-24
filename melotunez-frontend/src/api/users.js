import { base44 } from '../lib/base44.js';

export async function getAllUsers(options = {}) {
  const { q, limit = 50, skip = 0, sort_by = '-created_date' } = options;
  const records = await base44.entities.User.list(sort_by, limit, skip);
  if (!q) return records || [];
  const term = String(q).toLowerCase().trim();
  return (records || []).filter((user) =>
    [user.full_name, user.email, user.role]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(term))
  );
}

export async function getUserById(id) {
  return await base44.entities.User.get(id);
}

/**
 * Invite/create a user via auth.inviteUser (entities.User.create is not supported).
 * Accepts { email, role, full_name? } from the UI form.
 */
export async function createUser(data) {
  const email = data.email || data.user_email;
  const role = data.role || 'user';
  await base44.auth.inviteUser(email, role);
  if (data.full_name) {
    const users = await base44.entities.User.filter({ email });
    const created = users?.[0];
    if (created?.id) {
      return await base44.entities.User.update(created.id, { full_name: data.full_name });
    }
  }
  const users = await base44.entities.User.filter({ email });
  return users?.[0] ?? { email, role };
}

export async function updateUser(id, data) {
  return await base44.entities.User.update(id, data);
}

export async function deleteUser(id) {
  await base44.entities.User.delete(id);
}
