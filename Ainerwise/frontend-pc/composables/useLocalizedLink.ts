import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

/**
 * Keep in-site links on the language the visitor is already reading.
 *
 * Locale lives in the URL as a prefix (/cn/market/..., /rs/portal/...), added
 * by page aliases rather than by the router. A `<NuxtLink to="/market/...">`
 * therefore resolves to the unprefixed alias, which drops the visitor back to
 * the default locale — clicking a nav item while reading Chinese landed on the
 * English page.
 *
 * `localized()` re-attaches whatever prefix the current route carries, and is a
 * no-op on the default locale.
 */
export function useLocalizedLink() {
  const route = useRoute()
  const prefix = computed(() => getLocalePrefixFromPath(route.path))

  function localized(path?: string | null) {
    // Some links are optional (a grid item with no `to`); guard so an absent
    // path can never crash the render.
    if (!path || !path.startsWith('/')) return path ?? undefined
    return prefix.value ? withLocalePrefix(path, prefix.value) : path
  }

  return { localized, localePrefix: prefix }
}
