/** PC Commerce API client (Phase 3 — Cebu / procurement portals). */
export function useCommerce() {
  const { apiFetch } = useApi()
  const prefix = '/commerce'

  return {
    listPublicCategories: () =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/public/category-schemas`),
    listPublicListings: (params: { q?: string; category_schema_id?: string } = {}) => {
      const query = new URLSearchParams()
      if (params.q) query.set('q', params.q)
      if (params.category_schema_id) query.set('category_schema_id', params.category_schema_id)
      return apiFetch<{ items: any[]; total: number }>(
        `${prefix}/public/listings${query.size ? `?${query.toString()}` : ''}`,
      )
    },
    getPublicListing: (id: string) => apiFetch<any>(`${prefix}/public/listings/${id}`),
    getSupplierDashboard: () => apiFetch<any>(`${prefix}/supplier-dashboard`),
    getSupplierAccount: () => apiFetch<any>(`${prefix}/supplier-account`),
    updateSupplierAccount: (body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/supplier-account`, { method: 'PATCH', body }),
    listSupplierTeam: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/supplier-team`),
    inviteSupplierTeamMember: (body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/supplier-team`, { method: 'POST', body }),
    updateSupplierTeamMember: (id: string, body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/supplier-team/${id}`, { method: 'PATCH', body }),
    listSupplierPings: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/supplier-pings`),
    listSupplierOffers: (status?: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/supplier-offers${status ? `?status=${status}` : ''}`),
    withdrawSupplierOffer: (id: string) =>
      apiFetch<any>(`${prefix}/offers/${id}/withdraw`, { method: 'POST' }),
    listSupplierReviews: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/supplier-reviews`),
    listSupplierListings: (status?: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/supplier-listings${status ? `?status=${status}` : ''}`),
    createSupplierListing: (body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/supplier-listings`, { method: 'POST', body }),
    updateSupplierListing: (id: string, body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/supplier-listings/${id}`, { method: 'PATCH', body }),
    archiveSupplierListing: (id: string) =>
      apiFetch(`${prefix}/supplier-listings/${id}`, { method: 'DELETE' }),
    submitSupplierOffer: (requestId: string, body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/procurement-requests/${requestId}/offers`, { method: 'POST', body }),
    getBuyerAccount: () => apiFetch<any>(`${prefix}/buyer-account`),
    updateBuyerAccount: (body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/buyer-account`, { method: 'PATCH', body }),
    listBuyerTeam: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/buyer-team`),
    listWatchlist: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/watchlist`),
    addWatchlist: (body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/watchlist`, { method: 'POST', body }),
    removeWatchlist: (id: string) => apiFetch(`${prefix}/watchlist/${id}`, { method: 'DELETE' }),
    listOrders: (status?: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/orders${status ? `?status=${status}` : ''}`),
    getOrder: (id: string) => apiFetch<any>(`${prefix}/orders/${id}`),
    completeOrder: (id: string) => apiFetch<any>(`${prefix}/orders/${id}/complete`, { method: 'POST' }),
    listDeliveries: (id: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/orders/${id}/deliveries`),
    acceptDelivery: (id: string) =>
      apiFetch<any>(`${prefix}/deliveries/${id}/status`, { method: 'PATCH', body: { status: 'accepted' } }),
    listDisputes: (status?: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/disputes${status ? `?status=${status}` : ''}`),
    listOrderDisputes: (id: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/orders/${id}/disputes`),
    createDispute: (id: string, body: Record<string, unknown>) =>
      apiFetch<any>(`${prefix}/orders/${id}/disputes`, { method: 'POST', body }),
    listPaymentLedger: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/payment-ledger`),
    startCheckout: (id: string) =>
      apiFetch<{ checkout_url?: string; configured: boolean; detail?: string }>(
        `${prefix}/orders/${id}/checkout`,
        { method: 'POST' },
      ),
    listNotifications: (status?: string) =>
      apiFetch<{ items: any[]; total: number }>(
        `${prefix}/notifications${status ? `?status=${status}` : ''}`,
      ),
    listProcurementRequests: () =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/procurement-requests`),
    getProcurementRequest: (id: string) => apiFetch(`${prefix}/procurement-requests/${id}`),
    listOffers: (id: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/procurement-requests/${id}/offers`),
    getOffer: (id: string) => apiFetch<any>(`${prefix}/offers/${id}`),
    awardOffer: (id: string) => apiFetch<any>(`${prefix}/offers/${id}/award`, { method: 'POST' }),
    listCategorySchemas: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/category-schemas`),
    createProcurementRequest: (body: Record<string, unknown>) =>
      apiFetch(`${prefix}/procurement-requests`, { method: 'POST', body: { portal_key: 'cebu', ...body } }),
    publishRequest: (id: string) =>
      apiFetch(`${prefix}/procurement-requests/${id}/publish`, { method: 'POST' }),
    listCandidates: (requestId: string) =>
      apiFetch<{ items: any[]; total: number }>(
        `${prefix}/procurement-requests/${requestId}/supplier-candidates`,
      ),
    bindCandidate: (requestId: string, listingId: string) =>
      apiFetch<any>(`${prefix}/procurement-requests/${requestId}/supplier-candidates/${listingId}/bind`, {
        method: 'POST',
      }),
    listThreads: () => apiFetch<{ items: any[]; total: number }>(`${prefix}/threads`),
    getOrderThread: (id: string) => apiFetch<any>(`${prefix}/orders/${id}/thread`),
    listMessages: (id: string) =>
      apiFetch<{ items: any[]; total: number }>(`${prefix}/threads/${id}/messages`),
    postMessage: (id: string, body: string) =>
      apiFetch<any>(`${prefix}/threads/${id}/messages`, { method: 'POST', body: { body } }),
    // Trust and account context live on the cebu-compat surface, not /commerce.
    // The buyer workspace needs both to render the trust strip and to decide
    // whether the enterprise shortcuts apply.
    getTrustProfile: () => apiFetch<TrustProfile & { user?: TrustProfile }>('/cebu-compat/trust/me'),
    getAccountContext: () => apiFetch<AccountContext>('/auth/me/account-context'),
  }
}

export interface TrustProfile {
  trust_score?: number
  trust_tier?: string
  deal_completion_rate?: number
  profile_completion_rate?: number
  dispute_rate?: number
  deposit_amount_minor?: number
  deposit_currency?: string
}

export interface AccountContext {
  account_type?: string
  features?: Record<string, boolean>
}
