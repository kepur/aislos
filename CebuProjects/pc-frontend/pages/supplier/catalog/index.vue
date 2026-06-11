<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">My Catalog</h1>
        <p class="text-sm text-slate-500 mt-1">Manage items you sell. Our AI uses this to match you with buyer requests.</p>
      </div>
      <div class="flex gap-2">
        <UButton color="gray" variant="outline" icon="i-heroicons-arrow-path" :loading="loading" @click="load">Refresh</UButton>
        <UButton color="indigo" icon="i-heroicons-plus" @click="openCreate">Add Item</UButton>
      </div>
    </div>

    <UAlert
      v-if="companyMissing"
      color="amber"
      icon="i-heroicons-building-office-2"
      title="Complete your supplier profile"
      description="Catalog items are listed under your company. Finish KYB to verify your business, or continue listing with your draft profile."
    >
      <template #actions>
        <UButton size="sm" color="amber" variant="solid" to="/register-supplier">Complete KYB</UButton>
      </template>
    </UAlert>
    <UAlert
      v-else-if="company"
      color="blue"
      variant="soft"
      icon="i-heroicons-building-office-2"
      :title="`Listing as: ${company.name}`"
      :description="company.status === 'ACTIVE' ? 'Verified supplier company' : 'Company profile pending verification'"
    />

    <!-- Stats row -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <UCard class="text-center">
        <p class="text-2xl font-bold text-slate-900">{{ total }}</p>
        <p class="text-xs text-slate-500 mt-1">Total Items</p>
      </UCard>
      <UCard class="text-center">
        <p class="text-2xl font-bold text-green-600">{{ items.filter(i => i.status === 'ACTIVE').length }}</p>
        <p class="text-xs text-slate-500 mt-1">Active</p>
      </UCard>
      <UCard class="text-center">
        <p class="text-2xl font-bold text-amber-600">{{ items.filter(i => (i.stock_qty || 0) < 10).length }}</p>
        <p class="text-xs text-slate-500 mt-1">Low Stock</p>
      </UCard>
      <UCard class="text-center">
        <p class="text-2xl font-bold text-indigo-600">{{ items.filter(i => i.market_mode === 'B2C' || i.market_mode === 'BOTH').length }}</p>
        <p class="text-xs text-slate-500 mt-1">B2C Listed</p>
      </UCard>
    </div>

    <!-- Filters -->
    <UCard :ui="{ body: { padding: 'p-4' } }">
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative max-w-xs">
          <span class="absolute inset-y-0 left-3 flex items-center pointer-events-none"><svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg></span>
          <input v-model="keyword" type="text" placeholder="Search catalog..."
            class="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-4 py-2 text-sm text-slate-800 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
        </div>
        <USelect v-model="statusFilter" :options="statusOptions" option-attribute="label" value-attribute="value" @change="load" />
        <USelect v-model="modeFilter" :options="modeOptions" option-attribute="label" value-attribute="value" @change="load" />
      </div>
    </UCard>

    <!-- Table -->
    <UCard>
      <UTable :columns="columns" :rows="items" :loading="loading">
        <template #title-data="{ row }">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl overflow-hidden bg-slate-100 flex-shrink-0">
              <img v-if="row.images && row.images[0]" :src="row.images[0]" :alt="row.title" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center text-xl">📦</div>
            </div>
            <div>
              <p class="font-semibold text-slate-900">{{ row.title }}</p>
              <p class="text-xs text-slate-400">{{ row.category_name }}</p>
            </div>
          </div>
        </template>
        <template #price-data="{ row }">
          <span class="font-medium text-slate-900">{{ formatMinor(row.price_minor, row.currency) }}</span>
          <span class="text-xs text-slate-400 ml-1">/{{ row.unit }}</span>
        </template>
        <template #stock_qty-data="{ row }">
          <UBadge :color="(row.stock_qty || 0) > 50 ? 'green' : (row.stock_qty || 0) > 0 ? 'yellow' : 'red'" variant="subtle" size="xs">
            {{ (row.stock_qty || 0) > 0 ? `${row.stock_qty} in stock` : 'Out of Stock' }}
          </UBadge>
        </template>
        <template #market_mode-data="{ row }">
          <div class="flex gap-1">
            <UBadge v-if="row.market_mode === 'B2B' || row.market_mode === 'BOTH'" color="blue" variant="soft" size="xs">B2B</UBadge>
            <UBadge v-if="row.market_mode === 'B2C' || row.market_mode === 'BOTH'" color="green" variant="soft" size="xs">B2C</UBadge>
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'ACTIVE' ? 'green' : row.status === 'INACTIVE' ? 'yellow' : 'red'" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-pencil-square" @click="editItem(row)" />
            <UButton
              size="xs"
              :color="row.status === 'ACTIVE' ? 'yellow' : 'green'"
              variant="ghost"
              :icon="row.status === 'ACTIVE' ? 'i-heroicons-pause' : 'i-heroicons-play'"
              @click="toggleStatus(row)"
            />
            <UButton size="xs" color="red" variant="ghost" icon="i-heroicons-trash" @click="deleteItem(row)" />
          </div>
        </template>
      </UTable>

      <div class="flex items-center justify-between mt-4">
        <p class="text-sm text-slate-500">{{ total }} items total</p>
        <div class="flex gap-2">
          <UButton size="sm" color="gray" variant="outline" :disabled="page <= 1" @click="page--; load()">← Prev</UButton>
          <UButton size="sm" color="gray" variant="outline" :disabled="!hasNext" @click="page++; load()">Next →</UButton>
        </div>
      </div>
    </UCard>

    <!-- Create/Edit Modal -->
    <UModal v-model="showModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">{{ editingItem ? 'Edit Item' : 'Add Catalog Item' }}</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Title">
            <UInput v-model="form.title" placeholder="Product title" />
          </UFormGroup>
          <UFormGroup label="Category">
            <USelect v-model="form.category_id" :options="categoryOptions" option-attribute="label" value-attribute="value" placeholder="Select category" />
          </UFormGroup>
          <UFormGroup label="Product Images">
            <div class="space-y-3">
              <div class="grid grid-cols-5 gap-2">
                <div v-for="(image, idx) in form.images" :key="`${image}-${idx}`" class="relative aspect-square overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
                  <img :src="image" :alt="`Product image ${idx + 1}`" class="h-full w-full object-cover" />
                  <button type="button" class="absolute right-1 top-1 rounded-full bg-white/90 p-1 text-slate-700 shadow" @click="removeImage(idx)">
                    <UIcon name="i-heroicons-x-mark" class="h-4 w-4" />
                  </button>
                </div>
                <button
                  v-if="form.images.length < maxImages"
                  type="button"
                  class="aspect-square rounded-xl border border-dashed border-slate-300 bg-slate-50 text-xs font-semibold text-slate-500 hover:border-indigo-300 hover:text-indigo-600"
                  :disabled="uploadingImages"
                  @click="imageInput?.click()"
                >
                  {{ uploadingImages ? 'Uploading...' : '+ Upload' }}
                </button>
              </div>
              <input ref="imageInput" type="file" accept="image/jpeg,image/png,image/webp" multiple class="hidden" @change="handleImageFiles" />
              <div class="flex gap-2">
                <UInput v-model="imageUrlInput" placeholder="Or paste image URL" />
                <UButton color="gray" variant="outline" :disabled="form.images.length >= maxImages" @click="addImageUrl">Add URL</UButton>
              </div>
              <p class="text-xs text-slate-500">{{ form.images.length }}/{{ maxImages }} images. First image is used as the product cover.</p>
            </div>
          </UFormGroup>
          <div class="grid grid-cols-2 gap-3">
            <UFormGroup label="Price (per unit, minor)">
              <UInput v-model.number="form.price_minor" type="number" placeholder="e.g. 42000 = ₱420" />
            </UFormGroup>
            <UFormGroup label="Unit">
              <UInput v-model="form.unit" placeholder="bag, pc, kg..." />
            </UFormGroup>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <UFormGroup label="Stock Qty">
              <UInput v-model.number="form.stock_qty" type="number" />
            </UFormGroup>
            <UFormGroup label="Market Mode">
              <USelect v-model="form.market_mode" :options="['B2B','B2C','BOTH']" />
            </UFormGroup>
          </div>
          <UFormGroup label="Description">
            <UTextarea v-model="form.description" rows="3" placeholder="Product details..." />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showModal = false">Cancel</UButton>
            <UButton color="indigo" :loading="saving" @click="saveItem">{{ editingItem ? 'Save Changes' : 'Create Item' }}</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'supplier', middleware: ['supplier'] })

