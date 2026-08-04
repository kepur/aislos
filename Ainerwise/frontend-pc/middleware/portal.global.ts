import { getLocalePrefixFromPath, stripLocalePrefix, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware(async (to) => {
  const { mode, portal, urls, ownerForPath, isPathAllowed: isPhysicalPathAllowed } = usePortalMode()
  const { token } = useAuth()
  const { manifest, loadedKey, isRouteAllowed, isPortalAvailable, load, loadAccess } = usePortalManifest()
  const requestUrl = useRequestURL()
  const isCebuHost = ['cebu.localhost', 'cebu.local', 'market.localhost', 'market.local'].includes(requestUrl.hostname)
  const buildExternalUrl = (base: string, fullPath: string) => `${base.replace(/\/$/, '')}${fullPath}`
  const localePrefix = getLocalePrefixFromPath(to.path)
  const path = stripLocalePrefix(to.path)
  const localized = (target: string) => localePrefix ? withLocalePrefix(target, localePrefix) : target
  const publicAssetPrefixes = ['/_nuxt/', '/videos/', '/images/', '/img/', '/icons/', '/fonts/']
  const publicAssetFiles = [
    '/favicon.ico',
    '/robots.txt',
    '/sitemap.xml',
    '/manifest.webmanifest',
    '/site.webmanifest',
    '/apple-touch-icon.png',
  ]

  if (publicAssetPrefixes.some(prefix => path.startsWith(prefix)) || publicAssetFiles.includes(path)) {
    return
  }

  if (path === '/' && isCebuHost) return navigateTo(localized('/market'))
  if (path === '/' && mode !== 'aislos') return navigateTo(localized(portal.home))
  if (!isPhysicalPathAllowed(path)) {
    const owner = ownerForPath(path)
    const target = owner === 'customer'
      ? buildExternalUrl(urls.customer, localized('/'))
      : buildExternalUrl(urls[owner], to.fullPath)
    return navigateTo(target, { external: true })
  }

  const cebuPublicPaths = [
    '/market',
    '/market/categories',
    '/market/how-it-works',
    '/market/marketplace',
    '/market/pricing',
    '/market/trust-safety',
    '/market/post-request',
    '/register-buyer',
    '/register-role',
    '/register-supplier',
  ]
  const isCebuPublic = cebuPublicPaths.includes(path) || path.startsWith('/market/marketplace/')

  const targetKey = path === '/portal' || path.startsWith('/portal/') ? 'customer_pc'
    : ((path.startsWith('/market/') && !isCebuPublic) || path.startsWith('/buyer/')) ? 'cebu_buyer_pc'
      : path === '/supplier' || path.startsWith('/supplier/') || path === '/supplier-onboarding' ? 'supplier_pc'
        : path === '/partner' || path.startsWith('/partner/') ? 'partner_company_pc'
          : path === '/procurement' || path.startsWith('/procurement/') ? 'procurement'
            : path === '/developers' || path.startsWith('/developers/') || path === '/marketplace' || path.startsWith('/marketplace/') ? 'developer'
              : path === '/store' || path.startsWith('/store/') || path === '/products' || path.startsWith('/products/') ? 'store'
                : 'consumer_pc'

  if (loadedKey.value !== targetKey) await load(targetKey)
  if (!manifest.value) {
    return abortNavigation(createError({ statusCode: 404, statusMessage: 'Unknown portal route' }))
  }

  const publicPortal = ['consumer_pc', 'store', 'developer'].includes(targetKey)
  const protectedPortal = !publicPortal && manifest.value.required_grants.length > 0
  if (!token.value && protectedPortal) {
    return navigateTo({ path: localized('/login'), query: { redirect: to.fullPath } })
  }
  if (token.value) {
    const accessAvailable = await loadAccess(true)
    if (protectedPortal && !accessAvailable) {
      return abortNavigation(createError({ statusCode: 503, statusMessage: 'Portal access could not be verified' }))
    }
    if (protectedPortal && !isPortalAvailable(targetKey)) {
      return abortNavigation(createError({ statusCode: 403, statusMessage: 'Portal access denied' }))
    }
  }
  if (!isRouteAllowed(path)) {
    return abortNavigation(createError({ statusCode: 403, statusMessage: 'Route is not allowed in this portal' }))
  }
})
