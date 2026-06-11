<template>
  <div class="h-dvh flex flex-col">
    <!-- ===== Setup: claim device (one-time, admin pastes the device token) ===== -->
    <div v-if="state === 'setup'" class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-md space-y-5">
        <div class="text-center space-y-2">
          <div class="text-3xl font-bold tracking-tight">AISLOS<span class="text-sky-400"> Kiosk</span></div>
          <p class="text-sm text-slate-400">Paste the device token issued in Admin → Showroom → Devices.</p>
        </div>
        <input
          v-model="tokenInput"
          type="password"
          placeholder="Device token"
          class="w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-sky-500"
        >
        <button class="kiosk-btn-primary w-full" :disabled="!tokenInput.trim() || loading" @click="claimDevice">
          {{ loading ? 'Connecting…' : 'Claim this device' }}
        </button>
        <p v-if="setupError" class="text-sm text-rose-400 text-center">{{ setupError }}</p>
      </div>
    </div>

    <!-- ===== Attract loop: idle screen ===== -->
    <div v-else-if="state === 'attract'" class="flex-1 flex flex-col items-center justify-center gap-10 p-8 text-center">
      <div class="space-y-3">
        <div class="text-xs uppercase tracking-[0.3em] text-sky-400">{{ boot?.store?.name }}</div>
        <h1 class="text-5xl font-bold tracking-tight">
          {{ boot?.agent?.name || 'AI Consultant' }}
        </h1>
        <p class="text-lg text-slate-400">{{ boot?.agent?.role_title }}</p>
      </div>
      <div class="space-y-4">
        <p class="text-sm text-slate-500">Choose your language / Izaberite jezik / 选择语言</p>
        <div class="flex flex-wrap justify-center gap-3">
          <button
            v-for="lang in boot?.languages || []"
            :key="lang"
            class="px-6 py-4 rounded-2xl bg-slate-800 border border-slate-700 text-lg font-semibold hover:border-sky-500 hover:bg-slate-700 transition"
            @click="startSession(lang)"
          >
            {{ langLabel(lang) }}
          </button>
        </div>
      </div>
      <!-- AI Act Art.50 disclosure — always visible, not configurable -->
      <div class="kiosk-disclosure">{{ boot?.ai_disclosure }}</div>
    </div>

    <!-- ===== Active session: left conversation / right presentation canvas ===== -->
    <div v-else class="flex-1 flex min-h-0">
      <!-- Left: conversation -->
      <section class="w-[42%] flex flex-col border-r border-slate-800 min-h-0">
        <header class="px-5 py-3 border-b border-slate-800 flex items-center justify-between gap-3">
          <div>
            <div class="font-semibold">{{ boot?.agent?.name }}</div>
            <div class="text-[11px] text-sky-400">{{ boot?.ai_disclosure }}</div>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="text-[10px] rounded-full px-2 py-1 border"
              :class="voiceState === 'listening'
                ? 'border-rose-500 text-rose-400'
                : voice?.enabled
                  ? 'border-emerald-500 text-emerald-400'
                  : 'border-slate-700 text-slate-500'"
              :disabled="!voice?.enabled || voiceState === 'connecting'"
              :title="voice?.enabled ? 'Tap to start or stop realtime voice' : (voice?.reason || 'Text mode')"
              @click="toggleVoice"
            >{{ voiceLabel }}</button>
            <button class="kiosk-btn-ghost text-xs" @click="endSession('browse')">End</button>
          </div>
        </header>

        <div ref="chatBox" class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-for="(m, i) in messages" :key="i" :class="m.role === 'user' ? 'flex justify-end' : 'flex justify-start'">
            <div :class="m.role === 'user' ? 'kiosk-bubble-user' : 'kiosk-bubble-ai'">{{ m.content }}</div>
          </div>
          <div v-if="thinking" class="flex justify-start">
            <div class="kiosk-bubble-ai animate-pulse">…</div>
          </div>
        </div>

        <footer class="p-4 border-t border-slate-800 space-y-3">
          <div class="flex gap-2">
            <input
              v-model="draft"
              class="flex-1 rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-sky-500"
              :placeholder="'Ask about products, prices, stock…'"
              @keydown.enter="send"
            >
            <button class="kiosk-btn-primary px-5" :disabled="!draft.trim() || thinking" @click="send">Send</button>
          </div>
          <div class="flex gap-2 text-xs">
            <button class="kiosk-btn-ghost" @click="canvas = 'lead'">Leave my contact</button>
            <button v-if="cart.length" class="kiosk-btn-ghost" @click="canvas = 'order-preview'">
              Cart ({{ cart.length }})
            </button>
          </div>
        </footer>
      </section>

      <!-- Right: deterministic presentation canvas (D1) -->
      <section class="flex-1 overflow-y-auto p-6 min-h-0">
        <!-- Welcome -->
        <div v-if="canvas === 'welcome'" class="h-full flex flex-col items-center justify-center text-center gap-4">
          <div class="text-2xl font-semibold text-slate-300">How can I help today?</div>
          <p class="text-sm text-slate-500 max-w-sm">
            Ask me anything — I can compare products, check what's in stock here in the store, and prepare your order for the counter.
          </p>
        </div>

        <!-- Product cards -->
        <div v-else-if="canvas === 'products'" class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="kiosk-canvas-title">Products</h2>
            <button v-if="selected.length >= 2" class="kiosk-btn-primary text-sm" @click="compare">
              Compare ({{ selected.length }})
            </button>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div
              v-for="p in products"
              :key="p.id"
              class="kiosk-card"
              :class="selected.includes(p.id) ? 'ring-2 ring-sky-500' : ''"
            >
              <div class="font-semibold">{{ p.name }}</div>
              <div v-if="p.brand" class="text-xs text-slate-500">{{ p.brand }}</div>
              <div class="text-lg font-bold text-sky-400 mt-1">
                {{ p.list_price != null ? `€${p.list_price}` : 'Ask for price' }}
              </div>
              <p v-if="p.description" class="text-xs text-slate-400 mt-1 line-clamp-2">{{ p.description }}</p>
              <div class="flex gap-2 mt-3 text-xs">
                <button class="kiosk-btn-ghost" @click="toggleSelect(p.id)">
                  {{ selected.includes(p.id) ? 'Deselect' : 'Select' }}
                </button>
                <button class="kiosk-btn-ghost" @click="showStock(p)">Stock</button>
                <button class="kiosk-btn-ghost" @click="addToCart(p)">Add</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Comparison table -->
        <div v-else-if="canvas === 'compare'" class="space-y-4">
          <h2 class="kiosk-canvas-title">Comparison</h2>
          <table class="w-full text-sm">
            <thead>
              <tr>
                <th class="kiosk-th text-left">Spec</th>
                <th v-for="p in compareData.products" :key="p.id" class="kiosk-th text-left">{{ p.name }}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="kiosk-td text-slate-400">Price</td>
                <td v-for="p in compareData.products" :key="p.id" class="kiosk-td font-semibold text-sky-400">
                  {{ p.list_price != null ? `€${p.list_price}` : '—' }}
                </td>
              </tr>
              <tr v-for="row in compareData.spec_rows" :key="row.key">
                <td class="kiosk-td text-slate-400">{{ row.key }}</td>
                <td v-for="p in compareData.products" :key="p.id" class="kiosk-td">
                  {{ row.values[p.id] ?? '—' }}
                </td>
              </tr>
            </tbody>
          </table>
          <button class="kiosk-btn-ghost text-sm" @click="canvas = 'products'">Back to products</button>
        </div>

        <!-- Stock card -->
        <div v-else-if="canvas === 'stock'" class="space-y-4">
          <h2 class="kiosk-canvas-title">Stock — {{ stockProduct?.name }}</h2>
          <div class="kiosk-card text-center py-8">
            <div class="text-5xl font-bold" :class="stockData.available > 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ stockData.available }}
            </div>
            <div class="text-sm text-slate-400 mt-1">available now</div>
          </div>
          <div v-for="loc in stockData.locations" :key="loc.location" class="flex justify-between text-sm px-2">
            <span class="text-slate-400">{{ loc.location }}</span>
            <span>{{ loc.quantity }} pcs</span>
          </div>
          <div class="flex gap-2">
            <button v-if="stockData.available > 0 && stockProduct" class="kiosk-btn-primary text-sm" @click="addToCart(stockProduct)">
              Add to order
            </button>
            <button class="kiosk-btn-ghost text-sm" @click="canvas = 'products'">Back</button>
          </div>
        </div>

        <!-- Order preview / cart -->
        <div v-else-if="canvas === 'order-preview'" class="space-y-4">
          <h2 class="kiosk-canvas-title">Your order</h2>
          <div v-for="item in cart" :key="item.id" class="kiosk-card flex items-center justify-between">
            <div>
              <div class="font-semibold text-sm">{{ item.name }}</div>
              <div class="text-xs text-slate-500">€{{ item.list_price }} each</div>
            </div>
            <div class="flex items-center gap-3">
              <button class="kiosk-qty" @click="item.qty > 1 ? item.qty-- : removeFromCart(item.id)">−</button>
              <span class="w-6 text-center">{{ item.qty }}</span>
              <button class="kiosk-qty" @click="item.qty++">+</button>
            </div>
          </div>
          <div class="flex justify-between text-lg font-bold px-2">
            <span>Total</span><span class="text-sky-400">€{{ cartTotal.toFixed(2) }}</span>
          </div>
          <button class="kiosk-btn-primary w-full" :disabled="!cart.length || loading" @click="placeOrder">
            Reserve & get pickup code
          </button>
          <p class="text-xs text-slate-500 text-center">Payment by card at the counter.</p>
        </div>

        <!-- Pickup code -->
        <div v-else-if="canvas === 'order-done'" class="h-full flex flex-col items-center justify-center gap-5 text-center">
          <div class="text-sm uppercase tracking-widest text-slate-400">Show this code at the counter</div>
          <div class="text-7xl font-mono font-bold tracking-[0.2em] text-emerald-400">{{ order?.pickup_code }}</div>
          <div class="text-lg">Total <span class="font-bold text-sky-400">€{{ order?.total?.toFixed(2) }}</span></div>
          <p class="text-sm text-slate-500 max-w-xs">The owner will confirm your order and take card payment at the counter. Thank you!</p>
          <button class="kiosk-btn-ghost text-sm" @click="endSession()">Done</button>
        </div>

        <!-- Lead capture -->
        <div v-else-if="canvas === 'lead'" class="max-w-md mx-auto space-y-4">
          <h2 class="kiosk-canvas-title">Leave your contact</h2>
          <p class="text-sm text-slate-500">For bigger projects our team will prepare a tailored proposal.</p>
          <input v-model="lead.contact_name" placeholder="Name *" class="kiosk-input">
          <input v-model="lead.contact_phone" placeholder="Phone" class="kiosk-input">
          <input v-model="lead.contact_email" placeholder="Email" class="kiosk-input">
          <textarea v-model="lead.description" placeholder="What do you need?" rows="3" class="kiosk-input" />
          <button class="kiosk-btn-primary w-full" :disabled="!lead.contact_name.trim() || loading" @click="submitLead">
            Send
          </button>
          <button class="kiosk-btn-ghost w-full text-sm" @click="canvas = products.length ? 'products' : 'welcome'">Cancel</button>
        </div>

        <div v-else-if="canvas === 'lead-done'" class="h-full flex flex-col items-center justify-center gap-4 text-center">
          <div class="text-4xl">✓</div>
          <div class="text-xl font-semibold">Thank you!</div>
          <p class="text-sm text-slate-500">Our team will contact you shortly.</p>
          <button class="kiosk-btn-ghost text-sm" @click="endSession('lead')">Done</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'kiosk' })

