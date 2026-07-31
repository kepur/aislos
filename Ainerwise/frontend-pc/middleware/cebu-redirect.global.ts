// P0-3: legacy /cebu/* routes renamed to /market/*. Permanent-redirect old paths.
// Runs before portal.global.ts (alphabetical order). API paths (/cebu-compat,
// /cebu-trade) are never Vue routes, so they are unaffected.
import { getLocalePrefixFromPath, stripLocalePrefix, withLocalePrefix } from '~/utils/localeRoutes'

export default defineNuxtRouteMiddleware((to) => {
  const prefix = getLocalePrefixFromPath(to.path)
  const path = stripLocalePrefix(to.path)
  if (path === '/cebu' || path.startsWith('/cebu/')) {
    const target = path.replace(/^\/cebu/, '/market')
    const localizedTarget = prefix ? withLocalePrefix(target, prefix) : target
    return navigateTo({ path: localizedTarget, query: to.query, hash: to.hash }, { redirectCode: 301 })
  }
})
