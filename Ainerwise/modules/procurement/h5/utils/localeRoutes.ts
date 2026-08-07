export const URI_LOCALE_PREFIX_TO_H5_LOCALE: Record<string, string> = {
  en: 'en',
  cn: 'zh',
  rs: 'sr',
  pl: 'pl',
}

export const H5_LOCALE_TO_URI_PREFIX: Record<string, string> = {
  en: 'en',
  zh: 'cn',
  sr: 'rs',
  pl: 'pl',
}

export function normalizeH5Locale(value?: string | null) {
  const raw = String(value || '').trim()
  const upper = raw.toUpperCase()
  if (upper === 'ZH' || upper === 'CN' || upper === 'ZH-CN') return 'zh'
  if (upper === 'SR' || upper === 'RS' || upper === 'SR-RS') return 'sr'
  if (upper === 'PL' || upper === 'PL-PL') return 'pl'
  const primary = raw.split(/[-_]/)[0]?.toLowerCase()
  if (primary === 'zh') return 'zh'
  if (primary === 'sr') return 'sr'
  if (primary === 'pl') return 'pl'
  if (primary === 'en') return 'en'
  return raw.toLowerCase()
}

export function getLocalePrefixFromPath(path: string) {
  const first = (path.split('?')[0]?.split('#')[0]?.split('/').filter(Boolean)[0] || '').toLowerCase()
  return URI_LOCALE_PREFIX_TO_H5_LOCALE[first] ? first : ''
}

export function localeFromPrefix(prefix: string) {
  return URI_LOCALE_PREFIX_TO_H5_LOCALE[prefix.toLowerCase()] || ''
}

export function stripLocalePrefix(path: string) {
  const [pathAndQuery, hash = ''] = String(path || '/').split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length && URI_LOCALE_PREFIX_TO_H5_LOCALE[parts[0].toLowerCase()]) parts.shift()
  const cleanPath = parts.length ? `/${parts.join('/')}` : '/'
  return `${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}

export function withLocalePrefix(path: string, prefix: string) {
  const normalizedPrefix = prefix.toLowerCase()
  if (!URI_LOCALE_PREFIX_TO_H5_LOCALE[normalizedPrefix]) return stripLocalePrefix(path)
  const stripped = stripLocalePrefix(path)
  const [pathAndQuery, hash = ''] = stripped.split('#')
  const [pathname, query = ''] = pathAndQuery.split('?')
  const cleanPath = pathname === '/' ? '' : pathname
  return `/${normalizedPrefix}${cleanPath}${query ? `?${query}` : ''}${hash ? `#${hash}` : ''}`
}
