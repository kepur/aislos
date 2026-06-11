import { computed } from 'vue'

interface User {
  id: string
  email: string
  full_name: string | null
  role: string
  language: string
  company_id: string | null
  is_active: boolean
}

export function useAuth() {
  const user = useState<User | null>('ainerwise-auth-user', () => null)
  const token = useState<string | null>('ainerwise-auth-token', () => null)
  const refreshTokenValue = useState<string | null>('ainerwise-auth-refresh', () => null)
  const tokenCookie = useCookie<string | null>('ainerwise_token', { sameSite: 'lax' })
  const refreshCookie = useCookie<string | null>('ainerwise_refresh', { sameSite: 'lax' })
  if (!token.value && tokenCookie.value) token.value = tokenCookie.value
  if (!refreshTokenValue.value && refreshCookie.value) refreshTokenValue.value = refreshCookie.value

  const apiBase = useApiBase()
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'super_admin' || user.value?.role === 'admin')
  const isBuyer = computed(() => user.value?.role === 'buyer')
  const isVendor = computed(() => user.value?.role === 'vendor')

  function setTokens(access: string, refresh: string) {
    token.value = access
    refreshTokenValue.value = refresh
    tokenCookie.value = access
    refreshCookie.value = refresh
    if (import.meta.client) {
      localStorage.setItem('ainerwise_token', access)
      localStorage.setItem('ainerwise_refresh', refresh)
    }
  }

  function clearAuth() {
    token.value = null
    refreshTokenValue.value = null
    user.value = null
    tokenCookie.value = null
    refreshCookie.value = null
    if (import.meta.client) {
      localStorage.removeItem('ainerwise_token')
      localStorage.removeItem('ainerwise_refresh')
      localStorage.removeItem('ainerwise_demo_user')
    }
  }

  async function initAuth() {
    if (import.meta.client) {
      const savedToken = localStorage.getItem('ainerwise_token')
      const savedRefresh = localStorage.getItem('ainerwise_refresh')
      if (!token.value && savedToken) token.value = savedToken
      if (!refreshTokenValue.value && savedRefresh) refreshTokenValue.value = savedRefresh
    }
    if (token.value) await fetchUser()
  }

  function setDemoSession(role: 'buyer' | 'admin' | 'super_admin', email: string) {
    const demoUser: User = {
      id: `demo-${role}`,
      email,
      full_name: role === 'buyer' ? 'Demo Customer' : 'Demo Admin',
      role,
      language: 'en',
      company_id: 'demo-company',
      is_active: true,
    }
    user.value = demoUser
    token.value = `demo-token-${role}`
    refreshTokenValue.value = `demo-refresh-${role}`
    tokenCookie.value = token.value
    refreshCookie.value = refreshTokenValue.value
    if (import.meta.client) {
      localStorage.setItem('ainerwise_token', token.value)
      localStorage.setItem('ainerwise_refresh', refreshTokenValue.value)
      localStorage.setItem('ainerwise_demo_user', JSON.stringify(demoUser))
    }
  }

  async function login(email: string, password: string) {
    const data = await $fetch<{ access_token: string; refresh_token: string }>(`${apiBase}/auth/login`, {
      method: 'POST',
      body: { email, password },
    })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function register(payload: Record<string, any>) {
    const data = await $fetch<{ access_token: string; refresh_token: string }>(`${apiBase}/auth/register`, {
      method: 'POST',
      body: payload,
    })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function fetchUser() {
    if (!token.value) return
    if (token.value.startsWith('demo-token-')) {
      const savedDemoUser = import.meta.client ? localStorage.getItem('ainerwise_demo_user') : null
      if (savedDemoUser) user.value = JSON.parse(savedDemoUser)
      return
    }
    try {
      const data = await $fetch<User>(`${apiBase}/auth/me`, {
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
    setDemoSession,
  }
}
