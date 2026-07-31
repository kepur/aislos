export function useApiBase() {
  const config = useRuntimeConfig()
  const configuredBase = String(config.public.apiBase || '').replace(/\/$/, '')

  if (!configuredBase) {
    return configuredBase
  }

  try {
    const url = new URL(configuredBase)
    if (import.meta.server) {
      if (url.hostname === 'localhost' || url.hostname === '127.0.0.1') {
        url.hostname = 'backend'
      }
      return url.toString().replace(/\/$/, '')
    }

    const pageHost = window.location.hostname
    const isLocalApiHost = url.hostname === 'localhost' || url.hostname === '127.0.0.1'
    const isLocalPageHost = pageHost === 'localhost' || pageHost === '127.0.0.1'

    if (isLocalApiHost && pageHost && !isLocalPageHost) {
      url.hostname = pageHost
      return url.toString().replace(/\/$/, '')
    }
  } catch {}

  return configuredBase
}
