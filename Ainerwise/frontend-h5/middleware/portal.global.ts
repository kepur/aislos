export default defineNuxtRouteMiddleware((to) => {
  const { mode, portal, urls, ownerForPath, isPathAllowed } = usePortalMode()

  if (to.path === '/' && mode !== 'customer') {
    return navigateTo(portal.home)
  }
  if (isPathAllowed(to.path)) return

  const owner = ownerForPath(to.path)
  return navigateTo(`${urls[owner]}${to.fullPath}`, { external: true })
})
