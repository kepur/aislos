<template>
  <div class="px-4 py-4">
    <NuxtLink to="/partner/tasks" class="mb-4 inline-flex items-center gap-1 text-xs font-semibold text-blue-500">
      <span aria-hidden="true">&larr;</span> {{ $t('partner.backToTasks') }}
    </NuxtLink>

    <div v-if="loading" class="m-card text-center text-sm text-slate-400">{{ $t('partner.loadingTasks') }}</div>
    <div v-else-if="task" class="space-y-4">
      <div class="m-card">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-widest text-blue-500">{{ $t('partner.dispatchedTask') }}</p>
            <h1 class="mt-1 text-lg font-bold capitalize text-slate-800">{{ task.task_type?.replace(/_/g, ' ') || $t('partner.serviceTask') }}</h1>
          </div>
          <span :class="['status-pill shrink-0', statusClass(task.status)]">{{ task.status.replace(/_/g, ' ') }}</span>
        </div>
        <dl class="mt-4 space-y-2 text-xs">
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.project') }}</dt><dd class="text-right font-medium text-slate-700">{{ task.project_title || '—' }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.location') }}</dt><dd class="text-right font-medium text-slate-700">{{ task.project_region || '—' }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.due') }}</dt><dd class="text-right font-medium text-slate-700">{{ task.due_date || $t('partner.notSet') }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.workArea') }}</dt><dd class="text-right font-medium text-slate-700">{{ task.device_name || '—' }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-slate-400">{{ $t('partner.amcCoverage') }}</dt><dd class="text-right font-medium text-slate-700">{{ task.covered_by_amc ? $t('partner.yes') : $t('partner.no') }}</dd></div>
        </dl>
      </div>

      <div v-if="task.notes" class="m-card">
        <h2 class="text-sm font-bold text-slate-800">{{ $t('partner.instructions') }}</h2>
        <p class="mt-3 whitespace-pre-line text-xs leading-relaxed text-slate-600">{{ task.notes }}</p>
      </div>

      <div v-if="signingUrl" class="m-card border border-emerald-200 bg-emerald-50">
        <h2 class="text-sm font-bold text-emerald-800">{{ $t('partner.acceptanceSent') }}</h2>
        <p class="mt-2 text-xs text-emerald-700">{{ $t('partner.acceptanceHint') }}</p>
        <button class="m-btn mt-3 border border-emerald-300 bg-white text-emerald-700" @click="shareSigningLink">
          {{ $t('partner.shareSigningLink') }}
        </button>
        <p class="mt-2 break-all text-[10px] text-emerald-600">{{ signingUrl }}</p>
      </div>

      <div v-if="task.status !== 'done' && !signingUrl" class="m-card space-y-3">
        <button v-if="['scheduled', 'due'].includes(task.status)" :disabled="saving" class="m-btn-primary disabled:opacity-50" @click="changeStatus('in_progress')">
          {{ $t('partner.startTask') }}
        </button>

        <div v-if="task.status !== 'completed_pending_acceptance'">
          <button class="m-btn border border-emerald-200 bg-emerald-50 text-emerald-700" @click="showCompletion = !showCompletion">
            {{ $t('partner.submitCompletion') }}
          </button>

          <div v-if="showCompletion" class="mt-3 space-y-3">
            <div>
              <p class="mb-1 text-xs font-semibold text-slate-600">{{ $t('partner.sitePhotos') }}</p>
              <input type="file" accept="image/*" capture="environment" multiple class="text-xs" @change="onPhotos" />
              <p v-if="photos.length" class="mt-1 text-[10px] text-slate-400">{{ photos.length }} {{ $t('partner.photosUploaded') }}</p>
            </div>

            <div>
              <p class="mb-1 text-xs font-semibold text-slate-600">{{ $t('partner.installedDevices') }}</p>
              <div v-for="(d, i) in devices" :key="i" class="mb-2 grid grid-cols-3 gap-1">
                <input v-model="d.name" :placeholder="$t('partner.deviceName')" class="m-input text-xs" />
                <input v-model="d.serial" :placeholder="$t('partner.serialNo')" class="m-input text-xs" />
                <input v-model="d.room" :placeholder="$t('partner.room')" class="m-input text-xs" />
              </div>
              <button class="text-xs font-semibold text-blue-500" @click="devices.push({ name: '', serial: '', room: '' })">
                + {{ $t('partner.addDevice') }}
              </button>
            </div>

            <textarea v-model="completionNotes" rows="3" :placeholder="$t('partner.completionNotes')" class="m-input w-full text-xs"></textarea>

            <button :disabled="saving || uploading" class="m-btn-primary disabled:opacity-50" @click="submitCompletion">
              {{ saving ? $t('partner.submitting') : $t('partner.sendForAcceptance') }}
            </button>
          </div>
        </div>
        <p v-if="error" class="text-xs font-medium text-red-500">{{ error }}</p>
      </div>
    </div>
    <div v-else class="m-card text-center text-sm text-slate-500">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const { apiFetch } = useApi()
const task = ref<any>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')

function statusClass(status: string) {
  if (status === 'done') return 'bg-emerald-50 text-emerald-600'
  if (status === 'in_progress') return 'bg-amber-50 text-amber-600'
  return 'bg-blue-50 text-blue-600'
}
async function load() {
  loading.value = true
  try {
    task.value = await apiFetch<any>(`/partner/tasks/${route.params.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail || 'Task is unavailable.'
  } finally {
    loading.value = false
  }
}
async function changeStatus(status: string) {
  saving.value = true
  error.value = ''
  try {
    task.value = await apiFetch<any>(`/partner/tasks/${route.params.id}/status`, {
      method: 'PATCH',
      body: { status },
    })
  } catch (e: any) {
    error.value = e?.data?.detail || 'Task status could not be updated.'
  } finally {
    saving.value = false
  }
}

const showCompletion = ref(false)
const completionNotes = ref('')
const devices = ref<any[]>([{ name: '', serial: '', room: '' }])
const photos = ref<string[]>([])
const uploading = ref(false)
const signingUrl = ref('')

async function onPhotos(event: Event) {
  const files = (event.target as HTMLInputElement).files
  if (!files?.length) return
  uploading.value = true
  try {
    for (const file of Array.from(files)) {
      const presigned = await apiFetch<any>(
        `/files/upload-url?filename=${encodeURIComponent(file.name)}&content_type=${encodeURIComponent(file.type || 'image/jpeg')}`,
        { method: 'POST' },
      )
      await $fetch(presigned.upload_url, { method: 'PUT', body: file })
      photos.value.push(presigned.object_name)
    }
  } catch (e: any) {
    error.value = e?.data?.detail || 'Photo upload failed.'
  } finally {
    uploading.value = false
  }
}

async function submitCompletion() {
  saving.value = true
  error.value = ''
  try {
    const res = await apiFetch<any>(`/partner/tasks/${route.params.id}/complete`, {
      method: 'POST',
      body: {
        notes: completionNotes.value || null,
        photos: photos.value,
        devices: devices.value.filter((d) => d.name),
      },
    })
    signingUrl.value = res.customer_signing_url
    await load()
  } catch (e: any) {
    error.value = e?.data?.detail || 'Completion could not be submitted.'
  } finally {
    saving.value = false
  }
}

async function shareSigningLink() {
  if (navigator.share) {
    await navigator.share({ title: 'AinerWise acceptance', url: signingUrl.value }).catch(() => {})
  } else {
    await navigator.clipboard?.writeText(signingUrl.value)
  }
}

onMounted(load)
</script>
