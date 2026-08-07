<template>
  <select
    :value="currentLocale"
    @change="switchLang(($event.target as HTMLSelectElement).value)"
    class="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-700 shadow-sm outline-none transition hover:bg-slate-50 focus:ring-1 focus:ring-primary-500"
  >
    <option v-for="loc in localeOptions" :key="codeOfLocale(loc)" :value="codeOfLocale(loc)" class="bg-white text-slate-900">
      {{ labelForLocale(codeOfLocale(loc)) }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { prefixForLocale, withLocalePrefix } from '~/utils/localeRoutes'

const { locale, locales, setLocale } = useI18n({ useScope: 'global' })
const route = useRoute()
const { config: localizationConfig, load: loadLocalizationConfig } = useLocalizationConfig()

const currentLocale = computed(() => locale.value)

const localeNames: Record<string, string> = {
  en: 'EN',
  zh: '中文',
  sr: 'SR',
  pl: 'PL',
}

onMounted(() => {
  void loadLocalizationConfig()
})

function codeOfLocale(item: unknown) {
  if (typeof item === 'string') return item
  if (item && typeof item === 'object' && 'code' in item) return String((item as { code: string }).code)
  return ''
}

const localeOptions = computed(() => {
  const enabled = new Set((localizationConfig.value?.supported_locales || []).map(item => item.locale))
  const allLocales = locales.value as unknown[]
  return enabled.size ? allLocales.filter(item => enabled.has(codeOfLocale(item))) : allLocales
})

function labelForLocale(code: string) {
  return localizationConfig.value?.supported_locales.find(item => item.locale === code)?.label
    || localeNames[code]
    || code
}

async function switchLang(code: string) {
  await setLocale(code)
  const prefix = prefixForLocale(code)
  if (prefix) await navigateTo(withLocalePrefix(route.fullPath, prefix))
}
</script>