const authStore = useAuthStore()
const config = useRuntimeConfig()
const toast = useToast()

const keyword = ref('')
const statusFilter = ref('')
const modeFilter = ref('')
const page = ref(1)
const loading = ref(false)
const saving = ref(false)
const items = ref<any[]>([])
const categories = ref<any[]>([])
const company = ref<{ name: string; status: string } | null>(null)
const companyMissing = ref(false)
const total = ref(0)
const hasNext = ref(false)
const showModal = ref(false)
const editingItem = ref<any>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const imageUrlInput = ref('')
const uploadingImages = ref(false)
const maxImages = 10

const form = ref({
  category_id: '',
  title: '',
  price_minor: 0,
  unit: 'pc',
  stock_qty: 0,
  market_mode: 'B2B',
  description: '',
  images: [] as string[],
})

const categoryOptions = computed(() => categories.value.map((cat) => ({ label: cat.name, value: cat.id })))

const statusOptions = [
  { label: 'All Status', value: '' },
  { label: 'Active', value: 'ACTIVE' },
  { label: 'Inactive', value: 'INACTIVE' },
]
const modeOptions = [
  { label: 'All Modes', value: '' },
  { label: 'B2B Only', value: 'B2B' },
  { label: 'B2C Only', value: 'B2C' },
  { label: 'Both', value: 'BOTH' },
]

