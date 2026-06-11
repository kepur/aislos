type PcPortalMode = 'aislos' | 'store' | 'developer'

const PORTALS = {
  aislos: { name: 'AISLOS', home: '/' },
  store: { name: 'Ainerwise Store', home: '/store' },
  developer: { name: 'AISLOS Developer', home: '/developers' },
} as const

const COMMON_PREFIXES = ['/login', '/register', '/demo-login']
const OWNERS: Array<[string, PcPortalMode]> = [
  ['/store', 'store'],
  ['/products', 'store'],
  ['/developers', 'developer'],
  ['/marketplace', 'developer'],
]

export function usePortalMode() {
  const config = useRuntimeConfig()
  const rawMode = String(config.public.portalMode)
  const mode = (rawMode in PORTALS ? rawMode : 'aislos') as PcPortalMode
  const portal = PORTALS[mode]
  const urls: Record<PcPortalMode | 'customer' | 'admin' | 'storeAdmin' | 'agent', string> = {
    aislos: String(config.public.aislosUrl),
    store: String(config.public.storeUrl),
    developer: String(config.public.developerUrl),
    customer: String(config.public.customerUrl),
    admin: String(config.public.adminUrl),
    storeAdmin: String(config.public.storeAdminUrl),
    agent: String(config.public.agentUrl),
  }

  function ownerForPath(path: string): PcPortalMode {
    return OWNERS.find(([prefix]) => path === prefix || path.startsWith(`${prefix}/`))?.[1] || 'aislos'
  }

  function isPathAllowed(path: string) {
    return COMMON_PREFIXES.some(prefix => path === prefix || path.startsWith(`${prefix}/`))
      || ownerForPath(path) === mode
  }

  return { mode, portal, urls, ownerForPath, isPathAllowed }
}
