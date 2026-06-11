<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <div class="flex items-center gap-4 mb-6">
      <UButton color="gray" variant="ghost" icon="i-heroicons-arrow-left" to="/supplier/ads" />
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Create Campaign</h1>
        <p class="text-slate-500 mt-1">Set up your advertising campaign.</p>
      </div>
    </div>

    <UCard>
      <div class="space-y-5">
        <UFormGroup label="Campaign Title" required>
          <UInput v-model="form.title" placeholder="e.g. Summer Sale Promotion" />
        </UFormGroup>

        <UFormGroup label="Placement Type" required>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button v-for="p in placements" :key="p.value" @click="form.placement = p.value"
              type="button"
              :class="['p-3 rounded-xl border text-left transition-all', form.placement === p.value ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500' : 'border-slate-200 hover:border-indigo-300']">
              <div class="text-xl mb-1">{{ p.icon }}</div>
              <div class="font-semibold text-sm text-slate-900">{{ p.label }}</div>
              <div class="text-[10px] text-slate-500 mt-1">{{ p.desc }}</div>
            </button>
          </div>
        </UFormGroup>

        <UFormGroup label="Promote Catalog Item (Optional)">
          <USelect v-model="form.catalog_item_id" :options="catalogOptions" option-attribute="label" value-attribute="value" />
        </UFormGroup>

        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Total Budget (USD)" required>
            <UInput v-model.number="budgetInput" type="number" min="10" placeholder="100" />
          </UFormGroup>
          <UFormGroup label="Max Bid Per Click (USD)" required>
            <UInput v-model.number="bidInput" type="number" min="0.1" step="0.1" placeholder="0.5" />
          </UFormGroup>
        </div>

        <UFormGroup label="Target Keywords (Optional)">
          <UInput v-model="keywordsInput" placeholder="Comma separated keywords (e.g. masks, medical, PPE)" />
        </UFormGroup>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <UButton color="gray" variant="ghost" to="/supplier/ads">Cancel</UButton>
          <UButton color="indigo" :loading="saving" @click="save">Create Campaign</UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'supplier', middleware: ['supplier'] })

const config = useRuntimeConfig()
const authStore = useAuthStore()
const toast = useToast()
const router = useRouter()

const saving = ref(false)
const catalogOptions = ref([{ label: 'None (Brand/Profile Ad)', value: '' }])

const placements = [
  { value: 'SEARCH_TOP', label: 'Search Top', icon: '🔍', desc: 'Show at the top of search results' },
  { value: 'CATEGORY_TOP', label: 'Category Top', icon: '🗂️', desc: 'Show at the top of category pages' },
  { value: 'HOMEPAGE_BANNER', label: 'Homepage', icon: '✨', desc: 'Featured on marketplace homepage' },
]

const form = reactive({
  title: '',
  placement: 'SEARCH_TOP',
  catalog_item_id: '',
})
const budgetInput = ref(100)
const bidInput = ref(0.5)
const keywordsInput = ref('')

onMounted(async () => {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/supplier/catalog/items`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    const items = data?.items || data || []
    if (items.length) {
      catalogOptions.value = [
        { label: 'None (Brand/Profile Ad)', value: '' },
        ...items.map((i: any) => ({ label: i.title, value: i.id }))
      ]
    }
  } catch (e) {
    console.error('Failed to load catalog', e)
  }
})

async function save() {
  if (!form.title) {
    toast.add({ title: 'Title is required', color: 'red' })
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.title,
      placement: form.placement,
      catalog_item_id: form.catalog_item_id || undefined,
      budget_minor: Math.round(budgetInput.value * 100),
      bid_per_click_minor: Math.round(bidInput.value * 100),
      currency: 'USD',
      target_keywords: keywordsInput.value ? keywordsInput.value.split(',').map(s => s.trim()) : undefined
    }

    await $fetch(`${config.public.apiBase}/merchant/ad-campaigns`, {
      method: 'POST',
      body: payload,
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    
    toast.add({ title: 'Campaign created successfully', color: 'green' })
    router.push('/supplier/ads')
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Failed to create campaign', color: 'red' })
  } finally {
    saving.value = false
  }
}
</script>
