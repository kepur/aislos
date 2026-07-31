type DemoAccount = {
  id?: string
  key?: string
  label: string
  email?: string | null
  password?: string | null
  role?: string
  actual_role?: string
  auth_type?: string
  portals?: string[]
  portal_keys?: string[]
  exists?: boolean
  is_active?: boolean | null
  demo_only?: boolean
  device_count?: number
  grant_count?: number
  membership_count?: number
  login_blocked_when_demo_off?: boolean
  notes?: string
  description?: string
}

type DemoMode = {
  enabled: boolean
  buyer?: DemoAccount
  admin?: DemoAccount
  service_accounts?: DemoAccount[]
  account_matrix?: DemoAccount[]
}

const defaultDemoMode: DemoMode = {
  enabled: false,
}

export function useDemoMode() {
  const apiBase = useApiBase()
  const { token } = useAuth()

  async function getDemoMode(includeAdmin = false): Promise<DemoMode> {
    try {
      const headers: Record<string, string> = {}
      if (includeAdmin && token.value) headers.Authorization = `Bearer ${token.value}`
      return await $fetch<DemoMode>(`${apiBase}${includeAdmin ? '/demo-mode/admin' : '/demo-mode'}`, { headers })
    } catch {
      return defaultDemoMode
    }
  }

  async function updateDemoMode(enabled: boolean): Promise<DemoMode> {
    const headers: Record<string, string> = {}
    if (token.value) headers.Authorization = `Bearer ${token.value}`
    return await $fetch<DemoMode>(`${apiBase}/demo-mode`, {
      method: 'PATCH',
      headers,
      body: { enabled },
    })
  }

  return { getDemoMode, updateDemoMode, defaultDemoMode }
}