const columns = [
  { key: 'title', label: 'Product' },
  { key: 'price', label: 'Price' },
  { key: 'stock_qty', label: 'Stock' },
  { key: 'market_mode', label: 'Mode' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
]

function formatMinor(minor: number, currency = 'PHP') {
  if (!minor) return '—'
  const amount = minor / 100
  try { return new Intl.NumberFormat('en-PH', { style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount) }
  catch { return `${amount.toLocaleString()} ${currency}` }
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: 20 }
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    if (modeFilter.value) params.market_mode = modeFilter.value
    const data = await $fetch<any>(`${config.public.apiBase}/supplier/catalog/items`, {
      params,
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    items.value = data.items ?? data ?? []
    total.value = data.total ?? items.value.length
    hasNext.value = data.has_next ?? false
  } catch (e: any) {
    console.error('Catalog fetch error:', e)
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/categories`)
    categories.value = Array.isArray(data) ? data : (data.items ?? [])
  } catch {
    categories.value = []
  }
}

async function loadCompany() {
  try {
    company.value = await $fetch<any>(`${config.public.apiBase}/companies/me`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    companyMissing.value = false
  } catch (e: any) {
    if (e?.statusCode === 404 || e?.response?.status === 404) {
      company.value = null
      companyMissing.value = true
    }
  }
}

function openCreate() {
  editingItem.value = null
  form.value = {
    category_id: '',
    title: '',
    price_minor: 0,
    unit: 'pc',
    stock_qty: 0,
    market_mode: 'B2B',
    description: '',
    images: [],
  }
  imageUrlInput.value = ''
  showModal.value = true
}

function editItem(item: any) {
  editingItem.value = item
  form.value = {
    category_id: item.category_id || '',
    title: item.title,
    price_minor: item.price_minor,
    unit: item.unit,
    stock_qty: item.stock_qty,
    market_mode: item.market_mode,
    description: item.description || '',
    images: [...(item.images || [])].slice(0, maxImages),
  }
  imageUrlInput.value = ''
  showModal.value = true
}

async function handleImageFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const selected = Array.from(input.files || []).filter((file) => file.type.startsWith('image/'))
  input.value = ''
  if (!selected.length) return
  const remaining = maxImages - form.value.images.length
  if (remaining <= 0) {
    toast.add({ title: `Maximum ${maxImages} images allowed`, color: 'red' })
    return
  }
  if (selected.length > remaining) {
    toast.add({ title: `Only ${remaining} more image(s) can be uploaded`, color: 'red' })
  }
  uploadingImages.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.accessToken}` }
    for (const file of selected.slice(0, remaining)) {
      const fd = new FormData()
      fd.append('file', file)
      const res = await $fetch<{ url: string }>(`${config.public.apiBase}/uploads`, { method: 'POST', body: fd, headers })
      form.value.images.push(res.url)
    }
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Image upload failed', color: 'red' })
  } finally {
    uploadingImages.value = false
  }
}

function addImageUrl() {
  const url = imageUrlInput.value.trim()
  if (!url) return
  if (form.value.images.length >= maxImages) {
    toast.add({ title: `Maximum ${maxImages} images allowed`, color: 'red' })
    return
  }
  form.value.images.push(url)
  imageUrlInput.value = ''
}

function removeImage(index: number) {
  form.value.images.splice(index, 1)
}

async function saveItem() {
  saving.value = true
  try {
    if (!form.value.category_id) {
      toast.add({ title: 'Please select a category', color: 'red' })
      return
    }
    const headers = { Authorization: `Bearer ${authStore.accessToken}` }
    const body = { ...form.value, images: form.value.images.filter(Boolean).slice(0, maxImages) }
    if (editingItem.value) {
      await $fetch(`${config.public.apiBase}/supplier/catalog/items/${editingItem.value.id}`, {
        method: 'PATCH',
        body,
        headers,
      })
      toast.add({ title: 'Item updated!', color: 'green' })
    } else {
      await $fetch(`${config.public.apiBase}/supplier/catalog/items`, {
        method: 'POST',
        body,
        headers,
      })
      toast.add({ title: 'Item created!', color: 'green' })
    }
    showModal.value = false
    await load()
  } catch (e: any) {
    const detail = e?.data?.detail
    const msg = typeof detail === 'string' ? detail : 'Save failed'
    if (msg.toLowerCase().includes('company')) {
      toast.add({
        title: 'Supplier company profile required',
        description: 'Complete your company/KYB profile, then try again.',
        color: 'red',
      })
      companyMissing.value = true
    } else {
      toast.add({ title: msg, color: 'red' })
    }
  } finally {
    saving.value = false
  }
}

async function toggleStatus(item: any) {
  const newStatus = item.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
  try {
    await $fetch(`${config.public.apiBase}/supplier/catalog/items/${item.id}`, {
      method: 'PATCH',
      body: { status: newStatus },
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    item.status = newStatus
    toast.add({ title: `Item ${newStatus.toLowerCase()}`, color: 'green' })
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Update failed', color: 'red' })
  }
}

async function deleteItem(item: any) {
  if (!confirm(`Delete "${item.title}"?`)) return
  try {
    await $fetch(`${config.public.apiBase}/supplier/catalog/items/${item.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    })
    toast.add({ title: 'Item deleted', color: 'green' })
    await load()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Delete failed', color: 'red' })
  }
}

onMounted(() => {
  loadCompany()
  loadCategories()
  load()
})
</script>
