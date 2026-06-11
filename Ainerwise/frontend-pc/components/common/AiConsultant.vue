<template>
  <div class="fixed bottom-6 right-6 z-50">
    <!-- Panel -->
    <transition name="fade">
      <div
        v-if="open"
        class="mb-3 w-[360px] max-w-[calc(100vw-3rem)] rounded-2xl border border-gray-200 bg-white shadow-2xl flex flex-col overflow-hidden"
        style="height: 520px"
      >
        <div class="bg-gray-900 text-white px-4 py-3 flex items-center justify-between">
          <div>
            <div class="font-semibold text-sm">{{ $t('aiChat.title') }}</div>
            <div class="text-xs text-gray-300">{{ $t('aiChat.subtitle') }}</div>
          </div>
          <button class="text-gray-300 hover:text-white text-xl leading-none" aria-label="Close" @click="open = false">×</button>
        </div>

        <div ref="scrollArea" class="flex-1 overflow-y-auto px-3 py-3 space-y-3 bg-gray-50">
          <div v-if="messages.length === 0" class="text-sm text-gray-500 px-2 py-4">
            {{ $t('aiChat.welcome') }}
          </div>
          <div v-for="(m, i) in messages" :key="i" class="flex" :class="m.role === 'user' ? 'justify-end' : 'justify-start'">
            <div
              class="rounded-2xl px-3 py-2 text-sm max-w-[85%] whitespace-pre-wrap"
              :class="m.role === 'user' ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-800'"
            >
              <p>{{ m.content }}</p>
              <div v-if="m.sources && m.sources.length" class="mt-2 flex flex-wrap gap-1">
                <span
                  v-for="(s, j) in m.sources"
                  :key="j"
                  class="inline-block text-[11px] bg-gray-100 text-gray-600 rounded-full px-2 py-0.5"
                >📄 {{ s.title }}</span>
              </div>
              <div v-if="m.similarCases && m.similarCases.length" class="mt-2 space-y-1">
                <div
                  v-for="(c, k) in m.similarCases"
                  :key="'c' + k"
                  class="text-xs border border-emerald-200 bg-emerald-50 rounded-lg px-2 py-1.5"
                >
                  <span class="font-medium text-emerald-900">{{ c.title }}</span>
                  <span class="text-emerald-700">
                    · {{ c.area_sqm }}m² · {{ c.duration_days }}d
                    <template v-if="c.similarity"> · {{ Math.round(c.similarity * 100) }}%</template>
                  </span>
                </div>
              </div>
              <div v-if="m.products && m.products.length" class="mt-2 space-y-1">
                <NuxtLink
                  v-for="p in m.products"
                  :key="p.id"
                  :to="`/products/${p.slug}`"
                  class="block text-xs border border-gray-200 rounded-lg px-2 py-1.5 hover:border-gray-400 bg-gray-50"
                >
                  <span class="font-medium text-gray-800">{{ p.name }}</span>
                  <span v-if="p.brand" class="text-gray-500"> · {{ p.brand }}</span>
                </NuxtLink>
              </div>
              <div v-if="m.leadCreated" class="mt-2 text-[11px] text-emerald-700 bg-emerald-50 rounded px-2 py-1">
                ✓ {{ $t('aiChat.leadCreated') }}
              </div>
            </div>
          </div>
          <div v-if="loading" class="flex justify-start">
            <div class="bg-white border border-gray-200 rounded-2xl px-3 py-2 text-sm text-gray-400">
              {{ $t('aiChat.thinking') }}
            </div>
          </div>
        </div>

        <div class="px-3 pb-1 pt-2 border-t border-gray-100 bg-white">
          <div class="flex gap-2">
            <input
              v-model="draft"
              :placeholder="$t('aiChat.placeholder')"
              class="flex-1 text-sm border border-gray-300 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400"
              :disabled="loading"
              @keydown.enter.prevent="send"
            />
            <button
              class="bg-gray-900 text-white text-sm rounded-xl px-4 py-2 disabled:opacity-40"
              :disabled="loading || !draft.trim()"
              @click="send"
            >{{ $t('aiChat.send') }}</button>
          </div>
          <p class="text-[10px] text-gray-400 mt-1.5 mb-1 leading-snug">{{ $t('aiChat.disclaimer') }}</p>
        </div>
      </div>
    </transition>

    <!-- Floating button -->
    <button
      class="ml-auto flex items-center gap-2 bg-gray-900 hover:bg-gray-700 text-white rounded-full shadow-xl px-5 py-3 text-sm font-medium"
      @click="open = !open"
    >
      <span class="text-lg leading-none">💬</span>
      <span>{{ $t('aiChat.button') }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{ title: string }>
  products?: Array<{ id: string; name: string; brand?: string; slug: string }>
  similarCases?: Array<{ title: string; area_sqm?: number; duration_days?: number; similarity?: number }>
  leadCreated?: boolean
}

const { apiFetch } = useApi()
const { locale, t } = useI18n()

const open = ref(false)
const draft = ref('')
const loading = ref(false)
const messages = ref<ChatMessage[]>([])
const conversationId = ref<string | null>(null)
const scrollArea = ref<HTMLElement | null>(null)

const visitorId = useCookie<string>('aw_visitor_id', {
  default: () => `v-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`,
  maxAge: 60 * 60 * 24 * 365,
})

async function send() {
  const text = draft.value.trim()
  if (!text || loading.value) return
  draft.value = ''
  messages.value.push({ role: 'user', content: text })
  loading.value = true
  await scrollToEnd()
  try {
    const r = await apiFetch<any>('/ai/chat', {
      method: 'POST',
      body: {
        message: text,
        conversation_id: conversationId.value,
        visitor_id: visitorId.value,
        lang: locale.value,
      },
    })
    if (r.conversation_id) conversationId.value = r.conversation_id
    messages.value.push({
      role: 'assistant',
      content: r.answer || t('aiChat.unavailable'),
      sources: r.sources || [],
      products: r.products || [],
      similarCases: r.similar_cases || [],
      leadCreated: !!r.lead_created,
    })
  } catch {
    messages.value.push({ role: 'assistant', content: t('aiChat.unavailable') })
  } finally {
    loading.value = false
    await scrollToEnd()
  }
}

async function scrollToEnd() {
  await nextTick()
  if (scrollArea.value) scrollArea.value.scrollTop = scrollArea.value.scrollHeight
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
