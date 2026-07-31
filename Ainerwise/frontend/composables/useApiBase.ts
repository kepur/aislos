export function useApiBase() {
  const config = useRuntimeConfig()
  return String(config.public.apiBase || '').replace(/\/$/, '')
}
