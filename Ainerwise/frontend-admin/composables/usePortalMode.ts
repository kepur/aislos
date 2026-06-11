type AdminPortalMode = 'aislos' | 'store' | 'marketing' | 'agent'

const PORTALS = {
  aislos: { name: 'AISLOS Admin Console', shortName: 'AISLOS', home: '/' },
  store: { name: 'Ainerwise Store Admin', shortName: 'Store Admin', home: '/store-orders' },
  marketing: { name: 'Marketing Portal', shortName: 'Marketing', home: '/marketing' },
  agent: { name: 'Agent Console', shortName: 'Agent Console', home: '/agents' },
} as const

const SHARED_PREFIXES = ['/login']
const OWNERS: Array<[string, AdminPortalMode]> = [
  ['/store-orders', 'store'],
  ['/products', 'store'],
  ['/categories', 'store'],
  ['/inventory', 'store'],
  ['/vendors', 'store'],
  ['/service-packages', 'store'],
  ['/compatibility', 'store'],
  ['/warranty-policies', 'store'],
  ['/supplier-warranties', 'store'],
  ['/marketing-studio', 'marketing'],
  ['/marketing', 'marketing'],
  ['/leads', 'marketing'],
  ['/inquiries', 'marketing'],
  ['/case-library', 'marketing'],
  ['/documents', 'marketing'],
  ['/agent-missions', 'agent'],
  ['/agents', 'agent'],
  ['/marketplace', 'agent'],
  ['/business-brain', 'agent'],
  ['/ai-runs', 'agent'],
  ['/ai-reviews', 'agent'],
  ['/knowledge', 'agent'],
  ['/integration-events', 'agent'],
  ['/audit-logs', 'agent'],
]

export function usePortalMode() {
  const config = useRuntimeConfig()
  const rawMode = String(config.public.portalMode)
  const mode = (rawMode in PORTALS ? rawMode : 'aislos') as AdminPortalMode
  const portal = PORTALS[mode]
  const urls: Record<AdminPortalMode, string> = {
    aislos: String(config.public.aislosAdminUrl),
    store: String(config.public.storeAdminUrl),
    marketing: String(config.public.marketingUrl),
    agent: String(config.public.agentUrl),
  }

  function ownerForPath(path: string): AdminPortalMode {
    return OWNERS.find(([prefix]) => path === prefix || path.startsWith(`${prefix}/`))?.[1] || 'aislos'
  }

  function isPathAllowed(path: string) {
    return SHARED_PREFIXES.some(prefix => path === prefix || path.startsWith(`${prefix}/`))
      || ownerForPath(path) === mode
  }

  return { mode, portal, urls, ownerForPath, isPathAllowed }
}
