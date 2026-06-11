<template>
  <select
    :value="currentLocale"
    @change="switchLang(($event.target as HTMLSelectElement).value)"
    class="text-xs border border-white/20 rounded px-2 py-1 bg-white/5 text-white cursor-pointer hover:bg-white/10 transition outline-none focus:ring-1 focus:ring-primary-500"
  >
    <option v-for="loc in locales" :key="loc.code" :value="loc.code" class="bg-slate-900 text-white">
      {{ localeNames[loc.code] || loc.code }}
    </option>
  </select>
</template>

<script setup lang="ts">
const { locale, locales, setLocale } = useI18n({ useScope: 'global' })

const currentLocale = computed(() => locale.value)

const localeNames: Record<string, string> = {
  en: 'EN',
  zh: '中文',
  sr: 'SR',
}

async function switchLang(code: string) {
  await setLocale(code)
}
</script>
