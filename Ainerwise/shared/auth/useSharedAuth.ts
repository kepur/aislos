import { navigateTo, useCookie, useState } from '#app'
import { computed } from 'vue'

export interface AinerWiseAuthUser {
  id: string
  email: string
  full_name: string | null
  role: string
  language: string
  company_id: string | null
  is_active: boolean
}

type RoleSet = readonly string[] | ReadonlySet<string>

export interface SharedAuthOptions {
  apiBase: string
  adminRoles?: RoleSet
  logoutRedirect?: string
  onClearClient?: () => void | Promise<void>
}

function hasRole(roleSet: RoleSet | undefined, role: string | undefined) {
  if (!roleSet || !role) return false
  return Array.isArray(roleSet) ? roleSet.includes(role) : roleSet.has(role)
}

function resetPortalAccess(clearManifest = false) {
  useState('portal-access-loaded').value = false
  useState('portal-access-items').value = []
  useState('portal-access-memberships').value = []
  useState('portal-active-workspace').value = null
  useState('portal-access-error').value = ''
  if (clearManifest) {
    useCookie<string | null>('ainerwise_active_portal').value = null
    useCookie<string | null>('ainerwise_active_workspace').value = null
    useState('portal-manifest').value = null
    useState('portal-manifest-loaded-key').value = null
  }
}

export function createSharedAuth(options: SharedAuthOptions) {
  const user = useState<AinerWiseAuthUser | null>('ainerwise-auth-user', () => null)
  const token = useState<string | null>('ainerwise-auth-token', () => null)
  const refreshTokenValue = useState<string | null>('ainerwise-auth-refresh', () => null)
  const tokenCookie = useCookie<string | null>('ainerwise_token', { sameSite: 'lax' })
  const refreshCookie = useCookie<string | null>('ainerwise_refresh', { sameSite: 'lax' })

  if (!token.value && tokenCookie.value) token.value = tokenCookie.value
  if (!refreshTokenValue.value && refreshCookie.value) refreshTokenValue.value = refreshCookie.value

  const defaultAdminRoles = ['super_admin', 'admin']
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => hasRole(options.adminRoles || defaultAdminRoles, user.value?.role))
  const isBuyer = computed(() => user.value?.role === 'buyer')
  const isVendor = computed(() => user.value?.role === 'vendor')
  const isDeveloper = computed(() => user.value?.role === 'developer')
  const isServicePartner = computed(() => user.value?.role === 'service_partner')

  function setTokens(access: string, refresh: string) {
    resetPortalAccess()
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
    resetPortalAccess(true)
    token.value = null
    refreshTokenValue.value = null
    user.value = null
    tokenCookie.value = null
    refreshCookie.value = null
    if (import.meta.client) {
      localStorage.removeItem('ainerwise_token')
      localStorage.removeItem('ainerwise_refresh')
      void Promise.resolve(options.onClearClient?.()).catch(() => undefined)
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const data = await $fetch<AinerWiseAuthUser>(`${options.apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      user.value = data
    } catch {
      clearAuth()
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

  async function login(email: string, password: string) {
    const data = await $fetch<{ access_token: string; refresh_token: string }>(`${options.apiBase}/auth/login`, {
      method: 'POST',
      body: { email, password },
    })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  async function register(payload: Record<string, any>) {
    const data = await $fetch<{ access_token: string; refresh_token: string }>(`${options.apiBase}/auth/register`, {
      method: 'POST',
      body: payload,
    })
    setTokens(data.access_token, data.refresh_token)
    await fetchUser()
  }

  function logout() {
    clearAuth()
    return navigateTo(options.logoutRedirect || '/login')
  }

  return {
    user,
    token,
    refreshToken: refreshTokenValue,
    isLoggedIn,
    isAdmin,
    isBuyer,
    isVendor,
    isDeveloper,
    isServicePartner,
    login,
    register,
    logout,
    clearAuth,
    initAuth,
    fetchUser,
    setTokens,
  }
}
