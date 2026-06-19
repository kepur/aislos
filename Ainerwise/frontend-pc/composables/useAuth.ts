import { createSharedAuth } from '@ainerwise/shared-auth'

export function useAuth() {
  return createSharedAuth({
    apiBase: useApiBase(),
    logoutRedirect: '/login',
  })
}
