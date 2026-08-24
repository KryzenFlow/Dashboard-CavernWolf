import { apiRequest, buildQuery } from '../lib/http.js';

export async function getAllUsers(options = {}) {
  const { q, query, limit = 50, skip = 0, sort, sort_by } = options;
  return apiRequest(
    `/api/users${buildQuery({
      q: q ?? query,
      limit,
      skip,
      sort: sort ?? sort_by,
    })}`,
  );
}

export async function createUser(data) {
  return apiRequest('/api/users', { method: 'POST', body: data });
}

export async function deleteUser(id) {
  return apiRequest(`/api/users/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}
