export const CONDITION_GRADES = [
  { code: 'A', label: 'A — like new', hint: 'No visible wear' },
  { code: 'B', label: 'B — good', hint: 'Light cosmetic wear' },
  { code: 'C', label: 'C — fair', hint: 'Clearly used, fully working' },
  { code: 'D', label: 'D — for parts', hint: 'Faulty or incomplete' },
]

export const FULFILLMENT_MODES = [
  { code: 'SELLER_PICKUP', label: 'Collect from seller' },
  { code: 'PICKUP_POINT', label: 'Pickup point' },
  { code: 'PARTNER_CHANNEL', label: 'Channel partner' },
  { code: 'SHIP', label: 'Shipped' },
]

export function useMoney() {
  const config = useRuntimeConfig()
  return (minor: number | null | undefined, currency?: string) => {
    const value = (minor || 0) / 100
    const code = currency || (config.public.defaultCurrency as string) || 'EUR'
    try {
      return new Intl.NumberFormat('en', { style: 'currency', currency: code }).format(value)
    } catch {
      return `${value.toFixed(2)} ${code}`
    }
  }
}

/** Thin wrapper so every call sends auth headers and surfaces API detail messages. */
export function useApi() {
  const config = useRuntimeConfig()
  const auth = useAuthStore()

  return async <T>(path: string, options: Record<string, any> = {}): Promise<T> => {
    return await $fetch<T>(`${config.public.apiBase}${path}`, {
      ...options,
      headers: { ...(options.headers || {}), ...auth.authHeaders() },
    })
  }
}

export function apiErrorMessage(err: any, fallback = 'Something went wrong') {
  return err?.data?.detail || err?.data?.message || err?.message || fallback
}
