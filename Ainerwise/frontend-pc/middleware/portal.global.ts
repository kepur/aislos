export default defineNuxtRouteMiddleware((to) => {
  const { mode, portal, urls, ownerForPath, isPathAllowed } = usePortalMode()

  if (to.path === '/' && mode !== 'aislos') {
    return navigateTo(portal.home)
  }
  if (to.path === '/portal' || to.path.startsWith('/portal/')) {
    const suffix = to.fullPath.replace(/^\/portal/, '') || '/'
    return navigateTo(`${urls.customer}${suffix}`, { external: true })
  }
  if (to.path === '/procurement' || to.path.startsWith('/procurement/')) return
  if (isPathAllowed(to.path)) return

  const owner = ownerForPath(to.path)
  const target = `${urls[owner]}${to.fullPath}`
  return navigateTo(target, { external: true })
})