type ProductCard = {
  id: string; name: string; brand?: string; description?: string;
  list_price?: number | null; specs?: Record<string, any>
}
type CartItem = ProductCard & { qty: number }

const { deviceToken, loadToken, saveToken, clearToken, kioskFetch } = useKiosk()

const state = ref<'setup' | 'attract' | 'session'>('setup')
const canvas = ref<'welcome' | 'products' | 'compare' | 'stock' | 'order-preview' | 'order-done' | 'lead' | 'lead-done'>('welcome')
const boot = ref<any>(null)
const voice = ref<any>(null)
const voiceState = ref<'off' | 'connecting' | 'listening' | 'error'>('off')
const selectedLang = ref('en')
const tokenInput = ref('')
const setupError = ref('')
const loading = ref(false)

const sessionId = ref<string | null>(null)
const messages = ref<Array<{ role: string; content: string }>>([])
const draft = ref('')
const thinking = ref(false)
const chatBox = ref<HTMLElement | null>(null)

const products = ref<ProductCard[]>([])
const selected = ref<string[]>([])
const compareData = ref<any>({ products: [], spec_rows: [] })
const stockProduct = ref<ProductCard | null>(null)
const stockData = ref<any>({ available: 0, locations: [] })
const cart = ref<CartItem[]>([])
const order = ref<any>(null)
const lead = reactive({ contact_name: '', contact_phone: '', contact_email: '', description: '' })

