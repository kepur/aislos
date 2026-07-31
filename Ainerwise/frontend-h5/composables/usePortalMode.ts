type H5PortalMode = 'customer' | 'partner' | 'kiosk'

const PORTALS = {
  customer: { name: 'Customer Project Portal', shortName: 'AinerWise', home: '/' },
  partner: { name: 'Partner Portal', shortName: 'AinerWise Partner', home: '/partner' },
  kiosk: { name: 'AISLOS Experience Center', shortName: 'AISLOS Kiosk', home: '/kiosk' },
} as const

export function usePortalMode() {
  const config = useRuntimeConfig()
  const rawMode = String(config.public.portalMode)
  const mode = (rawMode in PORTALS ? rawMode : 'customer') as H5PortalMode
  const portal = PORTALS[mode]
  const urls: Record<H5PortalMode, string> = {
    customer: String(config.public.customerUrl),
    partner: String(config.public.partnerUrl),
    kiosk: String(config.public.kioskUrl),
  }

  function ownerForPath(path: string): H5PortalMode | 'field_worker' | 'supplier' {
    if (path === '/kiosk' || path.startsWith('/kiosk/')) return 'kiosk'
    if (path === '/field' || path.startsWith('/field/')) return 'field_worker'
    if (path === '/supplier' || path.startsWith('/supplier/')) return 'supplier'
    return path === '/partner' || path.startsWith('/partner/') ? 'partner' : 'customer'
  }

  function isPathAllowed(path: string) {
    const shared = ['/login', '/profile', '/access-denied']
    if (shared.some(prefix => path === prefix || path.startsWith(`${prefix}/`))) return true
    const owner = ownerForPath(path)
    if (owner === 'field_worker') return mode === 'partner' || mode === 'customer'
    if (owner === 'supplier') return mode === 'partner' || mode === 'customer'
    return owner === mode
  }

  return { mode, portal, urls, ownerForPath, isPathAllowed }
}
