/**
 * Locale-aware date/money formatting.
 *
 * The components used to call `Intl.DateTimeFormat(undefined, …)` and bare
 * `toLocaleDateString()`, which fall back to the *runtime* default locale
 * (zh here) — so a Serbian or English page rendered Chinese "8月4日" dates.
 * These helpers format against the active i18n locale instead, so dates and
 * numbers follow the language the visitor actually selected.
 */
const BCP47: Record<string, string> = {
  zh: 'zh-CN',
  sr: 'sr-Latn',
  en: 'en',
  pl: 'pl',
}

export function useLocaleFormat() {
  const { locale } = useI18n({ useScope: 'global' })
  const tag = computed(() => BCP47[locale.value] || locale.value || 'en')

  const DATE_TIME: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }

  function formatDate(value?: string | number | Date | null, opts?: Intl.DateTimeFormatOptions) {
    if (!value) return '—'
    try {
      return new Intl.DateTimeFormat(tag.value, opts || DATE_TIME).format(new Date(value))
    } catch {
      return String(value)
    }
  }

  function formatDay(value?: string | number | Date | null) {
    return formatDate(value, { year: 'numeric', month: 'short', day: 'numeric' })
  }

  function formatTime(value?: string | number | Date | null) {
    return formatDate(value, { hour: '2-digit', minute: '2-digit' })
  }

  function formatMoney(minor?: number | null, currency = 'EUR', maximumFractionDigits = 2) {
    if (minor == null) return '—'
    try {
      return new Intl.NumberFormat(tag.value, { style: 'currency', currency, maximumFractionDigits }).format(minor / 100)
    } catch {
      return `${(minor / 100).toLocaleString(tag.value)} ${currency}`
    }
  }

  return { formatDate, formatDay, formatTime, formatMoney, localeTag: tag }
}
