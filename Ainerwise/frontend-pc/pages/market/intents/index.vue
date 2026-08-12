<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p :class="['text-xs font-bold uppercase tracking-wider', brand.accentText]">Intents</p>
        <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('intents.title') }}</h1>
        <p class="text-sm text-slate-500">Core API · portal_key=cebu</p>
      </div>
      <button
        type="button"
        class="rounded-lg bg-gradient-to-r px-4 py-2 text-sm font-semibold text-white shadow-lg"
        :class="brand.accent"
        @click="showCreate = true"
      >
        {{ $t('intents.newReq') }}
      </button>
    </div>

    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
    <p v-if="loading" class="pc-card text-sm text-slate-400">{{ $t('common.loading') }}</p>

    <div v-else class="space-y-3">
      <NuxtLink
        v-for="item in items"
        :key="item.id"
        :to="localized(`/market/intents/${item.id}`)"
        class="pc-card block hover:border-white/20 transition"
      >
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="font-semibold text-white">{{ item.title }}</h2>
            <p class="mt-1 text-xs text-slate-500">{{ item.portal_key || 'cebu' }}</p>
          </div>
          <span class="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-slate-300">
            {{ item.status.replace(/_/g, ' ') }}
          </span>
        </div>
      </NuxtLink>
      <p v-if="!items.length" class="pc-card text-sm text-slate-400">{{ $t('intents.empty') }}</p>
    </div>

    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <form class="pc-card w-full max-w-lg space-y-4" @submit.prevent="createIntent">
        <h2 class="text-lg font-bold text-white">{{ $t('intents.createTitle') }}</h2>
        <div>
          <label class="mb-1 block text-sm text-slate-400">{{ $t('reqForm.rTitle') }}</label>
          <input v-model="form.title" required class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-sm text-slate-400">{{ $t('intents.descLabel') }}</label>
          <textarea v-model="form.description" class="input-field" rows="3" />
        </div>
        <p v-if="createError" class="text-sm text-red-400">{{ createError }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-secondary" @click="showCreate = false">{{ $t('common.cancel') }}</button>
          <button type="submit" class="btn-primary" :disabled="creating">{{ creating ? $t('reqForm.submitting') : $t('common.create') }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const { bootstrap } = useCebuPortalShell()
const policy = useState('procurement-portal-policy')
const { brand } = useProcurementBrand(policy)
const { listProcurementRequests, createProcurementRequest } = useCommerce()
const items = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const form = reactive({ title: '', description: '' })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await listProcurementRequests()
    items.value = res.items.filter((i: any) => (i.portal_key || 'cebu') === 'cebu')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('intents.loadFailed')
  } finally {
    loading.value = false
  }
}

async function createIntent() {
  creating.value = true
  createError.value = ''
  try {
    const row = await createProcurementRequest({
      title: form.title,
      description: form.description || undefined,
    })
    showCreate.value = false
    form.title = ''
    form.description = ''
    await navigateTo(`/market/intents/${(row as any).id}`)
  } catch (e: any) {
    createError.value = e?.data?.detail || e?.message || t('intents.createFailed')
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await bootstrap()
  await load()
})
</script>
