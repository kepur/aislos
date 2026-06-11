// Kiosk device client (Portal 10). The tablet is a dumb terminal: it only
// holds a revocable device token and can only reach the /showroom/kiosk API
// surface. No user JWT, no long-lived secrets, no direct data access.
const TOKEN_KEY = 'kiosk-device-token'

export function useKiosk() {
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase)

  const deviceToken = useState<string | null>('kiosk-token', () => null)

  function loadToken() {
    if (!import.meta.client) return null
    deviceToken.value = localStorage.getItem(TOKEN_KEY)
    return deviceToken.value
  }

  function saveToken(token: string) {
    deviceToken.value = token
    if (import.meta.client) localStorage.setItem(TOKEN_KEY, token)
  }

  function clearToken() {
    deviceToken.value = null
    if (import.meta.client) localStorage.removeItem(TOKEN_KEY)
  }

  async function kioskFetch<T>(path: string, options: any = {}): Promise<T> {
    return await $fetch<T>(`${apiBase}/showroom/kiosk${path}`, {
      ...options,
      headers: { 'X-Kiosk-Token': deviceToken.value || '', ...(options.headers || {}) },
    })
  }

  return { deviceToken, loadToken, saveToken, clearToken, kioskFetch }
}
