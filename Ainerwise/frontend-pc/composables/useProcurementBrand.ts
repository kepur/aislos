import type { PortalPolicy } from './useProcurement'

const BRAND_STYLES = {
  aislos: {
    key: 'aislos',
    accent: 'from-blue-500 to-indigo-500',
    accentText: 'text-indigo-300',
    badge: 'ws-badge',
    homePath: '/',
  },
  cebu: {
    key: 'cebu',
    accent: 'from-blue-500 to-indigo-500',
    accentText: 'text-indigo-300',
    badge: 'ws-badge',
    homePath: '/market',
  },
} as const

export type ProcurementBrandKey = keyof typeof BRAND_STYLES

export function useProcurementBrand(policy: Ref<PortalPolicy | null>) {
  const hostnameBrand = computed<ProcurementBrandKey>(() => {
    if (import.meta.client && (window.location.hostname.includes('market') || window.location.hostname.includes('cebu'))) return 'cebu'
    return 'aislos'
  })

  const portalKey = computed(() => policy.value?.portal_key || hostnameBrand.value)

  const brand = computed(() => BRAND_STYLES[portalKey.value as ProcurementBrandKey] || BRAND_STYLES.aislos)

  const showLineEstimates = computed(
    () => policy.value?.price_visibility_rule === 'line_estimates',
  )

  const showSuppliers = computed(
    () => policy.value?.supplier_visibility_rule === 'visible_when_self_service',
  )

  return {
    portalKey,
    brand,
    showLineEstimates,
    showSuppliers,
  }
}
