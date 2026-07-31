import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const { isLoggedIn, isAdmin } = useAuth()
  const prefix = getLocalePrefixFromPath(to.path)
  const localized = (target: string) => prefix ? withLocalePrefix(target, prefix) : target

  if (!isLoggedIn.value) {
    return navigateTo(localized('/login'))
  }

  if (!isAdmin.value) {
    return navigateTo(localized('/'))
  }
})
