export type CurrencyPolicy = {
  country_code: string
  country_name: string
  local_currency: string
  local_currency_alias?: string
  default_settlement_currency: string
  default_transaction_mode?: string
  enabled_currencies: string[]
  settlement_currencies?: string[]
  cross_border_currencies?: string[]
  reference_rates?: Record<string, number | string>
  rate_source?: string
  is_active?: boolean
  source?: string
}

export type CurrencyMeta = {
  code: string
  name: string
  symbol?: string
  alias?: string
  locale: string
  minorUnit: number
}

export const CURRENCY_META: Record<string, CurrencyMeta> = {
  EUR: { code: 'EUR', name: 'Euro', symbol: '€', locale: 'de-DE', minorUnit: 2 },
  RSD: { code: 'RSD', name: 'Serbian Dinar', symbol: 'дин.', alias: 'DIN', locale: 'sr-RS', minorUnit: 2 },
  PLN: { code: 'PLN', name: 'Polish Zloty', symbol: 'zł', locale: 'pl-PL', minorUnit: 2 },
  BAM: { code: 'BAM', name: 'Bosnia Convertible Mark', symbol: 'KM', locale: 'bs-BA', minorUnit: 2 },
  RON: { code: 'RON', name: 'Romanian Leu', symbol: 'lei', locale: 'ro-RO', minorUnit: 2 },
  PHP: { code: 'PHP', name: 'Philippine Peso', symbol: '₱', locale: 'en-PH', minorUnit: 2 },
  USD: { code: 'USD', name: 'US Dollar', symbol: '$', locale: 'en-US', minorUnit: 2 },
  CNY: { code: 'CNY', name: 'Chinese Yuan', symbol: '¥', locale: 'zh-CN', minorUnit: 2 },
  GBP: { code: 'GBP', name: 'British Pound', symbol: '£', locale: 'en-GB', minorUnit: 2 },
  CAD: { code: 'CAD', name: 'Canadian Dollar', symbol: '$', locale: 'en-CA', minorUnit: 2 },
  AUD: { code: 'AUD', name: 'Australian Dollar', symbol: '$', locale: 'en-AU', minorUnit: 2 },
  SGD: { code: 'SGD', name: 'Singapore Dollar', symbol: '$', locale: 'en-SG', minorUnit: 2 },
  HKD: { code: 'HKD', name: 'Hong Kong Dollar', symbol: '$', locale: 'en-HK', minorUnit: 2 },
  JPY: { code: 'JPY', name: 'Japanese Yen', symbol: '¥', locale: 'ja-JP', minorUnit: 0 },
  KRW: { code: 'KRW', name: 'Korean Won', symbol: '₩', locale: 'ko-KR', minorUnit: 0 },
  AED: { code: 'AED', name: 'UAE Dirham', locale: 'en-AE', minorUnit: 2 },
  INR: { code: 'INR', name: 'Indian Rupee', symbol: '₹', locale: 'en-IN', minorUnit: 2 },
  THB: { code: 'THB', name: 'Thai Baht', symbol: '฿', locale: 'th-TH', minorUnit: 2 },
  USDT: { code: 'USDT', name: 'Tether', symbol: '₮', locale: 'en-US', minorUnit: 2 },
}

