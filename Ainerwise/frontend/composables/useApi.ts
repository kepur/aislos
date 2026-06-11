export function useApi() {
  const config = useRuntimeConfig()
  const { token, logout } = useAuth()

  async function apiFetch<T>(path: string, options: Record<string, any> = {}): Promise<T> {
    const headers: Record<string, string> = { ...(options.headers || {}) }

    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }

    try {
      return await $fetch<T>(`${config.public.apiBase}${path}`, {
        ...options,
        headers,
      })
    } catch (error: any) {
      if (error?.response?.status === 401) {
        logout()
      }
      throw error
    }
  }

  return { apiFetch }
}
