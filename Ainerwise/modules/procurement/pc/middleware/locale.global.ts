import {
  getLocalePrefixFromPath,
  languageFromLocalePrefix,
  normalizeLanguageCode,
  withLocalePrefix,
} from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const appStore = useAppStore()
  const prefix = getLocalePrefixFromPath(to.path)

  if (prefix) {
    appStore.setRouteLocalePrefix(prefix)
    appStore.setLanguage(languageFromLocalePrefix(prefix))
    return
  }

  const requested = normalizeLanguageCode(String(to.query.lang || ''))
  if (requested) {
    appStore.setLanguage(requested)
    const targetPrefix = appStore.prefixForLanguage(requested)
    if (targetPrefix) {
      appStore.setRouteLocalePrefix(targetPrefix)
      return navigateTo(withLocalePrefix(to.fullPath, targetPrefix), { replace: true })
    }
    return
  }

  if (import.meta.client && appStore.routeLocalePrefix) {
    return navigateTo(withLocalePrefix(to.fullPath, appStore.routeLocalePrefix), { replace: true })
  }
})
