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

  function ownerForPath(path: string): H5PortalMode {
    if (path === '/kiosk' || path.startsWith('/kiosk/')) return 'kiosk'
    return path === '/partner' || path.startsWith('/partner/') ? 'partner' : 'customer'
  }

  function isPathAllowed(path: string) {
    return ['/login', '/profile', '/access-denied'].some(prefix => path === prefix || path.startsWith(`${prefix}/`))
      || ownerForPath(path) === mode
  }

  return { mode, portal, urls, ownerForPath, isPathAllowed }
}
