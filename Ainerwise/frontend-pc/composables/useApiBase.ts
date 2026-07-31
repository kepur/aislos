export function useApiBase() {
  const config = useRuntimeConfig()
  const configuredBase = String(config.public.apiBase || '').replace(/\/$/, '')

  if (!configuredBase) {
    return configuredBase
  }

  try {
    if (import.meta.server) {
      const url = new URL(configuredBase)
      if (url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
        url.hostname = 'backend'
      }
      return url.toString().replace(/\/$/, '')
    }

    const pageHost = window.location.hostname
    const isLocalHost = pageHost === 'localhost' || pageHost === '127.0.0.1'

    // Market/Cebu hostname → nginx injects X-Portal-Key: cebu on /api/
    if (pageHost.includes('cebu.') || pageHost.includes('market.')) {
      return `${window.location.protocol}//${pageHost}/api/v1`
    }

    // Local dev: frontend on :4099 etc. must hit nginx :80 /api so the gateway
    // injects trusted X-Portal-Key (direct :8000 calls have no portal context).
    if (isLocalHost && configuredBase.includes('localhost:8000')) {
      return `${window.location.protocol}//${pageHost}/api/v1`
    }

    const url = new URL(configuredBase)
    const isLocalApiHost = url.hostname === 'localhost' || url.hostname === '127.0.0.1'

    if (isLocalApiHost && pageHost && !isLocalHost) {
      url.hostname = pageHost
      return url.toString().replace(/\/$/, '')
    }
  } catch {}

  return configuredBase
}
