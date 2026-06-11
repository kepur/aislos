export default defineNuxtRouteMiddleware((to) => {
  const { mode, portal, urls, ownerForPath, isPathAllowed } = usePortalMode()

  if (to.path === '/' && mode !== 'aislos') {
    return navigateTo(portal.home)
  }
  if (isPathAllowed(to.path)) return

  const owner = ownerForPath(to.path)
  const target = `${urls[owner]}${to.fullPath}`
  return navigateTo(target, { external: true })
})