const cartTotal = computed(() => cart.value.reduce((s, i) => s + (i.list_price || 0) * i.qty, 0))
const voiceLabel = computed(() => {
  if (!voice.value?.enabled) return 'Text'
  if (voiceState.value === 'connecting') return 'Connecting'
  if (voiceState.value === 'listening') return 'Stop voice'
  if (voiceState.value === 'error') return 'Voice retry'
  return 'Start voice'
})

let realtimePc: RTCPeerConnection | null = null
let realtimeDc: RTCDataChannel | null = null
let realtimeStream: MediaStream | null = null
let realtimeAudio: HTMLAudioElement | null = null

const LANG_LABELS: Record<string, string> = {
  sr: '🇷🇸 Srpski', en: '🇬🇧 English', zh: '🇨🇳 中文', pl: '🇵🇱 Polski', de: '🇩🇪 Deutsch',
}
function langLabel(code: string) { return LANG_LABELS[code] || code }

// 90s without interaction ends the session back to the attract loop.
let idleTimer: ReturnType<typeof setTimeout> | null = null
function resetIdle() {
  if (idleTimer) clearTimeout(idleTimer)
  if (state.value === 'session') {
    idleTimer = setTimeout(() => endSession('abandoned'), 90_000)
  }
}

onMounted(async () => {
  loadToken()
  if (deviceToken.value) await bootstrap()
  window.addEventListener('pointerdown', resetIdle)
  window.addEventListener('keydown', resetIdle)
})
onBeforeUnmount(() => {
  if (idleTimer) clearTimeout(idleTimer)
  disconnectVoice()
  window.removeEventListener('pointerdown', resetIdle)
  window.removeEventListener('keydown', resetIdle)
})

