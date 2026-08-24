import { apiRequest } from '../lib/http.js';

/** POST /api/assistant/chat → Base44 functions.assistantChat */
export async function sendAssistantMessage(payload) {
  return apiRequest('/api/assistant/chat', {
    method: 'POST',
    body: payload,
  });
}

export async function assistantChat(payload) {
  return sendAssistantMessage(payload);
}
