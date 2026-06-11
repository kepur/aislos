interface MarketingAttribution {
  source_channel?: string
  source_detail?: string
  utm_source?: string
  utm_medium?: string
  utm_campaign?: string
  utm_content?: string
  landing_page?: string
  referrer?: string
}

const STORAGE_KEY = 'ainerwise_first_touch'

export function useMarketingAttribution() {
  function captureAttribution(): MarketingAttribution {
    if (!import.meta.client) return {}

    let existing: MarketingAttribution = {}
    try {
      existing = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}')
    } catch {
      existing = {}
    }

    const params = new URLSearchParams(window.location.search)
    const incoming: MarketingAttribution = {
      utm_source: params.get('utm_source') || undefined,
      utm_medium: params.get('utm_medium') || undefined,
      utm_campaign: params.get('utm_campaign') || undefined,
      utm_content: params.get('utm_content') || undefined,
      landing_page: `${window.location.pathname}${window.location.search}`,
      referrer: document.referrer || undefined,
    }
    incoming.source_channel = incoming.utm_source
      ? 'campaign'
      : existing.source_channel || 'website'
    incoming.source_detail = incoming.utm_source || existing.source_detail

    // Preserve first-touch attribution across the visitor's session. A new
    // explicit UTM campaign starts a new first-touch record.
    const value = incoming.utm_campaign
      ? incoming
      : { ...incoming, ...existing, landing_page: existing.landing_page || incoming.landing_page }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(value))
    return value
  }

  function getAttribution(): MarketingAttribution {
    if (!import.meta.client) return {}
    try {
      const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}')
      return Object.fromEntries(
        Object.entries(stored).filter(([, value]) => value !== undefined && value !== '')
      )
    } catch {
      return captureAttribution()
    }
  }

  return { captureAttribution, getAttribution }
}
