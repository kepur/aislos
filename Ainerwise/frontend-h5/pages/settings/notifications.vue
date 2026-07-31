<template>
  <div class="space-y-4 p-4">
    <h1 class="text-xl font-bold text-slate-800">Notification settings</h1>
    <form v-if="loaded" class="m-card space-y-4" @submit.prevent="save">
      <label v-for="item in toggles" :key="item.key" class="flex items-center justify-between gap-4 border-b border-slate-100 pb-3 last:border-0">
        <span><strong class="block text-sm text-slate-800">{{ item.label }}</strong><span class="text-xs text-slate-400">{{ item.description }}</span></span>
        <input v-model="form[item.key]" type="checkbox" class="h-5 w-5" />
      </label>
      <input v-if="form.telegram_enabled" v-model="form.telegram_chat_id" class="m-input" placeholder="Telegram chat ID" />
      <input v-if="form.whatsapp_enabled" v-model="form.whatsapp_number" class="m-input" placeholder="WhatsApp number" />
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
      <p v-if="error" class="text-xs text-red-600">{{ error }}</p>
      <button class="m-btn-primary" :disabled="saving">{{ saving ? 'Saving...' : 'Save preferences' }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })
const { apiFetch } = useApi()
const loaded = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')
const form = reactive<Record<string, any>>({
  email_enabled: true,
  telegram_enabled: false,
  whatsapp_enabled: false,
  alerts_enabled: true,
  reports_enabled: true,
  maintenance_enabled: true,
  renewal_enabled: true,
  telegram_chat_id: '',
  whatsapp_number: '',
})
const toggles = [
  { key: 'email_enabled', label: 'Email', description: 'Receive important updates by email.' },
  { key: 'telegram_enabled', label: 'Telegram', description: 'Receive enabled alerts in Telegram.' },
  { key: 'whatsapp_enabled', label: 'WhatsApp', description: 'Receive enabled alerts in WhatsApp.' },
  { key: 'alerts_enabled', label: 'Operational alerts', description: 'Project and order exceptions.' },
  { key: 'reports_enabled', label: 'Reports', description: 'New report and certificate notices.' },
  { key: 'maintenance_enabled', label: 'Maintenance', description: 'Maintenance reminders and changes.' },
  { key: 'renewal_enabled', label: 'Renewals', description: 'Warranty and AMC renewal reminders.' },
]
async function save() {
  saving.value = true
  error.value = ''
  try {
    Object.assign(form, await apiFetch('/portal/notification-preferences', { method: 'PUT', body: form }))
    message.value = 'Notification preferences saved.'
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to save notification preferences.'
  } finally {
    saving.value = false
  }
}
onMounted(async () => {
  try {
    Object.assign(form, await apiFetch('/portal/notification-preferences'))
    loaded.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || 'Unable to load notification preferences.'
  }
})
</script>
