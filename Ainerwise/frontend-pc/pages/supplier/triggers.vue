<template>
  <section class="mx-auto max-w-2xl space-y-5">
    <div>
      <h1 class="text-2xl font-bold text-white">{{ $t('supTrig.title') }}</h1>
      <p class="mt-2 text-sm text-slate-400">{{ $t('supTrig.subtitle') }}</p>
    </div>
    <form v-if="loaded" class="pc-card space-y-5" @submit.prevent="save">
      <label v-for="item in fields" :key="item.key" class="flex justify-between gap-4 border-b border-white/10 pb-3">
        <span><strong class="block text-white">{{ $t(item.label) }}</strong><span class="text-xs text-slate-400">{{ $t(item.desc) }}</span></span>
        <input v-model="form[item.key]" type="checkbox" />
      </label>
      <div>
        <label class="mb-2 block text-sm font-semibold text-white">{{ $t('supTrig.categories') }}</label>
        <select v-model="form.supplier_category_ids_json" class="input-field min-h-32" multiple>
          <option v-for="item in categories" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <p class="mt-1 text-xs text-slate-400">{{ $t('supTrig.catHint') }}</p>
      </div>
      <div>
        <label class="mb-2 block text-sm font-semibold text-white">{{ $t('supTrig.deliveryRegions') }}</label>
        <select v-model="form.supplier_region_ids_json" class="input-field min-h-32" multiple>
          <option v-for="item in regions" :key="item.id" :value="item.id">{{ item.name }} ({{ item.code }})</option>
        </select>
        <p class="mt-1 text-xs text-slate-400">{{ $t('supTrig.regionHint') }}</p>
      </div>
      <button class="btn-primary" :disabled="saving">{{ saving ? $t('supTrig.saving') : $t('supTrig.saveRules') }}</button>
      <p v-if="message" class="text-emerald-300">{{ message }}</p>
      <p v-if="error" class="text-red-300">{{ error }}</p>
    </form>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const { t } = useI18n()
const { apiFetch } = useApi()
const { listPublicCategories } = useCommerce()
const loaded = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')
const categories = ref<any[]>([])
const regions = ref<any[]>([])
const form = reactive<Record<string, any>>({
  alerts_enabled: true,
  email_enabled: true,
  telegram_enabled: false,
  whatsapp_enabled: false,
  supplier_category_ids_json: [],
  supplier_region_ids_json: [],
})
const fields = [
  { key: 'alerts_enabled', label: 'supTrig.fAlerts', desc: 'supTrig.fAlertsDesc' },
  { key: 'email_enabled', label: 'supTrig.fEmail', desc: 'supTrig.fEmailDesc' },
  { key: 'telegram_enabled', label: 'supTrig.fTelegram', desc: 'supTrig.fTelegramDesc' },
  { key: 'whatsapp_enabled', label: 'supTrig.fWhatsapp', desc: 'supTrig.fWhatsappDesc' },
]

async function save() {
  saving.value = true
  error.value = ''
  try {
    Object.assign(form, await apiFetch('/portal/notification-preferences', { method: 'PUT', body: form }))
    message.value = t('supTrig.rulesSaved')
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || t('supTrig.saveFailed')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const [preferences, categoryData, regionData] = await Promise.all([
      apiFetch('/portal/notification-preferences'),
      listPublicCategories(),
      apiFetch('/regions'),
    ])
    Object.assign(form, preferences)
    categories.value = categoryData.items
    regions.value = regionData.items
    loaded.value = true
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || t('supTrig.loadFailed')
  }
})
</script>
