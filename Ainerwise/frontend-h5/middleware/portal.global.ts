import { getLocalePrefixFromPath, stripLocalePrefix, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware(async (to) => {
  const { mode, portal, urls, ownerForPath, isPathAllowed: isPhysicalPathAllowed } = usePortalMode()
  const { token } = useAuth()
  const {
    manifest,
    loadedKey,
    isRouteAllowed,
    isPortalAvailable,
    load,
    loadAccess,
    activePortalCookie,
  } = usePortalManifest()
  const buildExternalUrl = (base: string, fullPath: string) => `${base.replace(/\/$/, '')}${fullPath}`
  const localePrefix = getLocalePrefixFromPath(to.path)
  const path = stripLocalePrefix(to.path)
  const localized = (target: string) => localePrefix ? withLocalePrefix(target, localePrefix) : target

  if (path === '/' && mode !== 'customer') return navigateTo(localized(portal.home))
  if (!isPhysicalPathAllowed(path)) {
    const owner = ownerForPath(path)
    const ownerUrl = owner === 'field_worker' || owner === 'supplier' ? urls.customer : urls[owner]
    return navigateTo(buildExternalUrl(ownerUrl, to.fullPath), { external: true })
  }

  const sharedPath = ['/login', '/register', '/access-denied'].includes(path)
    || path.startsWith('/auth/')
  const accountPath = path.startsWith('/profile/') || path.startsWith('/settings/')
  const activeH5Portal = activePortalCookie.value?.endsWith('_h5')
    ? activePortalCookie.value
    : null
  const targetKey = sharedPath && manifest.value ? manifest.value.portal_key
    : accountPath ? activeH5Portal || 'cebu_buyer_h5'
      : path === '/partner' || path.startsWith('/partner/') ? 'partner_company_h5'
      : path === '/field' || path.startsWith('/field/') ? 'field_worker_h5'
        : path === '/supplier' || path.startsWith('/supplier/') ? 'supplier_h5'
          : path.startsWith('/messages/') ? activeH5Portal || 'cebu_buyer_h5'
          : path === '/buyer' || path.startsWith('/buyer/') || path.startsWith('/messages/') ? 'cebu_buyer_h5'
            : path === '/crew' || path.startsWith('/crew/') ? 'crew_lead_h5'
              : path === '/marketing-mobile' || path.startsWith('/marketing-mobile/') ? 'marketing_h5'
                : path === '/kiosk' || path.startsWith('/kiosk/') ? 'kiosk_h5'
                  : path === '/projects' || path.startsWith('/projects/') || path === '/dashboard' || path.startsWith('/customer/') ? 'customer_h5'
                    : 'consumer_h5'
  if (loadedKey.value !== targetKey) {
    await load(targetKey)
  }

  if (sharedPath) return

  // Kiosk access is authenticated by its revocable device token at the API,
  // not by a human Core session.
  const protectedPortal = targetKey !== 'kiosk_h5' && Boolean(manifest.value?.required_grants.length)
  if (!token.value && protectedPortal && !sharedPath) {
    return navigateTo({ path: localized('/login'), query: { redirect: to.fullPath } })
  }
  if (token.value) {
    const accessAvailable = await loadAccess(true)
    if (protectedPortal && !sharedPath && !accessAvailable) {
      return navigateTo({ path: localized('/access-denied'), query: { reason: 'Portal access could not be verified' } })
    }
    if (protectedPortal && !sharedPath && !isPortalAvailable(targetKey)) {
      return navigateTo(localized('/access-denied'))
    }
  }

  if (isRouteAllowed(path)) return
  return navigateTo({ path: localized('/access-denied'), query: { reason: 'Route is not allowed in this portal' } })
})
