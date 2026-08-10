import { prefixForLocale } from '~/utils/localeRoutes'

/**
 * Keep in-site links on the language the visitor is reading.
 *
 * The interface language lives in the i18n locale (cookie-backed); the URL
 * prefix (/cn, /rs, /en...) is derived from it. An earlier version of this
 * helper took the prefix from the *current path* instead — which broke the
 * moment path and locale disagreed: reading English on a stale /cn URL, every
 * click re-attached /cn and the locale sync dragged the interface back to
 * Chinese. Deriving the prefix from the locale makes links follow the language
 * the visitor actually sees, whatever the current URL says.
 */
export function useLocalizedLink() {
  const { locale } = useI18n({ useScope: 'global' })
  const prefix = computed(() => prefixForLocale(locale.value) || '')

  function localized(path?: string | null) {
    // Some links are optional (a grid item with no `to`); guard so an absent
    // path can never crash the render.
    if (!path || !path.startsWith('/')) return path ?? undefined
    if (!prefix.value) return path
    // withLocalePrefix strips any existing prefix first, so stale ones can't
    // stack (imported lazily to avoid a circular utils dependency at SSR).
    const clean = path.replace(/^\/(en|cn|rs|ba|pl|de|ro)(?=\/|\?|#|$)/, '') || '/'
    const [pathAndQuery, hash = ''] = clean.split('#')
    const [pathname, query = ''] = pathAndQuery.split('?')
    const core = pathname === '/' ? '' : pathname
    return `/${prefix.value}${core}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
  }

  return { localized, localePrefix: prefix }
}
