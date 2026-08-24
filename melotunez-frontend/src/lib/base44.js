import { createClient } from '@base44/sdk'

export const base44 = createClient({
  appId: '6a8bbac67d8d3dfc43538a00',
  headers: {
    api_key: '5dc82b6be12b477e90146c7cf66b1845',
  },
  requiresAuth: false,
})
