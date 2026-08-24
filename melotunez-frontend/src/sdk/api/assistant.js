/**
 * Option 3 — Assistant chat via Base44 SDK (browser).
 *
 * Prefer Option 2 (`src/api/assistant.js` → Express) so the api_key stays server-side.
 * Tries functions.assistantChat first, then functions.invoke('assistantChat').
 */
import { base44 } from '../lib/base44.js';

export async function sendAssistantMessage(payload) {
  if (typeof base44.functions.assistantChat === 'function') {
    return await base44.functions.assistantChat(payload);
  }
  const result = await base44.functions.invoke('assistantChat', payload || {});
  return result?.data ?? result;
}

export async function assistantChat(payload) {
  return sendAssistantMessage(payload);
}
