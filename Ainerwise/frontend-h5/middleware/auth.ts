import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn } = useAuth()
  const prefix = getLocalePrefixFromPath(to.path)
  const loginPath = prefix ? withLocalePrefix('/login', prefix) : '/login'

  if (!isLoggedIn.value) {
    return navigateTo(`${loginPath}?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
