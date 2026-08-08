import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const appStore = useAppStore()
  const prefix = getLocalePrefixFromPath(to.path) || appStore.routeLocalePrefix
  const target = prefix ? withLocalePrefix('/marketplace', prefix) : '/marketplace'
  return navigateTo(target, { replace: true })
})
