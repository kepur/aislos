/** Admin / Staff Commerce API (settlement + reconciliation). */
export function useCommerce() {
  const { apiFetch } = useApi()
  const prefix = '/commerce'

  return {
    listSettlements: (status?: string) =>
      apiFetch<{ items: any[]; total: number }>(
        `${prefix}/settlements${status ? `?status=${status}` : ''}`,
      ),
    confirmFunding: (orderId: string, externalRef: string) =>
      apiFetch(`${prefix}/orders/${orderId}/confirm-funding`, {
        method: 'POST',
        body: { external_ref: externalRef },
      }),
    settlePayment: (settlementId: string, pspRef: string) =>
      apiFetch(`${prefix}/settlements/${settlementId}/settle`, {
        method: 'POST',
        body: { psp_settlement_ref: pspRef },
      }),
    runReconciliation: (periodStart: string, periodEnd: string) =>
      apiFetch(`${prefix}/reconciliation-runs`, {
        method: 'POST',
        body: { period_start: periodStart, period_end: periodEnd },
      }),
    listRiskFlags: (status = 'open') =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/risk-flags?status=${status}`),
  }
}
