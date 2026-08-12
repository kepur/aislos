<template>
  <section class="space-y-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold ws-title">{{ $t('portal.buyerSet.title') }}</h1>
        <p class="mt-1 text-sm ws-muted">{{ $t('portal.buyerSet.subtitle') }}</p>
      </div>
      <div class="rounded-xl border ws-hairline ws-soft px-4 py-2 text-xs ws-muted">{{ $t('portal.buyerSet.authoritative') }}</div>
    </div>

    <p v-if="message" class="pc-card text-sm text-emerald-300">{{ message }}</p>
    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <div class="grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-start">
    <!-- Account contact -->
    <form v-if="loaded" class="pc-card space-y-4" @submit.prevent="saveProfile">
      <div>
        <h2 class="text-lg font-medium ws-title">{{ $t('portal.buyerSet.contactTitle') }}</h2>
        <p class="mt-1 text-sm ws-muted">{{ $t('portal.buyerSet.contactDesc') }}</p>
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <div><label class="mb-1 block text-sm ws-muted">{{ $t('portal.buyerSet.name') }}</label><input v-model.trim="form.full_name" class="input-field" /></div>
        <div><label class="mb-1 block text-sm ws-muted">{{ $t('supTeam.phonePh') }}</label><input v-model.trim="form.phone" class="input-field" /></div>
        <div><label class="mb-1 block text-sm ws-muted">{{ $t('portal.account.email') }}</label><input :value="form.email" disabled class="input-field opacity-60" /></div>
        <div><label class="mb-1 block text-sm ws-muted">{{ $t('portal.account.country') }}</label><input v-model.trim="form.country" class="input-field" /></div>
        <div class="sm:col-span-2"><label class="mb-1 block text-sm ws-muted">{{ $t('portal.buyerSet.telegramId') }}</label><input v-model.trim="form.telegram_chat_id" class="input-field" :placeholder="$t('portal.buyerSet.optional')" /></div>
      </div>
      <div class="flex justify-end border-t ws-hairline pt-4">
        <button class="btn-primary" :disabled="savingProfile">{{ savingProfile ? $t('portal.account.saving') : $t('portal.buyerSet.saveContact') }}</button>
      </div>
    </form>

    <div class="space-y-6">
    <!-- Language & region -->
    <div v-if="loaded" class="pc-card space-y-4">
      <div>
        <h2 class="text-lg font-medium ws-title">{{ $t('portal.buyerSet.langTitle') }}</h2>
        <p class="mt-1 text-sm ws-muted">{{ $t('portal.buyerSet.langDesc') }}</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="l in localeOptions"
          :key="l.code"
          type="button"
          :class="['rounded-xl border px-4 py-2 text-sm transition', currentLocale === l.code ? 'border-[color:var(--accent)] ws-accent' : 'ws-hairline ws-muted hover:border-[color:var(--accent)]']"
          @click="changeLocale(l.code)"
        >{{ l.label }}</button>
      </div>
    </div>

    <!-- Notification channels -->
    <form v-if="loaded" class="pc-card space-y-4" @submit.prevent="saveNotifications">
      <div>
        <h2 class="text-lg font-medium ws-title">{{ $t('portal.buyerSet.notifTitle') }}</h2>
        <p class="mt-1 text-sm ws-muted">{{ $t('portal.buyerSet.notifDesc') }}</p>
      </div>
      <label class="flex items-start gap-3 rounded-xl ws-row !p-4">
        <input v-model="notif.email" type="checkbox" class="mt-1 accent-[color:var(--accent)]" />
        <div><p class="text-sm font-medium ws-title">{{ $t('portal.buyerSet.emailAlert') }}</p><p class="mt-1 text-sm ws-muted">{{ $t('portal.buyerSet.emailAlertDesc') }}</p></div>
      </label>
      <label class="flex items-start gap-3 rounded-xl ws-row !p-4">
        <input v-model="notif.telegram" type="checkbox" class="mt-1 accent-[color:var(--accent)]" />
        <div><p class="text-sm font-medium ws-title">{{ $t('portal.buyerSet.telegramAlert') }}</p><p class="mt-1 text-sm ws-muted">{{ $t('portal.buyerSet.telegramAlertDesc') }}</p></div>
      </label>
      <div class="flex justify-end border-t ws-hairline pt-4">
        <button class="btn-secondary" :disabled="savingNotif">{{ savingNotif ? $t('portal.account.saving') : $t('portal.buyerSet.saveNotif') }}</button>
      </div>
    </form>
    </div>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/settings'] })

const api = useCommerce()
const { t, locale, setLocale } = useI18n({ useScope: 'global' })
const loaded = ref(false)
const message = ref('')
const error = ref('')
const savingProfile = ref(false)
const savingNotif = ref(false)
const form = reactive({ full_name: '', phone: '', email: '', country: '', telegram_chat_id: '', language: 'en' })
const notif = reactive({ email: true, telegram: false })

const localeOptions = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文' },
  { code: 'sr', label: 'Srpski' },
  { code: 'pl', label: 'Polski' },
]
const currentLocale = computed(() => locale.value)

async function changeLocale(code: string) {
  await setLocale(code as any)
  form.language = code
  try { await api.updateBuyerAccount({ language: code }) } catch { /* locale still switches locally */ }
}

async function saveProfile() {
  savingProfile.value = true
  error.value = ''
  message.value = ''
  try {
    await api.updateBuyerAccount({
      full_name: form.full_name,
      phone: form.phone,
      country: form.country,
      telegram_chat_id: form.telegram_chat_id || undefined,
    })
    message.value = t('portal.buyerSet.contactSaved')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('portal.buyerSet.saveFailed')
  } finally {
    savingProfile.value = false
  }
}

async function saveNotifications() {
  savingNotif.value = true
  error.value = ''
  message.value = ''
  try {
    await api.updateBuyerAccount({ notify_email: notif.email, notify_telegram: notif.telegram })
    message.value = t('portal.buyerSet.notifSaved')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('portal.buyerSet.saveFailed')
  } finally {
    savingNotif.value = false
  }
}

onMounted(async () => {
  try {
    const data = await api.getBuyerAccount()
    Object.assign(form, {
      full_name: data.user?.full_name || '',
      phone: data.user?.phone || '',
      email: data.user?.email || '',
      country: data.user?.country || '',
      telegram_chat_id: data.user?.telegram_chat_id || '',
      language: data.user?.language || locale.value,
    })
    notif.email = data.user?.notify_email ?? true
    notif.telegram = data.user?.notify_telegram ?? false
    loaded.value = true
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('portal.buyerSet.loadFailed')
  }
})
</script>