async function bootstrap() {
  try {
    boot.value = await kioskFetch('/bootstrap')
    state.value = 'attract'
    // voice activation probe — non-fatal; text mode is the safe default
    try {
      voice.value = await kioskFetch('/voice-config?probe=true')
    } catch {
      voice.value = { enabled: false, mode: 'text' }
    }
  } catch {
    clearToken()
    state.value = 'setup'
  }
}

async function claimDevice() {
  loading.value = true
  setupError.value = ''
  saveToken(tokenInput.value.trim())
  try {
    boot.value = await kioskFetch('/bootstrap')
    state.value = 'attract'
    tokenInput.value = ''
  } catch (e: any) {
    clearToken()
    setupError.value = e?.data?.detail || 'Invalid or revoked device token.'
  } finally {
    loading.value = false
  }
}

async function startSession(lang: string) {
  try {
    const r = await kioskFetch<any>('/sessions', { method: 'POST', body: { lang } })
    sessionId.value = r.id
    selectedLang.value = lang
    messages.value = [{
      role: 'assistant',
      // Art.50: the assistant introduces itself as an AI in the opener.
      content: `${boot.value?.ai_disclosure} I'm ${boot.value?.agent?.name}. How can I help you today?`,
    }]
    canvas.value = 'welcome'
    products.value = []
    selected.value = []
    cart.value = []
    order.value = null
    state.value = 'session'
    resetIdle()
  } catch { /* device may have been revoked mid-day */ await bootstrap() }
}

async function toggleVoice() {
  if (voiceState.value === 'listening' || voiceState.value === 'connecting') {
    disconnectVoice()
    return
  }
  await connectVoice()
}

