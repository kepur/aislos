export type DialOption = {
  countryCode: string
  countryName: string
  dialCode: string
  label: string
  placeholder: string
}

export const CONTACT_DIAL_OPTIONS: DialOption[] = [
  { countryCode: 'RS', countryName: 'Serbia', dialCode: '+381', label: 'Serbia +381', placeholder: '6X XXX XXXX' },
  { countryCode: 'PL', countryName: 'Poland', dialCode: '+48', label: 'Poland +48', placeholder: 'XXX XXX XXX' },
  { countryCode: 'PH', countryName: 'Philippines', dialCode: '+63', label: 'Philippines +63', placeholder: '9XX XXX XXXX' },
  { countryCode: 'BA', countryName: 'Bosnia and Herzegovina', dialCode: '+387', label: 'Bosnia +387', placeholder: '6X XXX XXX' },
  { countryCode: 'RO', countryName: 'Romania', dialCode: '+40', label: 'Romania +40', placeholder: '7XX XXX XXX' },
]

export function dialOptionForCountry(countryCode?: string | null): DialOption {
  const normalized = String(countryCode || '').toUpperCase().slice(0, 2)
  return CONTACT_DIAL_OPTIONS.find((option) => option.countryCode === normalized) || CONTACT_DIAL_OPTIONS[0]
}

export function splitContactNumber(raw?: string | null, fallbackCountryCode = 'RS') {
  const value = String(raw || '').trim()
  const fallback = dialOptionForCountry(fallbackCountryCode)
  if (!value) {
    return { countryCode: fallback.countryCode, dialCode: fallback.dialCode, localNumber: '' }
  }
  const compact = value.replace(/[\s().-]/g, '')
  const matched = CONTACT_DIAL_OPTIONS
    .slice()
    .sort((a, b) => b.dialCode.length - a.dialCode.length)
    .find((option) => compact.startsWith(option.dialCode))
  if (matched) {
    return {
      countryCode: matched.countryCode,
      dialCode: matched.dialCode,
      localNumber: compact.slice(matched.dialCode.length),
    }
  }
  return { countryCode: fallback.countryCode, dialCode: fallback.dialCode, localNumber: value }
}

export function composeContactNumber(countryCode: string, localNumber?: string | null) {
  const local = String(localNumber || '').trim()
  if (!local) return ''
  if (local.startsWith('+')) return local
  const option = dialOptionForCountry(countryCode)
  const normalizedLocal = local.replace(/[^\d]/g, '').replace(/^0+/, '')
  return normalizedLocal ? `${option.dialCode}${normalizedLocal}` : ''
}

export function contactPlaceholder(countryCode: string) {
  const option = dialOptionForCountry(countryCode)
  return `${option.dialCode} ${option.placeholder}`
}
