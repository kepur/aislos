type PcPortalMode = 'aislos' | 'store' | 'developer'
type PcRouteOwner = PcPortalMode | 'customer'

const PORTALS = {
  aislos: { name: 'AISLOS', home: '/' },
  store: { name: 'AISLOS Product Catalog', home: '/products' },
  developer: { name: 'AISLOS Developer', home: '/developers' },
} as const

const COMMON_PREFIXES = ['/login', '/register', '/demo-login']
const OWNERS: Array<[string, PcRouteOwner]> = [
  ['/portal', 'customer'],
  ['/store', 'store'],
  ['/products', 'store'],
  ['/developers', 'developer'],
  ['/marketplace', 'developer'],
]

// Cross-portal links must follow the host the visitor is actually on:
// the configured URLs bake in a build-time host (localhost or a LAN IP that
// goes stale when the network changes), which breaks portal jumps for any
// other host. Keep the configured port, swap in the current hostname.
function adaptUrlToCurrentHost(raw: string): string {
  if (!import.meta.client || !raw) return raw
  try {
    const url = new URL(raw)
    const pageHost = window.location.hostname
    const isLoopback = (host: string) => host === 'localhost' || host === '127.0.0.1'
    const isPrivateIp = (host: string) => /^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)/.test(host)
    if (url.hostname !== pageHost && (isLoopback(url.hostname) || isPrivateIp(url.hostname))) {
      url.hostname = pageHost
      return url.toString().replace(/\/$/, '')
    }
  } catch {}
  return raw
}

export function usePortalMode() {
  const config = useRuntimeConfig()
  const rawMode = String(config.public.portalMode)
  const mode = (rawMode in PORTALS ? rawMode : 'aislos') as PcPortalMode
  const portal = PORTALS[mode]
  const urls: Record<PcPortalMode | 'customer' | 'admin' | 'storeAdmin' | 'agent' | 'market', string> = {
    aislos: adaptUrlToCurrentHost(String(config.public.aislosUrl)),
    store: adaptUrlToCurrentHost(String(config.public.storeUrl)),
    developer: adaptUrlToCurrentHost(String(config.public.developerUrl)),
    customer: adaptUrlToCurrentHost(String(config.public.customerUrl)),
    admin: adaptUrlToCurrentHost(String(config.public.adminUrl)),
    storeAdmin: adaptUrlToCurrentHost(String(config.public.storeAdminUrl)),
    agent: adaptUrlToCurrentHost(String(config.public.agentUrl)),
    market: adaptUrlToCurrentHost(String(config.public.marketUrl)),
  }

  function ownerForPath(path: string): PcRouteOwner {
    return OWNERS.find(([prefix]) => path === prefix || path.startsWith(`${prefix}/`))?.[1] || 'aislos'
  }

  function isPathAllowed(path: string) {
    const owner = ownerForPath(path)
    return COMMON_PREFIXES.some(prefix => path === prefix || path.startsWith(`${prefix}/`))
      || owner === mode
      || (mode === 'aislos' && owner === 'customer')
  }

  return { mode, portal, urls, ownerForPath, isPathAllowed }
}
