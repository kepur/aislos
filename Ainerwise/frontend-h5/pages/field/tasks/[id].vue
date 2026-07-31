<template>
  <div class="p-4 space-y-4 pb-24">
    <NuxtLink to="/field/today" class="text-sm text-primary-600">← 今日任务</NuxtLink>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <div v-if="task" class="space-y-4">
      <div>
        <h1 class="text-xl font-semibold">{{ task.title }}</h1>
        <p class="text-sm text-gray-500">{{ task.task_type }} · v{{ task.offline_version }}</p>
        <p v-if="!online" class="text-xs text-amber-600 mt-1">离线模式 — 操作将排队同步</p>
      </div>

      <div v-if="task.site_json?.address" class="rounded-lg border p-3 bg-white text-sm">
        <p class="font-medium">地址</p>
        <p class="text-gray-700">{{ task.site_json.address }}</p>
        <a
          v-if="mapsUrl"
          :href="mapsUrl"
          target="_blank"
          rel="noopener"
          class="inline-block mt-2 text-primary-600 text-xs"
        >导航</a>
      </div>

      <div v-if="task.site_contact_phone" class="rounded-lg border p-3 bg-white text-sm">
        <p class="font-medium">现场联系（任务有效期内）</p>
        <a :href="`tel:${task.site_contact_phone}`" class="text-primary-600">{{ task.site_contact_phone }}</a>
      </div>

      <div v-if="checklist.length" class="rounded-lg border p-3 bg-white">
        <p class="font-medium text-sm mb-2">施工清单</p>
        <ul class="text-sm space-y-1 text-gray-700">
          <li v-for="(item, i) in checklist" :key="i">• {{ item }}</li>
        </ul>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          v-for="action in actions"
          :key="action.status"
          class="px-3 py-2 rounded-lg border text-sm"
          :disabled="busy"
          @click="setStatus(action.status)"
        >
          {{ action.label }}
        </button>
      </div>

      <div class="rounded-lg border p-3 bg-white space-y-3">
        <p class="font-medium text-sm">证据</p>
        <input ref="photoInput" type="file" accept="image/*" capture="environment" class="hidden" @change="addPhotoEvidence">
        <button class="text-sm text-primary-600" :disabled="busy" @click="photoInput?.click()">拍照记录</button>
        <p v-if="photoNotice" class="text-xs text-emerald-600">{{ photoNotice }}</p>
        <button class="text-sm text-primary-600 block" :disabled="busy" @click="addLocationEvidence">定位签到</button>
        <div class="space-y-2">
          <p class="text-xs text-gray-500">扫码绑定设备</p>
          <FieldQrScanner @scanned="onQrScanned" />
          <input v-model="qrCode" class="w-full border rounded px-2 py-1 text-sm" placeholder="扫描或输入 QR / 序列号" />
          <button class="text-sm text-primary-600" :disabled="busy || !qrCode.trim()" @click="bindQr">绑定设备</button>
        </div>
        <div v-if="showSignature" class="space-y-2">
          <p class="text-xs text-gray-500">客户现场签字</p>
          <input v-model="signerName" class="w-full border rounded px-2 py-1 text-sm" placeholder="签字人姓名（可选）" />
          <FieldSignaturePad @signed="onSigned" />
        </div>
        <button v-else class="text-sm text-primary-600" :disabled="busy" @click="showSignature = true">客户签字</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default', middleware: ['auth'] })

const route = useRoute()
const { apiFetch } = useApi()
const { online, queueStatusChange, queueEvidence, queuePhotoEvidence, flushQueue } = useFieldWorkerSync()

const task = ref<any>(null)
const error = ref('')
const busy = ref(false)
const qrCode = ref('')
const showSignature = ref(false)
const signerName = ref('')
const photoInput = ref<HTMLInputElement | null>(null)
const photoNotice = ref('')

const actions = [
  { status: 'in_progress', label: '开工' },
  { status: 'paused', label: '暂停' },
  { status: 'blocked', label: '阻塞' },
  { status: 'done', label: '完工' },
]

const checklist = computed(() => {
  const raw = task.value?.checklist_json
  if (Array.isArray(raw)) return raw
  if (raw?.items && Array.isArray(raw.items)) return raw.items
  return []
})

const mapsUrl = computed(() => {
  const addr = task.value?.site_json?.address
  if (!addr) return ''
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(String(addr))}`
})

async function load() {
  error.value = ''
  try {
    task.value = await apiFetch(`/field/tasks/${route.params.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to load'
  }
}

async function setStatus(status: string) {
  if (!task.value) return
  busy.value = true
  try {
    if (online.value) {
      task.value = await apiFetch(`/field/tasks/${task.value.id}/status`, {
        method: 'PATCH',
        body: { status, offline_version: task.value.offline_version },
      })
    } else {
      await queueStatusChange(task.value, status)
      task.value = { ...task.value, status, offline_version: task.value.offline_version + 1 }
    }
  } catch (e: any) {
    if (e?.response?.status === 409) {
      error.value = '版本冲突，请刷新后重试'
      await load()
    } else {
      error.value = e?.data?.detail || 'Update failed'
    }
  } finally {
    busy.value = false
  }
}

async function addPhotoEvidence(event: Event) {
  if (!task.value) return
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  busy.value = true
  error.value = ''
  try {
    await queuePhotoEvidence(task.value.id, file)
    photoNotice.value = online.value ? '照片已上传并提交证据。' : '照片已安全缓存，联网后自动上传。'
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Photo capture failed'
  } finally {
    busy.value = false
    if (photoInput.value) photoInput.value.value = ''
  }
}

async function addLocationEvidence() {
  if (!task.value || !navigator.geolocation) return
  navigator.geolocation.getCurrentPosition(async (pos) => {
    await queueEvidence(task.value.id, 'location', {
      lat: pos.coords.latitude,
      lng: pos.coords.longitude,
      captured_at: new Date().toISOString(),
    })
    await flushQueue()
  })
}

async function bindQr() {
  if (!task.value || !qrCode.value.trim()) return
  busy.value = true
  try {
    if (online.value) {
      await apiFetch(`/field/tasks/${task.value.id}/bind-qr`, {
        method: 'POST',
        body: { qr_code: qrCode.value.trim() },
      })
      qrCode.value = ''
    } else {
      await queueEvidence(task.value.id, 'qr', {
        qr_code: qrCode.value.trim(),
        captured_at: new Date().toISOString(),
      })
      qrCode.value = ''
    }
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'QR bind failed'
  } finally {
    busy.value = false
  }
}

function onQrScanned(value: string) {
  qrCode.value = value
}

async function onSigned(dataUrl: string) {
  if (!task.value) return
  busy.value = true
  try {
    if (online.value) {
      await apiFetch(`/field/tasks/${task.value.id}/signature`, {
        method: 'POST',
        body: {
          signature_data_url: dataUrl,
          signer_name: signerName.value || undefined,
          idempotency_key: `sig-${task.value.id}-${Date.now()}`,
        },
      })
      showSignature.value = false
      signerName.value = ''
    } else {
      await queueEvidence(task.value.id, 'signature', {
        signature_data_url: dataUrl,
        signer_name: signerName.value || undefined,
        captured_at: new Date().toISOString(),
      })
      showSignature.value = false
    }
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Signature failed'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