export const FALLBACK_PAYMENT_POLICIES: Record<string, CurrencyPolicy> = {
  RS: {
    country_code: 'RS',
    country_name: 'Serbia',
    local_currency: 'RSD',
    local_currency_alias: 'DIN',
    default_settlement_currency: 'EUR',
    default_transaction_mode: 'SETTLEMENT_WITH_LOCAL_REFERENCE',
    enabled_currencies: ['EUR', 'RSD'],
    settlement_currencies: ['EUR', 'RSD'],
    cross_border_currencies: ['EUR'],
    reference_rates: {
      'EUR:RSD': 117.2,
      'RSD:EUR': 0.00853242,
    },
    rate_source: 'STATIC_POLICY_REFERENCE',
    is_active: true,
    source: 'frontend_fallback',
  },
  PL: {
    country_code: 'PL',
    country_name: 'Poland',
    local_currency: 'PLN',
    default_settlement_currency: 'PLN',
    default_transaction_mode: 'LOCAL_OR_EUR_SETTLEMENT',
    enabled_currencies: ['PLN', 'EUR'],
    settlement_currencies: ['PLN', 'EUR'],
    cross_border_currencies: ['EUR'],
    reference_rates: {
      'EUR:PLN': 4.3,
      'PLN:EUR': 0.23255814,
    },
    rate_source: 'STATIC_POLICY_REFERENCE',
    is_active: true,
    source: 'frontend_fallback',
  },
  PH: {
    country_code: 'PH',
    country_name: 'Philippines',
    local_currency: 'PHP',
    default_settlement_currency: 'PHP',
    default_transaction_mode: 'LOCAL_ONLY',
    enabled_currencies: ['PHP', 'USD'],
    settlement_currencies: ['PHP', 'USD'],
    cross_border_currencies: ['USD'],
    reference_rates: {},
    rate_source: 'NONE',
    is_active: true,
    source: 'frontend_fallback',
  },
  BA: {
    country_code: 'BA',
    country_name: 'Bosnia and Herzegovina',
    local_currency: 'BAM',
    default_settlement_currency: 'EUR',
    default_transaction_mode: 'SETTLEMENT_WITH_LOCAL_REFERENCE',
    enabled_currencies: ['EUR', 'BAM'],
    settlement_currencies: ['EUR', 'BAM'],
    cross_border_currencies: ['EUR'],
    reference_rates: {
      'EUR:BAM': 1.95583,
      'BAM:EUR': 0.51129188,
    },
    rate_source: 'STATIC_POLICY_REFERENCE',
    is_active: true,
    source: 'frontend_fallback',
  },
  RO: {
    country_code: 'RO',
    country_name: 'Romania',
    local_currency: 'RON',
    default_settlement_currency: 'RON',
    default_transaction_mode: 'LOCAL_OR_EUR_SETTLEMENT',
    enabled_currencies: ['RON', 'EUR'],
    settlement_currencies: ['RON', 'EUR'],
    cross_border_currencies: ['EUR'],
    reference_rates: {},
    rate_source: 'REQUIRES_FX_QUOTE',
    is_active: true,
    source: 'frontend_fallback',
  },
}

export function normalizeCurrencyCode(code?: string | null, fallback = 'EUR') {
  return String(code || fallback).trim().toUpperCase()
}

export function normalizePaymentPolicy(raw?: Record<string, any> | null, country = 'RS'): CurrencyPolicy {
  const normalizedCountry = String(raw?.country_code || country || 'RS').toUpperCase().slice(0, 2)
  const fallback = FALLBACK_PAYMENT_POLICIES[normalizedCountry] || {
    country_code: normalizedCountry,
    country_name: normalizedCountry,
    local_currency: 'EUR',
    default_settlement_currency: 'EUR',
    default_transaction_mode: 'LOCAL_ONLY',
    enabled_currencies: ['EUR'],
    settlement_currencies: ['EUR'],
    cross_border_currencies: [],
    reference_rates: {},
    rate_source: 'REQUIRES_REGION_CONFIG',
    is_active: true,
    source: 'generated_fallback',
  }

  const localCurrency = normalizeCurrencyCode(raw?.local_currency, fallback.local_currency)
  const defaultSettlement = normalizeCurrencyCode(raw?.default_settlement_currency, fallback.default_settlement_currency)
  const enabled = normalizeCurrencyList(raw?.enabled_currencies, fallback.enabled_currencies)
  const settlement = normalizeCurrencyList(raw?.settlement_currencies, raw?.enabled_currencies || fallback.settlement_currencies || enabled)

  return {
    ...fallback,
    ...(raw || {}),
    country_code: normalizedCountry,
    country_name: String(raw?.country_name || fallback.country_name || normalizedCountry),
    local_currency: localCurrency,
    local_currency_alias: String(raw?.local_currency_alias || fallback.local_currency_alias || ''),
    default_settlement_currency: defaultSettlement,
    default_transaction_mode: String(raw?.default_transaction_mode || fallback.default_transaction_mode || 'LOCAL_ONLY'),
    enabled_currencies: enabled.length ? enabled : [defaultSettlement],
    settlement_currencies: settlement.length ? settlement : [defaultSettlement],
    cross_border_currencies: normalizeCurrencyList(raw?.cross_border_currencies, fallback.cross_border_currencies || []),
    reference_rates: { ...(fallback.reference_rates || {}), ...((raw?.reference_rates || {}) as Record<string, number | string>) },
    rate_source: String(raw?.rate_source || fallback.rate_source || 'REQUIRES_FX_QUOTE'),
    is_active: raw?.is_active ?? fallback.is_active ?? true,
    source: String(raw?.source || fallback.source || 'core'),
  }
}

