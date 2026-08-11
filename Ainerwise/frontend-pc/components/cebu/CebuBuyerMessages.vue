<template>
  <section class="space-y-4">
    <h1 class="text-2xl font-bold text-white">{{ $t('msg.title') }}</h1>

    <div class="pc-card flex items-start gap-3 border-amber-500/30 bg-amber-500/[0.06]">
      <span class="text-lg">🛡️</span>
      <div>
        <p class="text-sm font-semibold text-white">{{ $t('msg.keepOnPlatform') }}</p>
        <p class="mt-1 text-sm text-slate-400">{{ $t('msg.keepDesc') }}</p>
      </div>
    </div>

    <div class="grid min-h-[620px] gap-4 lg:grid-cols-[320px_1fr]">
      <!-- Thread list -->
      <aside class="pc-card flex flex-col !p-0">
        <div class="border-b border-white/10 p-3">
          <input v-model.trim="keyword" class="input-field" :placeholder="$t('msg.searchPh')" />
        </div>
        <div class="flex-1 overflow-y-auto">
          <button
            v-for="thread in filteredThreads"
            :key="thread.id"
            class="block w-full border-b border-white/5 border-l-4 p-4 text-left transition"
            :class="active?.id === thread.id ? 'border-l-indigo-500 bg-indigo-500/10' : 'border-l-transparent hover:bg-white/5'"
            @click="select(thread)"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-sm font-medium text-white">{{ thread.subject || $t('msg.threadDefault') }}</span>
              <span class="shrink-0 text-[10px] text-slate-500">{{ shortId(orderOf(thread)) }}</span>
            </div>
            <p class="mt-1 truncate text-xs text-slate-500">{{ thread.last_message_preview || thread.status || $t('msg.lastClick') }}</p>
          </button>
          <p v-if="!filteredThreads.length" class="p-4 text-sm text-slate-500">{{ $t('msg.emptyThreads') }}</p>
        </div>
      </aside>

      <!-- Chat area -->
      <div class="pc-card flex flex-col !p-0">
        <template v-if="active">
          <div class="flex items-center justify-between border-b border-white/10 p-4">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500/15 text-sm text-indigo-200">{{ (active.subject || 'O').slice(0, 1) }}</div>
              <h3 class="font-medium text-white">{{ active.subject || $t('msg.threadDefault') }}</h3>
            </div>
            <NuxtLink v-if="orderOf(active)" :to="localized(`/market/buyer/orders/${orderOf(active)}`)" class="text-xs text-indigo-300 hover:text-indigo-200">{{ $t('msg.viewOrder') }} #{{ shortId(orderOf(active)) }}</NuxtLink>
          </div>

          <div ref="chatBox" class="flex-1 space-y-3 overflow-y-auto p-4">
            <div v-for="(m, i) in messages" :key="m.id || i" class="flex flex-col" :class="isSelf(m) ? 'items-end' : 'items-start'">
              <div :class="['max-w-[78%] rounded-2xl px-4 py-2 text-sm', isSelf(m) ? 'rounded-tr-sm bg-indigo-600 text-white' : 'rounded-tl-sm border border-white/10 bg-white/5 text-slate-100']">
                <p class="whitespace-pre-wrap">{{ m.body }}</p>
              </div>
              <span class="mt-1 text-[10px] text-slate-500">{{ m.sender_role || (isSelf(m) ? $t('msg.me') : $t('msg.other')) }} · {{ timeOf(m) }}</span>
            </div>
            <p v-if="!messages.length" class="py-8 text-center text-sm text-slate-500">{{ $t('msg.noMessages') }}</p>
          </div>

          <form class="flex gap-2 border-t border-white/10 p-4" @submit.prevent="send">
            <input v-model.trim="body" required class="input-field flex-1" :placeholder="$t('msg.inputPh')" autocomplete="off" />
            <button class="btn-primary" :disabled="sending || !body">{{ sending ? $t('msg.sending') : $t('msg.send') }}</button>
          </form>
        </template>
        <p v-else class="m-auto p-8 text-sm text-slate-500">{{ $t('msg.selectThread') }}</p>
      </div>
    </div>

    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
const { formatTime } = useLocaleFormat()
const route = useRoute()
const api = useCommerce()
const auth = useAuth() as any
const threads = ref<any[]>([])
const active = ref<any>()
const messages = ref<any[]>([])
const body = ref('')
const error = ref('')
const sending = ref(false)
const keyword = ref('')
const chatBox = ref<HTMLElement | null>(null)

const myId = computed(() => auth?.user?.value?.id || auth?.user?.id || '')
const filteredThreads = computed(() => {
  const kw = keyword.value.toLowerCase()
  if (!kw) return threads.value
  return threads.value.filter(t => `${t.subject || ''} ${orderOf(t)}`.toLowerCase().includes(kw))
})

function orderOf(t: any) {
  return t?.commerce_order_id || t?.order_id || ''
}
function shortId(v?: string) {
  return v ? String(v).slice(0, 8) : ''
}
function isSelf(m: any) {
  if (typeof m?.is_self === 'boolean') return m.is_self
  if (myId.value && m?.sender_id) return m.sender_id === myId.value
  return /buyer|customer|me/i.test(String(m?.sender_role || ''))
}
function timeOf(m: any) {
  return m?.created_at ? formatTime(m.created_at) : ''
}

async function scrollDown() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function select(t: any) {
  active.value = t
  try {
    messages.value = (await api.listMessages(t.id)).items || []
    await scrollDown()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('msg.loadMsgFailed')
  }
}

async function send() {
  if (!active.value || !body.value) return
  sending.value = true
  error.value = ''
  try {
    await api.postMessage(active.value.id, body.value)
    body.value = ''
    messages.value = (await api.listMessages(active.value.id)).items || []
    await scrollDown()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('msg.sendFailed')
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  try {
    threads.value = (await api.listThreads()).items || []
    const orderId = String(route.query.order_id || '')
    const target = (orderId && threads.value.find(t => orderOf(t) === orderId)) || threads.value[0]
    if (target) await select(target)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('msg.loadThreadsFailed')
  }
})
</script>
