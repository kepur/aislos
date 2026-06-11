export function useApiBase() {
  const config = useRuntimeConfig()
  const configuredBase = String(config.public.apiBase || '').replace(/\/$/, '')

  if (!import.meta.client || !configuredBase) {
    return configuredBase
  }

  try {
    const url = new URL(configuredBase)
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
