import {
  getLocalePrefixFromPath,
  localeFromPrefix,
  normalizeLocaleCode,
  prefixForLocale,
  withLocalePrefix,
} from '~/utils/localeRoutes'

function codeOfLocale(item: unknown) {
  if (typeof item === 'string') return item
  if (item && typeof item === 'object' && 'code' in item) return String((item as { code: string }).code)
  return ''
}

function valueOfRef<T>(value: T | { value: T }) {
  return value && typeof value === 'object' && 'value' in value ? value.value : value
}

export default defineNuxtRouteMiddleware(async (to) => {
  const { $i18n } = useNuxtApp()
  const i18n = $i18n as any
  const prefixCookie = useCookie<string | null>('ainerwise_locale_prefix', { sameSite: 'lax' })
  const localeCookie = useCookie<string | null>('i18n_locale', { sameSite: 'lax' })
  const supportedLocales = (valueOfRef(i18n.locales) || []).map(codeOfLocale).filter(Boolean)
  const isSupported = (code: string) => !supportedLocales.length || supportedLocales.includes(code)

  async function applyLocale(code: string, prefix: string) {
    if (!isSupported(code)) return false
    prefixCookie.value = prefix
    localeCookie.value = code
    if (import.meta.client) localStorage.setItem('ainerwise_locale_prefix', prefix)
    const currentLocale = valueOfRef(i18n.locale)
    if (currentLocale !== code && typeof i18n.setLocale === 'function') {
      await i18n.setLocale(code)
    } else if (i18n.locale && typeof i18n.locale === 'object' && 'value' in i18n.locale) {
      i18n.locale.value = code
    }
    return true
  }

  const prefix = getLocalePrefixFromPath(to.path)
  if (prefix) {
    await applyLocale(localeFromPrefix(prefix), prefix)
    return
  }

  const requested = normalizeLocaleCode(String(to.query.lang || ''))
  const requestedPrefix = prefixForLocale(requested)
  if (requested && requestedPrefix && isSupported(requested)) {
    prefixCookie.value = requestedPrefix
    localeCookie.value = requested
    if (import.meta.client) localStorage.setItem('ainerwise_locale_prefix', requestedPrefix)
    return navigateTo(withLocalePrefix(to.fullPath, requestedPrefix), { replace: true })
  }

  const savedPrefix = import.meta.client
    ? localStorage.getItem('ainerwise_locale_prefix') || prefixCookie.value || ''
    : prefixCookie.value || ''
  const savedLocale = localeFromPrefix(savedPrefix)
  if (savedPrefix && savedLocale && isSupported(savedLocale)) {
    return navigateTo(withLocalePrefix(to.fullPath, savedPrefix), { replace: true })
  }

  if (import.meta.client) {
    const savedCookieLocale = normalizeLocaleCode(localeCookie.value || '')
    const savedCookiePrefix = prefixForLocale(savedCookieLocale)
    if (savedCookieLocale && savedCookiePrefix && isSupported(savedCookieLocale)) {
      localStorage.setItem('ainerwise_locale_prefix', savedCookiePrefix)
      return navigateTo(withLocalePrefix(to.fullPath, savedCookiePrefix), { replace: true })
    }

    const browserLocale = (navigator.languages || [navigator.language || ''])
      .map(value => normalizeLocaleCode(String(value).split('-')[0] || value))
      .find(code => code && isSupported(code))
      || 'en'
    const browserPrefix = prefixForLocale(browserLocale)
    if (browserPrefix) {
      return navigateTo(withLocalePrefix(to.fullPath, browserPrefix), { replace: true })
    }
  }
})
