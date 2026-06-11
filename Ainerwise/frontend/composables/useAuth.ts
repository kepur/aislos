import { ref, computed } from 'vue'

interface User {
  id: string
  email: string
  full_name: string | null
  role: string
  language: string
  company_id: string | null
  is_active: boolean
}

const user = ref<User | null>(null)
const token = ref<string | null>(null)
const refreshTokenValue = ref<string | null>(null)

export function useAuth() {
  const config = useRuntimeConfig()
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'super_admin' || user.value?.role === 'admin')
  const isBuyer = computed(() => user.value?.role === 'buyer')
  const isVendor = computed(() => user.value?.role === 'vendor')

  function setTokens(access: string, refresh: string) {
    token.value = access
    refreshTokenValue.value = refresh
    if (import.meta.client) {
      localStorage.setItem('ainerwise_token', access)
      localStorage.setItem('ainerwise_refresh', refresh)
    }
  }

  function clearAuth() {
    token.value = null
    refreshTokenValue.value = null
    user.value = null
    if (import.meta.client) {
      localStorage.removeItem('ainerwise_token')
      localStorage.removeItem('ainerwise_refresh')
    }
  }

  function initAuth() {
    if (import.meta.client) {
      const savedToken = localStorage.getItem('ainerwise_token')
      const savedRefresh = localStorage.getItem('ainerwise_refresh')
      if (savedToken) {
        token.value = savedToken
        refreshTokenValue.value = savedRefresh
        fetchUser()
      }
    }
  }

  async function login(email: string, password: string) {
    const data = await $fetch<{ access_token: string; refresh_token: string }>(`${config.public.apiBase}/auth/login`, {
      method: 'POST',
      body: { email, password },
    })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function register(payload: Record<string, any>) {
    const data = await $fetch<{ access_token: string; refresh_token: string }>(`${config.public.apiBase}/auth/register`, {
      method: 'POST',
      body: payload,
    })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const data = await $fetch<User>(`${config.public.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      user.value = data
    } catch {
      clearAuth()
    }
  }

  function logout() {
    clearAuth()
    navigateTo('/login')
  }

  return {
    user,
    token,
    isLoggedIn,
    isAdmin,
    isBuyer,
    isVendor,
    login,
    register,
    logout,
    initAuth,
    fetchUser,
  }
}
