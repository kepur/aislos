import { useRuntimeConfig } from '#app'
import { useAuthStore } from '~/stores/auth'

export const useApi = () => {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()

  const fetchApi = async <T>(endpoint: string, options: any = {}) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (authStore.accessToken) {
      headers['Authorization'] = `Bearer ${authStore.accessToken}`
    }

    try {
      const response = await $fetch<T>(`${config.public.apiBase}${endpoint}`, {
        ...options,
        headers,
      })
      return { data: response, error: null }
    } catch (err: any) {
      console.error(`API Error on ${endpoint}:`, err)
      return { data: null, error: err.data || err.message }
    }
  }

  return {
    // Auth
    login: (credentials: any) => fetchApi('/auth/login', { method: 'POST', body: credentials }),
    register: (data: any) => fetchApi('/auth/register', { method: 'POST', body: data }),
    getMe: () => fetchApi('/auth/me'),

    // Buyer Intents (Requests)
    getIntents: (params: any = {}) => fetchApi('/intents', { params }),
    getMyIntents: (params: any = {}) => fetchApi('/intents/my', { params }),
    getIntent: (id: string) => fetchApi(`/intents/${id}`),
    createIntent: (data: any) => fetchApi('/intents', { method: 'POST', body: data }),

    // Offers
    getOffersForIntent: (intentId: string) => fetchApi(`/intents/${intentId}/offers`),
    makeOffer: (intentId: string, data: any) => fetchApi(`/intents/${intentId}/offers`, { method: 'POST', body: data }),
    awardOffer: (offerId: string) => fetchApi(`/offers/${offerId}/award`, { method: 'POST' }),

    // Orders & Escrow
    getOrders: () => fetchApi('/orders/my'),
    getOrder: (id: string) => fetchApi(`/orders/${id}`),
    confirmDelivery: (id: string) => fetchApi(`/orders/${id}/accept`, { method: 'POST' }),

    // Catalog & Suppliers
    getCatalog: () => fetchApi('/supplier/catalog/items'),
    updateCatalog: (id: string, data: any) => fetchApi(`/supplier/catalog/items/${id}`, { method: 'PATCH', body: data }),

    // Disputes
    openDispute: (orderId: string, data: any) => fetchApi(`/orders/${orderId}/dispute`, { method: 'POST', body: data }),
    getDisputes: () => fetchApi('/admin/disputes'),
  }
}
