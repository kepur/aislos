<template>
  <section class="mx-auto max-w-2xl space-y-5">
    <div>
      <h1 class="text-2xl font-bold text-white">匹配与通知规则</h1>
      <p class="mt-2 text-sm text-slate-400">Only matching published requests appear in your supplier ping queue.</p>
    </div>
    <form v-if="loaded" class="pc-card space-y-5" @submit.prevent="save">
      <label v-for="item in fields" :key="item.key" class="flex justify-between gap-4 border-b border-white/10 pb-3">
        <span><strong class="block text-white">{{ item.label }}</strong><span class="text-xs text-slate-400">{{ item.desc }}</span></span>
        <input v-model="form[item.key]" type="checkbox" />
      </label>
      <div>
        <label class="mb-2 block text-sm font-semibold text-white">Categories</label>
        <select v-model="form.supplier_category_ids_json" class="input-field min-h-32" multiple>
          <option v-for="item in categories" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <p class="mt-1 text-xs text-slate-400">Leave empty to derive categories from your active catalog.</p>
      </div>
      <div>
        <label class="mb-2 block text-sm font-semibold text-white">Delivery regions</label>
        <select v-model="form.supplier_region_ids_json" class="input-field min-h-32" multiple>
          <option v-for="item in regions" :key="item.id" :value="item.id">{{ item.name }} ({{ item.code }})</option>
        </select>
        <p class="mt-1 text-xs text-slate-400">Leave empty to receive matching requests from every region.</p>
      </div>
      <button class="btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save rules' }}</button>
      <p v-if="message" class="text-emerald-300">{{ message }}</p>
      <p v-if="error" class="text-red-300">{{ error }}</p>
    </form>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

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
  { key: 'alerts_enabled', label: 'Matching request alerts', desc: 'New procurement demand and order exceptions.' },
  { key: 'email_enabled', label: 'Email', desc: 'Send enabled alerts by email.' },
  { key: 'telegram_enabled', label: 'Telegram', desc: 'Send enabled alerts through Telegram.' },
  { key: 'whatsapp_enabled', label: 'WhatsApp', desc: 'Send enabled alerts through WhatsApp.' },
]

async function save() {
  saving.value = true
  error.value = ''
  try {
    Object.assign(form, await apiFetch('/portal/notification-preferences', { method: 'PUT', body: form }))
    message.value = 'Rules saved.'
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || 'Rules could not be saved.'
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
    error.value = cause?.data?.detail || cause?.message || 'Rules could not be loaded.'
  }
})
</script>