export function normalizeCurrencyList(value: unknown, fallback: string[] = []) {
  const raw = Array.isArray(value) ? value : fallback
  return Array.from(new Set(raw.map((item) => normalizeCurrencyCode(String(item))).filter(Boolean)))
}

export function currencyMeta(code?: string | null): CurrencyMeta {
  const normalized = normalizeCurrencyCode(code)
  return CURRENCY_META[normalized] || { code: normalized, name: normalized, locale: 'en', minorUnit: 2 }
}

export function currencyOptionLabel(code?: string | null) {
  const meta = currencyMeta(code)
  return meta.alias ? `${meta.code} / ${meta.alias} - ${meta.name}` : `${meta.code} - ${meta.name}`
}

export function localCurrencyLabel(policy?: CurrencyPolicy | null) {
  const normalized = normalizePaymentPolicy(policy, policy?.country_code || 'RS')
  const meta = currencyMeta(normalized.local_currency)
  return normalized.local_currency_alias
    ? `${meta.code} / ${normalized.local_currency_alias}`
    : meta.code
}

export function localeForLanguage(language?: string | null, currency?: string | null) {
  const lang = String(language || '').toUpperCase()
  if (lang === 'ZH') return 'zh-CN'
  if (lang === 'SR') return 'sr-RS'
  if (lang === 'BS') return 'bs-BA'
  if (lang === 'PL') return 'pl-PL'
  if (lang === 'DE') return 'de-DE'
  if (lang === 'RO') return 'ro-RO'
  return currencyMeta(currency).locale || 'en'
}

export function formatMoneyMinor(minor: number | null | undefined, currency?: string | null, locale?: string | null) {
  const normalized = normalizeCurrencyCode(currency)
  const meta = currencyMeta(normalized)
  const amount = Number(minor || 0) / 100
  try {
    return new Intl.NumberFormat(locale || meta.locale || 'en', {
      style: 'currency',
      currency: normalized,
      minimumFractionDigits: meta.minorUnit === 0 ? 0 : 2,
      maximumFractionDigits: meta.minorUnit === 0 ? 0 : 2,
    }).format(amount)
  } catch {
    return `${amount.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${normalized}`
  }
}

export function rateFor(policy: CurrencyPolicy | null | undefined, fromCurrency: string, toCurrency: string): number | null {
  const from = normalizeCurrencyCode(fromCurrency)
  const to = normalizeCurrencyCode(toCurrency)
  if (from === to) return 1
  const normalized = normalizePaymentPolicy(policy, policy?.country_code || 'RS')
  const raw = normalized.reference_rates?.[`${from}:${to}`]
  const value = raw == null ? NaN : Number(raw)
  return Number.isFinite(value) && value > 0 ? value : null
}

export function convertMinorReference(
  minor: number | null | undefined,
  fromCurrency: string,
  toCurrency: string,
  policy?: CurrencyPolicy | null,
) {
  const rate = rateFor(policy, fromCurrency, toCurrency)
  if (rate == null) return null
  return Math.round(Number(minor || 0) * rate)
}
