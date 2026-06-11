import type { PortalPolicy } from './useProcurement'

const BRAND_STYLES = {
  aislos: {
    key: 'aislos',
    accent: 'from-emerald-500 to-cyan-500',
    accentText: 'text-emerald-300',
    badge: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/30',
    homePath: '/',
  },
  cebu: {
    key: 'cebu',
    accent: 'from-orange-500 to-amber-500',
    accentText: 'text-orange-300',
    badge: 'bg-orange-500/20 text-orange-200 border-orange-400/30',
    homePath: '/',
  },
} as const

export type ProcurementBrandKey = keyof typeof BRAND_STYLES

export function useProcurementBrand(policy: Ref<PortalPolicy | null>) {
  const hostnameBrand = computed<ProcurementBrandKey>(() => {
    if (import.meta.client && window.location.hostname.includes('cebu')) return 'cebu'
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
