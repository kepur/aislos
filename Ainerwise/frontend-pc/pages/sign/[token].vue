<template>
  <div class="max-w-3xl mx-auto px-4 py-12">
    <template v-if="state === 'signed'">
      <div class="text-center py-16">
        <div class="text-5xl mb-4">✅</div>
        <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ $t('sign.done') }}</h1>
        <p class="text-gray-500">{{ $t('sign.doneHint') }}</p>
      </div>
    </template>

    <template v-else-if="state === 'error'">
      <div class="text-center py-16">
        <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ $t('sign.invalid') }}</h1>
        <p class="text-gray-500">{{ errorDetail }}</p>
      </div>
    </template>

    <template v-else-if="doc">
      <h1 class="text-2xl font-bold text-gray-900 mb-1">{{ doc.title }}</h1>
      <p class="text-sm text-gray-500 mb-6">{{ $t('sign.for') }} {{ doc.signer_name }}</p>

      <div class="border border-gray-200 rounded-2xl p-6 bg-gray-50 mb-8 max-h-[28rem] overflow-y-auto">
        <pre class="whitespace-pre-wrap text-sm text-gray-800 font-sans leading-relaxed">{{ doc.body_md }}</pre>
      </div>

      <div class="border border-gray-200 rounded-2xl p-6">
        <h2 class="font-semibold text-gray-900 mb-3">{{ $t('sign.signHere') }}</h2>
        <canvas
          ref="pad"
          class="border border-dashed border-gray-300 rounded-xl bg-white w-full touch-none"
          height="160"
          @pointerdown="startDraw"
          @pointermove="draw"
          @pointerup="stopDraw"
          @pointerleave="stopDraw"
        ></canvas>
        <div class="flex items-center justify-between mt-2">
          <button class="text-xs text-gray-500 hover:underline" @click="clearPad">{{ $t('sign.clear') }}</button>
        </div>
        <input v-model="signerName" :placeholder="$t('sign.namePlaceholder')" class="mt-3 w-full text-sm border border-gray-300 rounded-xl px-3 py-2" />
        <label class="flex items-start gap-2 mt-3 text-sm text-gray-600">
          <input v-model="agreed" type="checkbox" class="mt-1" />
          <span>{{ $t('sign.consent') }}</span>
        </label>
        <button
          class="mt-4 w-full bg-gray-900 text-white rounded-xl px-5 py-3 text-sm font-medium disabled:opacity-40"
          :disabled="busy || !agreed || !hasInk"
          @click="submit"
        >{{ busy ? $t('sign.signing') : $t('sign.submit') }}</button>
        <p class="text-[11px] text-gray-400 mt-3">{{ $t('sign.legal') }}</p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { apiFetch } = useApi()

const doc = ref<any>(null)
const state = ref<'loading' | 'ready' | 'signed' | 'error'>('loading')
const errorDetail = ref('')
const signerName = ref('')
const agreed = ref(false)
const busy = ref(false)
const hasInk = ref(false)
const pad = ref<HTMLCanvasElement | null>(null)
let drawing = false
let ctx: CanvasRenderingContext2D | null = null

onMounted(async () => {
  try {
    doc.value = await apiFetch<any>(`/sign/${route.params.token}`)
    signerName.value = doc.value.signer_name || ''
    state.value = 'ready'
    await nextTick()
    if (pad.value) {
      pad.value.width = pad.value.offsetWidth
      ctx = pad.value.getContext('2d')
      if (ctx) { ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.strokeStyle = '#111' }
    }
  } catch (e: any) {
    state.value = 'error'
    errorDetail.value = e?.data?.detail || ''
  }
})

function pos(e: PointerEvent) {
  const rect = pad.value!.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}
function startDraw(e: PointerEvent) {
  if (!ctx) return
  drawing = true
  const p = pos(e)
  ctx.beginPath()
  ctx.moveTo(p.x, p.y)
}
function draw(e: PointerEvent) {
  if (!drawing || !ctx) return
  const p = pos(e)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  hasInk.value = true
}
function stopDraw() { drawing = false }
function clearPad() {
  if (ctx && pad.value) ctx.clearRect(0, 0, pad.value.width, pad.value.height)
  hasInk.value = false
}

async function submit() {
  if (!pad.value) return
  busy.value = true
  try {
    await apiFetch(`/sign/${route.params.token}`, {
      method: 'POST',
      body: {
        signature_data_url: pad.value.toDataURL('image/png'),
        signer_name: signerName.value || null,
        agreed: agreed.value,
      },
    })
    state.value = 'signed'
  } catch (e: any) {
    state.value = 'error'
    errorDetail.value = e?.data?.detail || ''
  } finally {
    busy.value = false
  }
}

useHead({ title: 'Sign document — AinerWise' })
</script>
