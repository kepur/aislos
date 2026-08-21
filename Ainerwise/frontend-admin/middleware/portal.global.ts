import { getLocalePrefixFromPath, stripLocalePrefix, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware(async (to) => {
  const { mode, portal, urls, ownerForPath, isPathAllowed: isPhysicalPathAllowed } = usePortalMode()
  const { token, clearAuth } = useAuth()
  const { manifest, loadedKey, accessStatus, isRouteAllowed, isPortalAvailable, load, loadAccess } = usePortalManifest()
  const buildExternalUrl = (base: string, fullPath: string) => `${base.replace(/\/$/, '')}${fullPath}`
  const localePrefix = getLocalePrefixFromPath(to.path)
  const path = stripLocalePrefix(to.path)
  const localized = (target: string) => localePrefix ? withLocalePrefix(target, localePrefix) : target

  if (path === '/login') return
  if (path === '/' && mode !== 'aislos') return navigateTo(localized(portal.home))
  if (!isPhysicalPathAllowed(path)) {
    const owner = ownerForPath(path)
    return navigateTo(buildExternalUrl(urls[owner], to.fullPath), { external: true })
  }

  const targetKey = path === '/' || path.startsWith('/dashboard') ? 'admin_executive'
    : path.startsWith('/leads') || path.startsWith('/inquiries') || path.startsWith('/crm') || path.startsWith('/tickets') ? 'admin_crm'
      : path.startsWith('/solutions') || path.startsWith('/proposals') || path.startsWith('/quotes') ? 'admin_ai_solution'
        : path.startsWith('/rfqs') || path.startsWith('/procurement') ? 'admin_procurement'
          : ['/vendors', '/products', '/inventory', '/categories', '/service-packages', '/compatibility', '/warranty-policies', '/supplier-warranties', '/supplier-scorecards'].some(prefix => path === prefix || path.startsWith(`${prefix}/`)) ? 'admin_supplier_ops'
            : path.startsWith('/service-partners') || path.startsWith('/certifications') ? 'admin_partner'
              : path.startsWith('/field-ops') ? 'admin_field_ops'
                : path.startsWith('/projects') ? 'admin_project'
                  : ['/lifecycle-dashboard', '/assets', '/sites', '/amc-contracts', '/monitoring-points', '/maintenance', '/calibration', '/customer-warranties', '/renewal-queue'].some(prefix => path === prefix || path.startsWith(`${prefix}/`)) ? 'admin_asset'
                    : path.startsWith('/project-finance') || path.startsWith('/finance') || path.startsWith('/platform-fee-rules') || path.startsWith('/commerce/reconciliation') ? 'admin_finance'
                      : ['/payments', '/payment-plans', '/store-orders', '/commerce'].some(prefix => path === prefix || path.startsWith(`${prefix}/`)) ? 'admin_commerce'
                      : path.startsWith('/growth') ? 'admin_growth'
                      : ['/marketing', '/marketing-studio', '/seo'].some(prefix => path === prefix || path.startsWith(`${prefix}/`)) ? 'marketing_pc'
                        : ['/agents', '/agent-missions', '/business-brain', '/ai-runs', '/ai-reviews', '/marketplace'].some(prefix => path === prefix || path.startsWith(`${prefix}/`)) ? 'admin_ai_supervisor'
                          : path.startsWith('/knowledge') || path.startsWith('/case-library') ? 'admin_knowledge'
                            : 'admin_audit'

  if (loadedKey.value !== targetKey) await load(targetKey)
  if (!token.value) return navigateTo({ path: localized('/login'), query: { redirect: to.fullPath } })
  if (!manifest.value) {
    return abortNavigation(createError({ statusCode: 404, statusMessage: 'Unknown admin portal' }))
  }
  const accessAvailable = await loadAccess(true)
  if (!accessAvailable) {
    if (accessStatus.value === 401 || accessStatus.value === 403) {
      clearAuth()
      return navigateTo({ path: localized('/login'), query: { redirect: to.fullPath } })
    }
    return abortNavigation(createError({ statusCode: 503, statusMessage: 'Admin workbench access could not be verified' }))
  }
  if (!isPortalAvailable(targetKey)) {
    return abortNavigation(createError({ statusCode: 403, statusMessage: 'Admin workbench access denied' }))
  }
  if (!isRouteAllowed(path)) {
    return abortNavigation(createError({ statusCode: 403, statusMessage: 'Route is not allowed in this workbench' }))
  }
})
