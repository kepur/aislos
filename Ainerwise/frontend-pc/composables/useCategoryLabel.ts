/**
 * Localised label for a product/procurement category.
 *
 * Category names come from the backend as a fixed taxonomy (Access Control,
 * EV Charging, Smart Locks…). They are the same enumerable set everywhere, so
 * the frontend can translate them by slug via the `cat.*` i18n namespace —
 * the display flips with the interface language while the stored value stays.
 * Anything not in the map (a truly custom category) falls back to its name.
 */

// English name (lowercased) -> normalised slug, so categories that arrive with
// only a `name` can still be localised.
const NAME_TO_SLUG: Record<string, string> = {
  '2hands / second-hand': '2hands',
  'access control': 'access-control',
  'audio / video / multiroom': 'av-multiroom',
  'blinds & shading': 'shading-blinds',
  'energy management': 'energy-management',
  'energy storage & batteries': 'energy-storage',
  'ev charging': 'ev-charging',
  'fire & safety': 'fire-safety',
  'hvac & climate': 'hvac-climate',
  'knx & building automation': 'knx',
  'networking & it': 'networking-it',
  'security & cctv': 'security-cctv',
  'sensors & iot': 'sensors-iot',
  'smart home automation': 'smart-home',
  'smart lighting': 'smart-lighting',
  'smart locks': 'smart-locks',
  'solar & pv': 'solar-pv',
  'knx devices': 'knx-devices',
  'gateways': 'gateways',
  'sensors': 'sensors',
  'smart panels': 'smart-panels',
  'cctv': 'cctv',
  'network devices': 'network-devices',
  'hvac controllers': 'hvac-controllers',
  'energy meters': 'energy-meters',
  'solar monitoring': 'solar-monitoring',
  'lighting control': 'lighting-control',
  'home assistant compatible': 'home-assistant-compatible',
  'service packages': 'service-packages-cat',
  'industrial automation': 'industrial-automation',
  'plc / scada gateways': 'plc-scada-gateways',
  'machine energy monitoring': 'machine-energy-monitoring',
  'storageguard monitoring': 'storageguard-monitoring',
}

// Some slugs carry a random hash suffix (smart-lighting-f3f349); strip it so
// the base taxonomy key still matches.
function normaliseSlug(slug?: string | null): string {
  return String(slug || '').replace(/-[0-9a-f]{6,}$/i, '')
}

export function useCategoryLabel() {
  const { t, te } = useI18n({ useScope: 'global' })

  function categoryLabel(input: { slug?: string; name?: string; title?: string } | string | null | undefined): string {
    if (!input) return ''
    const cat = typeof input === 'string' ? { name: input } : input
    const bySlug = normaliseSlug(cat.slug)
    if (bySlug && te(`cat.${bySlug}`)) return t(`cat.${bySlug}`)
    const name = String(cat.name || cat.title || '').trim()
    const key = NAME_TO_SLUG[name.toLowerCase()]
    if (key && te(`cat.${key}`)) return t(`cat.${key}`)
    return name
  }

  return { categoryLabel }
}
