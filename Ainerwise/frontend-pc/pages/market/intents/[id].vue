<template>
  <div class="space-y-6">
    <NuxtLink :to="localized('/market/intents')" :class="['text-sm hover:underline', brand.accentText]">← {{ $t('intents.backList') }}</NuxtLink>
    <p v-if="loading" class="pc-card text-sm text-slate-400">{{ $t('common.loading') }}</p>
    <p v-else-if="error" class="text-sm text-red-400">{{ error }}</p>
    <template v-else-if="intent">
      <div class="pc-card space-y-2">
        <h1 class="text-2xl font-bold text-white">{{ intent.title }}</h1>
        <p class="text-sm text-slate-500">{{ $t('intents.statusPrefix', { status: intent.status }) }}</p>
        <p v-if="intent.description" class="text-slate-300">{{ intent.description }}</p>
        <button
          v-if="intent.status === 'draft'"
          type="button"
          class="mt-3 rounded-lg bg-gradient-to-r px-4 py-2 text-sm font-semibold text-white"
          :class="brand.accent"
          :disabled="publishing"
          @click="publish"
        >
          {{ publishing ? $t('reqDetail.publishing') : $t('reqDetail.publish') }}
        </button>
      </div>

      <div v-if="intent.status !== 'draft'" class="pc-card">
        <h2 class="font-semibold text-white mb-3">{{ $t('intents.matchSuppliers') }}</h2>
        <p v-if="candidatesLoading" class="text-sm text-slate-400">{{ $t('intents.loadingCandidates') }}</p>
        <ul v-else class="space-y-2 text-sm">
          <li v-for="c in candidates" :key="c.id" class="rounded-lg border border-white/10 p-3 text-slate-300">
            {{ c.title }} · {{ c.price_minor ? (c.price_minor / 100).toFixed(2) : '—' }} {{ c.currency }}
          </li>
          <li v-if="!candidates.length" class="text-slate-500">{{ $t('intents.noSuppliers') }}</li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
const { t } = useI18n()
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const route = useRoute()
const id = String(route.params.id)
const { bootstrap } = useCebuPortalShell()
const policy = useState('procurement-portal-policy')
const { brand } = useProcurementBrand(policy)
const { getProcurementRequest, publishRequest, listCandidates } = useCommerce()
const intent = ref<any>(null)
const candidates = ref<any[]>([])
const loading = ref(true)
const candidatesLoading = ref(false)
const publishing = ref(false)
const error = ref('')

async function loadCandidates() {
  candidatesLoading.value = true
  try {
    const res = await listCandidates(id)
    candidates.value = res.items
  } catch {
    candidates.value = []
  } finally {
    candidatesLoading.value = false
  }
}

async function publish() {
  publishing.value = true
  try {
    intent.value = await publishRequest(id)
    await loadCandidates()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('reqDetail.publishFailed')
  } finally {
    publishing.value = false
  }
}

onMounted(async () => {
  await bootstrap()
  try {
    intent.value = await getProcurementRequest(id)
    if (intent.value?.status !== 'draft') await loadCandidates()
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || t('intents.loadFailed')
  } finally {
    loading.value = false
  }
})
</script>
