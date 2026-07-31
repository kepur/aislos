import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn, isAdmin } = useAuth()
  const prefix = getLocalePrefixFromPath(to.path)
  const localized = (target: string) => prefix ? withLocalePrefix(target, prefix) : target

  if (isLoggedIn.value) {
    if (isAdmin.value) {
      return navigateTo(localized('/admin'))
    }
    return navigateTo(localized('/portal'))
  }
})
