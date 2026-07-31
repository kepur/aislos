/** P3-05: Cebu portal shell — manifest + procurement policy for shared layout tokens. */
export function useCebuPortalShell() {
  const policy = useState<import('~/composables/useProcurement').PortalPolicy | null>(
    'procurement-portal-policy',
    () => null,
  )
  const { manifest, load: loadManifest } = usePortalManifest()
  const procurement = useProcurement()

  async function bootstrap() {
    await loadManifest('cebu')
    try {
      policy.value = await procurement.fetchPortalPolicy()
    } catch {
      policy.value = {
        portal_key: 'cebu',
        version: manifest.value?.version ?? 2,
        default_procurement_mode: 'self_service',
        allowed_project_types: ['villa_smart_home', 'hotel_retrofit'],
        price_visibility_rule: 'line_estimates',
        supplier_visibility_rule: 'visible_when_self_service',
        visible_categories: null,
        confidence_gate: { ask_below: 0.6, review_above: 0.8 },
      }
    }
  }

  return { manifest, policy, bootstrap }
}
