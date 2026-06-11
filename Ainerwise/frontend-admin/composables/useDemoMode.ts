type DemoAccount = {
  label: string
  email: string
  password: string
  description?: string
}

type DemoMode = {
  enabled: boolean
  buyer: DemoAccount
  admin?: DemoAccount
}

const defaultDemoMode: DemoMode = {
  enabled: true,
  buyer: {
    label: 'Demo Customer',
    email: 'demo@ainerwise.com',
    password: 'demo123',
    description: 'Explore customer portal, AI assessment, leads, quotes, tickets, and project previews.',
  },
  admin: {
    label: 'Demo Admin',
    email: 'admin@ainerwise.com',
    password: 'admin123456',
    description: 'Explore admin CRM, leads, products, solutions, proposals, and operations views.',
  },
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
