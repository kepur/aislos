/**
 * Legacy Cebu Intent API on Core (P3-06 compat layer).
 * apiBase already includes /api/v1 — paths start with /cebu-compat.
 */
export function useCebuCompat() {
  const { apiFetch } = useApi()
  const prefix = '/cebu-compat'

  return {
    createIntent: (body: { title: string; description?: string; category_schema_id?: string }) =>
      apiFetch(`${prefix}/intents`, {
        method: 'POST',
        body: { portal_key: 'cebu', ...body },
      }),
    publishIntent: (intentId: string) =>
      apiFetch(`${prefix}/intents/${intentId}/publish`, { method: 'POST' }),
    listCandidates: (intentId: string) =>
      apiFetch<{ items: any[]; total: number; intent_id: string }>(
        `${prefix}/intents/${intentId}/supplier-candidates`,
      ),
    bindCandidate: (intentId: string, catalogItemId: string) =>
      apiFetch(`${prefix}/intents/${intentId}/supplier-candidates/${catalogItemId}/bind`, {
        method: 'POST',
      }),
  }
}
