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
}

export function useDemoMode() {
  const apiBase = useApiBase()

  async function getDemoMode(): Promise<DemoMode> {
    try {
      return await $fetch<DemoMode>(`${apiBase}/demo-mode`)
    } catch {
      return defaultDemoMode
    }
  }

  return { getDemoMode, defaultDemoMode }
}
