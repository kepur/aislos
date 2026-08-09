<template>
  <section class="space-y-6">
    <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 class="text-2xl font-bold ws-title">买家设置</h1>
        <p class="mt-1 text-sm ws-muted">维护买家身份、回访联系方式、界面语言与提醒渠道。</p>
      </div>
      <div class="rounded-xl border ws-hairline ws-soft px-4 py-2 text-xs ws-muted">站内会话与交易记录始终是争议与审计的权威来源。</div>
    </div>

    <p v-if="message" class="pc-card text-sm text-emerald-300">{{ message }}</p>
    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>

    <div class="grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-start">
    <!-- Account contact -->
    <form v-if="loaded" class="pc-card space-y-4" @submit.prevent="saveProfile">
      <div>
        <h2 class="text-lg font-medium ws-title">账户联系人</h2>
        <p class="mt-1 text-sm ws-muted">保持买家身份与回访联系方式最新。</p>
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <div><label class="mb-1 block text-sm ws-muted">姓名</label><input v-model.trim="form.full_name" class="input-field" /></div>
        <div><label class="mb-1 block text-sm ws-muted">手机号</label><input v-model.trim="form.phone" class="input-field" /></div>
        <div><label class="mb-1 block text-sm ws-muted">邮箱</label><input :value="form.email" disabled class="input-field opacity-60" /></div>
        <div><label class="mb-1 block text-sm ws-muted">国家 / 地区</label><input v-model.trim="form.country" class="input-field" /></div>
        <div class="sm:col-span-2"><label class="mb-1 block text-sm ws-muted">Telegram Chat ID（可选，仅用于提醒）</label><input v-model.trim="form.telegram_chat_id" class="input-field" placeholder="选填" /></div>
      </div>
      <div class="flex justify-end border-t ws-hairline pt-4">
        <button class="btn-primary" :disabled="savingProfile">{{ savingProfile ? '保存中…' : '保存联系方式' }}</button>
      </div>
    </form>

    <div class="space-y-6">
    <!-- Language & region -->
    <div v-if="loaded" class="pc-card space-y-4">
      <div>
        <h2 class="text-lg font-medium ws-title">界面语言</h2>
        <p class="mt-1 text-sm ws-muted">立即切换整个界面语言（含内页）。</p>
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
        <h2 class="text-lg font-medium ws-title">提醒渠道</h2>
        <p class="mt-1 text-sm ws-muted">提醒渠道可选，订单凭证不可选——核心记录始终留在站内。</p>
      </div>
      <label class="flex items-start gap-3 rounded-xl ws-row !p-4">
        <input v-model="notif.email" type="checkbox" class="mt-1 accent-[color:var(--accent)]" />
        <div><p class="text-sm font-medium ws-title">邮件提醒</p><p class="mt-1 text-sm ws-muted">有新消息、订单变更或供应商响应时发送摘要。</p></div>
      </label>
      <label class="flex items-start gap-3 rounded-xl ws-row !p-4">
        <input v-model="notif.telegram" type="checkbox" class="mt-1 accent-[color:var(--accent)]" />
        <div><p class="text-sm font-medium ws-title">Telegram 提醒</p><p class="mt-1 text-sm ws-muted">需先在上方保存 Telegram Chat ID。</p></div>
      </label>
      <div class="flex justify-end border-t ws-hairline pt-4">
        <button class="btn-secondary" :disabled="savingNotif">{{ savingNotif ? '保存中…' : '保存提醒设置' }}</button>
      </div>
    </form>
    </div>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'], alias: ['/buyer/settings'] })

const api = useCommerce()
const { locale, setLocale } = useI18n({ useScope: 'global' })
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
    message.value = '联系方式已保存。'
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '保存失败'
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
    message.value = '提醒设置已保存。'
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || '保存失败'
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
    error.value = e?.data?.detail || e?.message || '加载设置失败'
  }
})
</script>
