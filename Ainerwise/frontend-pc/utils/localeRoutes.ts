export const URI_LOCALE_PREFIX_TO_LOCALE: Record<string, string> = {
  en: 'en',
  cn: 'zh',
  rs: 'sr',
  ba: 'bs',
  pl: 'pl',
  de: 'de',
  ro: 'ro',
}

export const LOCALE_TO_URI_PREFIX: Record<string, string> = {
  en: 'en',
  zh: 'cn',
  sr: 'rs',
  bs: 'ba',
  pl: 'pl',
  de: 'de',
  ro: 'ro',
}

export function normalizeLocaleCode(value?: string | null) {
  const raw = String(value || '').trim()
  const upper = raw.toUpperCase()
  if (upper === 'CN' || upper === 'ZH-CN') return 'zh'
  if (upper === 'RS' || upper === 'SR-LATN') return 'sr'
  if (upper === 'BA') return 'bs'
  return raw.toLowerCase()
}

export function getLocalePrefixFromPath(path: string) {
  const first = (path.split('?')[0]?.split('#')[0]?.split('/').filter(Boolean)[0] || '').toLowerCase()
  return URI_LOCALE_PREFIX_TO_LOCALE[first] ? first : ''
}

export function localeFromPrefix(prefix: string) {
  return URI_LOCALE_PREFIX_TO_LOCALE[prefix.toLowerCase()] || ''
}

export function prefixForLocale(locale: string) {
  return LOCALE_TO_URI_PREFIX[normalizeLocaleCode(locale)] || ''
}

export function stripLocalePrefix(path: string) {
  const [pathAndQuery, hash = ''] = String(path || '/').split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length && URI_LOCALE_PREFIX_TO_LOCALE[parts[0].toLowerCase()]) parts.shift()
  const cleanPath = parts.length ? `/${parts.join('/')}` : '/'
  return `${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}

export function withLocalePrefix(path: string, prefix: string) {
  const normalizedPrefix = prefix.toLowerCase()
  if (!URI_LOCALE_PREFIX_TO_LOCALE[normalizedPrefix]) return stripLocalePrefix(path)
  const stripped = stripLocalePrefix(path)
  const [pathAndQuery, hash = ''] = stripped.split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const cleanPath = pathname === '/' ? '' : pathname
  return `/${normalizedPrefix}${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}
