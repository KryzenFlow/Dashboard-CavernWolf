/**
 * Base44 SDK client for MeloTunez.
 * API key stays server-side — never expose this to the browser.
 */
import { createClient } from '@base44/sdk';

const APP_ID = process.env.BASE44_APP_ID || '6a8bbac67d8d3dfc43538a00';
const API_KEY =
  process.env.BASE44_API_KEY || '5dc82b6be12b477e90146c7cf66b1845';

export const base44 = createClient({
  appId: APP_ID,
  headers: {
    api_key: API_KEY,
  },
});

export const base44Config = {
  appId: APP_ID,
};
