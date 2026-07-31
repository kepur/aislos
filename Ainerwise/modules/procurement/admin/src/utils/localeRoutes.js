export const URI_LOCALE_PREFIX_TO_ADMIN_LOCALE = {
  en: 'en',
  cn: 'zh',
  rs: 'sr',
}

export const ADMIN_LOCALE_TO_URI_PREFIX = {
  en: 'en',
  zh: 'cn',
  sr: 'rs',
}

export const ADMIN_LOCALE_PREFIXES = Object.keys(URI_LOCALE_PREFIX_TO_ADMIN_LOCALE)

export function normalizeAdminLocale(value = '') {
  const raw = String(value || '').trim()
  const upper = raw.toUpperCase()
  if (upper === 'CN' || upper === 'ZH-CN') return 'zh'
  if (upper === 'RS' || upper === 'SR-LATN') return 'sr'
  return raw.toLowerCase()
}

export function getLocalePrefixFromPath(path = '/') {
  const first = String(path || '/').split('?')[0].split('#')[0].split('/').filter(Boolean)[0] || ''
  const prefix = first.toLowerCase()
  return URI_LOCALE_PREFIX_TO_ADMIN_LOCALE[prefix] ? prefix : ''
}

export function localeFromPrefix(prefix = '') {
  return URI_LOCALE_PREFIX_TO_ADMIN_LOCALE[String(prefix || '').toLowerCase()] || ''
}

export function prefixForLocale(locale = '') {
  return ADMIN_LOCALE_TO_URI_PREFIX[normalizeAdminLocale(locale)] || ''
}

export function stripLocalePrefix(path = '/') {
  const [pathAndQuery, hash = ''] = String(path || '/').split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length && URI_LOCALE_PREFIX_TO_ADMIN_LOCALE[parts[0].toLowerCase()]) parts.shift()
  const cleanPath = parts.length ? `/${parts.join('/')}` : '/'
  return `${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}

export function withLocalePrefix(path = '/', prefix = '') {
  const normalizedPrefix = String(prefix || '').toLowerCase()
  if (!URI_LOCALE_PREFIX_TO_ADMIN_LOCALE[normalizedPrefix]) return stripLocalePrefix(path)
  const stripped = stripLocalePrefix(path)
  const [pathAndQuery, hash = ''] = stripped.split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const cleanPath = pathname === '/' ? '' : pathname
  return `/${normalizedPrefix}${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}

export function currentLocalePrefix(path = '') {
  const routePrefix = getLocalePrefixFromPath(path || window.location.pathname)
  if (routePrefix) return routePrefix
  const savedPrefix = localStorage.getItem('admin_locale_prefix') || ''
  if (URI_LOCALE_PREFIX_TO_ADMIN_LOCALE[savedPrefix]) return savedPrefix
  return prefixForLocale(localStorage.getItem('admin_locale') || 'en') || 'en'
}

export function applyRouteLocale(path, i18nLocaleRef, applyDirection) {
  const prefix = getLocalePrefixFromPath(path)
  if (!prefix) return ''
  const nextLocale = localeFromPrefix(prefix)
  if (nextLocale) {
    i18nLocaleRef.value = nextLocale
    localStorage.setItem('admin_locale', nextLocale)
    localStorage.setItem('admin_locale_prefix', prefix)
    applyDirection(nextLocale)
  }
  return prefix
}
