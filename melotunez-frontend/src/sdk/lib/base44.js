/**
 * Option 3 — direct Base44 SDK client (browser).
 *
 * Prefer Option 2 (`src/api/*` → Express) so the api_key stays server-side.
 * This module exists for Option 3 paste completeness / local experiments only.
 *
 * Config matches melotunez-backend/src/base44Client.js defaults.
 * Override with VITE_BASE44_APP_ID / VITE_BASE44_API_KEY if needed.
 */
import { createClient } from '@base44/sdk';

const APP_ID =
  import.meta.env.VITE_BASE44_APP_ID || '6a8bbac67d8d3dfc43538a00';
const API_KEY =
  import.meta.env.VITE_BASE44_API_KEY || '5dc82b6be12b477e90146c7cf66b1845';

export const base44 = createClient({
  appId: APP_ID,
  headers: {
    api_key: API_KEY,
  },
});

export const base44Config = {
  appId: APP_ID,
};