async function connectVoice() {
  if (!sessionId.value || !navigator.mediaDevices?.getUserMedia) return
  voiceState.value = 'connecting'
  try {
    const cfg = await kioskFetch<any>(`/voice-config?lang=${encodeURIComponent(selectedLang.value)}`)
    if (!cfg.enabled || !cfg.client_secret || !cfg.webrtc_url) throw new Error(cfg.reason || 'Voice unavailable')

    const pc = new RTCPeerConnection()
    const audio = new Audio()
    audio.autoplay = true
    pc.ontrack = (event) => {
      audio.srcObject = event.streams[0]
      void audio.play()
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    })
    stream.getTracks().forEach(track => pc.addTrack(track, stream))

    const dc = pc.createDataChannel('oai-events')
    dc.onmessage = event => void handleRealtimeEvent(JSON.parse(event.data))
    dc.onopen = () => { voiceState.value = 'listening' }
    pc.onconnectionstatechange = () => {
      if (['failed', 'disconnected', 'closed'].includes(pc.connectionState)) disconnectVoice(true)
    }

    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    const answer = await fetch(cfg.webrtc_url, {
      method: 'POST',
      body: offer.sdp,
      headers: {
        Authorization: `Bearer ${cfg.client_secret}`,
        'Content-Type': 'application/sdp',
      },
    })
    if (!answer.ok) throw new Error(`Voice SDP failed (${answer.status})`)
    await pc.setRemoteDescription({ type: 'answer', sdp: await answer.text() })

    realtimePc = pc
    realtimeDc = dc
    realtimeStream = stream
    realtimeAudio = audio
  } catch {
    disconnectVoice(true)
  }
}

function disconnectVoice(failed = false) {
  realtimeDc?.close()
  realtimePc?.close()
  realtimeStream?.getTracks().forEach(track => track.stop())
  if (realtimeAudio) realtimeAudio.srcObject = null
  realtimeDc = null
  realtimePc = null
  realtimeStream = null
  realtimeAudio = null
  voiceState.value = failed ? 'error' : 'off'
}

async function handleRealtimeEvent(event: any) {
  if (!sessionId.value) return
  const userTranscript = event.type === 'conversation.item.input_audio_transcription.completed'
    ? event.transcript : null
  const assistantTranscript = ['response.output_audio_transcript.done', 'response.audio_transcript.done'].includes(event.type)
    ? event.transcript : null
  if (userTranscript) {
    messages.value.push({ role: 'user', content: userTranscript })
    void logVoiceTranscript('user', userTranscript)
  }
  if (assistantTranscript) {
    messages.value.push({ role: 'assistant', content: assistantTranscript })
    void logVoiceTranscript('assistant', assistantTranscript)
  }
  if (event.type === 'response.function_call_arguments.done') {
    let args = {}
    try { args = JSON.parse(event.arguments || '{}') } catch {}
    const result = await kioskFetch<any>('/realtime-tool-call', {
      method: 'POST',
      body: { session_id: sessionId.value, name: event.name, arguments: args },
    })
    applyRealtimeToolResult(result)
    realtimeDc?.send(JSON.stringify({
      type: 'conversation.item.create',
      item: { type: 'function_call_output', call_id: event.call_id, output: JSON.stringify(result) },
    }))
    realtimeDc?.send(JSON.stringify({ type: 'response.create' }))
  }
  scrollChat()
  resetIdle()
}

function applyRealtimeToolResult(result: any) {
  if (result.view === 'products') {
    products.value = result.items || []
    canvas.value = 'products'
  } else if (result.view === 'compare') {
    compareData.value = result
    canvas.value = 'compare'
  } else if (result.view === 'stock') {
    stockData.value = result
    stockProduct.value = products.value.find(p => p.id === result.product_id) || null
    canvas.value = 'stock'
  } else if (['welcome', 'lead'].includes(result.view)) {
    canvas.value = result.view
  }
}

async function logVoiceTranscript(role: 'user' | 'assistant', content: string) {
  if (!sessionId.value || !content.trim()) return
  try {
    await kioskFetch(`/sessions/${sessionId.value}/messages`, {
      method: 'POST', body: { role, content },
    })
  } catch { /* transcript logging must never freeze the live conversation */ }
}

async function send() {
  const text = draft.value.trim()
  if (!text || !sessionId.value) return
  draft.value = ''
  messages.value.push({ role: 'user', content: text })
  scrollChat()
  thinking.value = true
  try {
    const r = await kioskFetch<any>('/chat', {
      method: 'POST', body: { session_id: sessionId.value, message: text },
    })
    if (r.answer) {
      messages.value.push({ role: 'assistant', content: r.answer })
    } else if (r.fallback_products?.length) {
      products.value = r.fallback_products
      canvas.value = 'products'
      messages.value.push({ role: 'assistant', content: 'Here is what I found in our catalog — see the screen on the right.' })
    } else {
      messages.value.push({ role: 'assistant', content: 'I could not find that. Try other keywords, or call the store owner — happy to help!' })
    }
  } catch {
    messages.value.push({ role: 'assistant', content: 'Connection problem — please call the store owner.' })
  } finally {
    thinking.value = false
    scrollChat()
    resetIdle()
  }
}

