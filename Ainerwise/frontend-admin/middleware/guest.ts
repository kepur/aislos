import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn } = useAuth()
  const prefix = getLocalePrefixFromPath(to.path)

  if (isLoggedIn.value) {
    return navigateTo(prefix ? withLocalePrefix('/', prefix) : '/')
  }
})
