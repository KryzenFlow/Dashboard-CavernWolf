import { base44 } from '../lib/base44.js';

export async function sendAssistantMessage(payload) {
  return await base44.functions.assistantChat(payload);
}
