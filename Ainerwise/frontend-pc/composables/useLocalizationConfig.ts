export type LocalizationConfig = {
  default_locale_prefix: string
  supported_locales: Array<{ code: string; locale: string; uri_prefix: string; label: string }>
  enabled_region_codes: string[]
  supported_regions: Array<{ id: string; code: string; name: string; currency_code: string; language_codes_json?: string[] | null; timezone?: string | null }>
  translation_policy: {
    machine_translation_enabled: boolean
    review_required: boolean
    provider_category: string
    ai_output_policy: string
  }
}

export function useLocalizationConfig() {
  const apiBase = useApiBase()
  const config = useState<LocalizationConfig | null>('localization-config', () => null)
  const loaded = useState('localization-config-loaded', () => false)
  const error = useState('localization-config-error', () => '')

  async function load(force = false) {
    if (loaded.value && config.value && !force) return config.value
    error.value = ''
    try {
      config.value = await $fetch<LocalizationConfig>(`${apiBase}/localization/config`)
      loaded.value = true
    } catch (e: any) {
      error.value = e?.data?.detail || e?.message || 'Unable to load localization config'
    }
    return config.value
  }

  return { config, loaded, error, load }
}