function scrollChat() {
  nextTick(() => { chatBox.value?.scrollTo({ top: chatBox.value.scrollHeight, behavior: 'smooth' }) })
}

function toggleSelect(id: string) {
  selected.value = selected.value.includes(id)
    ? selected.value.filter(x => x !== id)
    : [...selected.value, id].slice(-4)
}

async function compare() {
  try {
    compareData.value = await kioskFetch<any>('/products/compare', {
      method: 'POST', body: { session_id: sessionId.value, product_ids: selected.value },
    })
    canvas.value = 'compare'
  } catch { /* keep current canvas */ }
}

async function showStock(p: ProductCard) {
  stockProduct.value = p
  try {
    stockData.value = await kioskFetch<any>(`/products/${p.id}/stock`)
    canvas.value = 'stock'
  } catch { /* keep current canvas */ }
}

function addToCart(p: ProductCard) {
  const existing = cart.value.find(i => i.id === p.id)
  if (existing) existing.qty++
  else cart.value.push({ ...p, qty: 1 })
  canvas.value = 'order-preview'
}

function removeFromCart(id: string) {
  cart.value = cart.value.filter(i => i.id !== id)
}

async function placeOrder() {
  if (!sessionId.value || !cart.value.length) return
  loading.value = true
  try {
    order.value = await kioskFetch<any>('/orders', {
      method: 'POST',
      body: {
        session_id: sessionId.value,
        items: cart.value.map(i => ({ product_id: i.id, qty: i.qty })),
      },
    })
    canvas.value = 'order-done'
  } finally {
    loading.value = false
  }
}

async function submitLead() {
  if (!sessionId.value) return
  loading.value = true
  try {
    await kioskFetch('/leads', {
      method: 'POST',
      body: { session_id: sessionId.value, ...lead },
    })
    canvas.value = 'lead-done'
    Object.assign(lead, { contact_name: '', contact_phone: '', contact_email: '', description: '' })
  } finally {
    loading.value = false
  }
}

async function endSession(outcome?: string) {
  if (idleTimer) clearTimeout(idleTimer)
  disconnectVoice()
  if (sessionId.value) {
    try {
      await kioskFetch(`/sessions/${sessionId.value}`, {
        method: 'PATCH',
        body: outcome ? { outcome } : {},
      })
    } catch { /* attract anyway */ }
  }
  sessionId.value = null
  state.value = 'attract'
}
</script>

<style>
.kiosk-btn-primary {
  @apply rounded-xl bg-sky-500 text-white font-semibold py-3 px-4 transition
         hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed;
}
.kiosk-btn-ghost {
  @apply rounded-lg border border-slate-700 text-slate-300 px-3 py-2 transition hover:border-sky-500 hover:text-white;
}
.kiosk-card {
  @apply rounded-2xl bg-slate-800/60 border border-slate-700/60 p-4;
}
.kiosk-canvas-title {
  @apply text-xl font-bold tracking-tight;
}
.kiosk-bubble-user {
  @apply max-w-[80%] rounded-2xl rounded-br-sm bg-sky-600 text-white text-sm px-4 py-2.5;
}
.kiosk-bubble-ai {
  @apply max-w-[80%] rounded-2xl rounded-bl-sm bg-slate-800 text-slate-100 text-sm px-4 py-2.5;
}
.kiosk-th {
  @apply border-b border-slate-700 px-3 py-2 text-slate-400 font-medium;
}
.kiosk-td {
  @apply border-b border-slate-800 px-3 py-2;
}
.kiosk-qty {
  @apply w-8 h-8 rounded-lg bg-slate-700 text-white font-bold;
}
.kiosk-input {
  @apply w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 text-sm text-slate-100
         placeholder-slate-500 outline-none focus:border-sky-500;
}
.kiosk-disclosure {
  @apply fixed bottom-4 left-1/2 -translate-x-1/2 text-[11px] text-slate-500 bg-slate-800/80
         border border-slate-700 rounded-full px-4 py-1.5;
}
</style>
