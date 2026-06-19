export default defineNuxtRouteMiddleware(async (to) => {
  const { mode, portal } = usePortalMode()
  const { token } = useAuth()
  const { manifest, loadedKey, isRouteAllowed, isPortalAvailable, load, loadAccess } = usePortalManifest()

  if (to.path === '/login') return
  if (to.path === '/' && mode !== 'aislos') return navigateTo(portal.home)

  const targetKey = to.path === '/' || to.path.startsWith('/dashboard') ? 'admin_executive'
    : to.path.startsWith('/leads') || to.path.startsWith('/inquiries') || to.path.startsWith('/crm') || to.path.startsWith('/tickets') ? 'admin_crm'
      : to.path.startsWith('/solutions') || to.path.startsWith('/proposals') || to.path.startsWith('/quotes') ? 'admin_ai_solution'
        : to.path.startsWith('/rfqs') || to.path.startsWith('/procurement') ? 'admin_procurement'
          : ['/vendors', '/products', '/inventory', '/categories', '/service-packages', '/compatibility', '/warranty-policies', '/supplier-warranties', '/supplier-scorecards'].some(prefix => to.path === prefix || to.path.startsWith(`${prefix}/`)) ? 'admin_supplier_ops'
            : to.path.startsWith('/service-partners') || to.path.startsWith('/certifications') ? 'admin_partner'
              : to.path.startsWith('/field-ops') ? 'admin_field_ops'
                : to.path.startsWith('/projects') ? 'admin_project'
                  : ['/lifecycle-dashboard', '/assets', '/sites', '/amc-contracts', '/monitoring-points', '/maintenance', '/calibration', '/customer-warranties', '/renewal-queue'].some(prefix => to.path === prefix || to.path.startsWith(`${prefix}/`)) ? 'admin_asset'
                    : to.path.startsWith('/project-finance') || to.path.startsWith('/finance') || to.path.startsWith('/platform-fee-rules') || to.path.startsWith('/commerce/reconciliation') ? 'admin_finance'
                      : ['/payments', '/payment-plans', '/store-orders', '/commerce'].some(prefix => to.path === prefix || to.path.startsWith(`${prefix}/`)) ? 'admin_commerce'
                      : ['/marketing', '/marketing-studio'].some(prefix => to.path === prefix || to.path.startsWith(`${prefix}/`)) ? 'marketing_pc'
                        : ['/agents', '/agent-missions', '/business-brain', '/ai-runs', '/ai-reviews', '/marketplace'].some(prefix => to.path === prefix || to.path.startsWith(`${prefix}/`)) ? 'admin_ai_supervisor'
                          : to.path.startsWith('/knowledge') || to.path.startsWith('/case-library') ? 'admin_knowledge'
                            : 'admin_audit'

  if (loadedKey.value !== targetKey) await load(targetKey)
  if (!token.value) return navigateTo({ path: '/login', query: { redirect: to.fullPath } })
  if (!manifest.value) {
    return abortNavigation(createError({ statusCode: 404, statusMessage: 'Unknown admin portal' }))
  }
  const accessAvailable = await loadAccess(true)
  if (!accessAvailable) {
    return abortNavigation(createError({ statusCode: 503, statusMessage: 'Admin workbench access could not be verified' }))
  }
  if (!isPortalAvailable(targetKey)) {
    return abortNavigation(createError({ statusCode: 403, statusMessage: 'Admin workbench access denied' }))
  }
  if (!isRouteAllowed(to.path)) {
    return abortNavigation(createError({ statusCode: 403, statusMessage: 'Route is not allowed in this workbench' }))
  }
})
