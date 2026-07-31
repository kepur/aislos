export const URI_LOCALE_PREFIX_TO_LANGUAGE: Record<string, string> = {
  en: 'EN',
  cn: 'ZH',
  rs: 'SR',
  ba: 'BS',
  pl: 'PL',
  de: 'DE',
  ro: 'RO',
}

export const LANGUAGE_TO_URI_LOCALE_PREFIX: Record<string, string> = {
  EN: 'en',
  ZH: 'cn',
  SR: 'rs',
  BS: 'ba',
  PL: 'pl',
  DE: 'de',
  RO: 'ro',
}

export function normalizeLanguageCode(value?: string | null) {
  const normalized = String(value || '').trim().toUpperCase()
  if (normalized === 'CN' || normalized === 'ZH-CN') return 'ZH'
  if (normalized === 'RS' || normalized === 'SR-LATN') return 'SR'
  return normalized
}

export function getLocalePrefixFromPath(path: string) {
  const first = (path.split('?')[0]?.split('#')[0]?.split('/').filter(Boolean)[0] || '').toLowerCase()
  return URI_LOCALE_PREFIX_TO_LANGUAGE[first] ? first : ''
}

export function languageFromLocalePrefix(prefix: string) {
  return URI_LOCALE_PREFIX_TO_LANGUAGE[prefix.toLowerCase()] || ''
}

export function stripLocalePrefix(path: string) {
  const [pathAndQuery, hash = ''] = String(path || '/').split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length && URI_LOCALE_PREFIX_TO_LANGUAGE[parts[0].toLowerCase()]) {
    parts.shift()
  }
  const cleanPath = parts.length ? `/${parts.join('/')}` : '/'
  return `${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}

export function withLocalePrefix(path: string, prefix: string) {
  const normalizedPrefix = prefix.toLowerCase()
  if (!URI_LOCALE_PREFIX_TO_LANGUAGE[normalizedPrefix]) return stripLocalePrefix(path)
  const stripped = stripLocalePrefix(path)
  const [pathAndQuery, hash = ''] = stripped.split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const cleanPath = pathname === '/' ? '' : pathname
  return `/${normalizedPrefix}${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}
