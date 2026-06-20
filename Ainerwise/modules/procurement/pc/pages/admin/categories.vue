<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Taxonomy & Category Schema</h1>
        <p class="text-sm text-slate-500 mt-1">
          {{ total }} active Core categories loaded from AinerWise taxonomy.
        </p>
      </div>
      <UButton color="gray" icon="i-heroicons-lock-closed" disabled>
        Managed in Core Seed
      </UButton>
    </div>

    <UCard>
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
        <UInput
          v-model="keyword"
          icon="i-heroicons-magnifying-glass"
          placeholder="Search categories..."
          class="max-w-sm"
        />
        <UButton color="gray" variant="ghost" icon="i-heroicons-arrow-path" :loading="loading" @click="loadCategories">
          Refresh
        </UButton>
      </div>

      <UAlert
        v-if="error"
        color="red"
        variant="soft"
        icon="i-heroicons-exclamation-triangle"
        class="mb-4"
        :title="error"
      />

      <UTable :columns="columns" :rows="filteredCategories" :loading="loading">
        <template #id-data="{ row }">
          <span class="font-mono text-xs text-slate-500">{{ shortId(row.id) }}</span>
        </template>
        <template #name-data="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="text-xs text-slate-400">{{ row.slug || 'No slug' }}</p>
          </div>
        </template>
        <template #schema_fields-data="{ row }">
          <UBadge color="indigo" variant="soft">
            {{ schemaFieldCount(row.schema_json) }} fields
          </UBadge>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'ACTIVE' ? 'green' : 'gray'" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #created_at-data="{ row }">
          <span class="text-xs text-slate-500">{{ formatDate(row.created_at) }}</span>
        </template>
        <template #actions-data>
          <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye" disabled>
            Read-only
          </UButton>
        </template>
      </UTable>

      <div v-if="!loading && filteredCategories.length === 0" class="py-10 text-center text-sm text-slate-500">
        <p>No categories match the current search.</p>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: ['admin'] })

interface CategoryRow {
  id: string
  slug?: string
  name: string
  description?: string | null
  icon?: string | null
  schema_json?: Record<string, any>
  status: string
  created_at?: string
}

const config = useRuntimeConfig()
const authStore = useAuthStore()

const keyword = ref('')
const loading = ref(false)
const error = ref('')
const categories = ref<CategoryRow[]>([])

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Category' },
  { key: 'description', label: 'Description' },
  { key: 'schema_fields', label: 'Schema' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Created' },
  { key: 'actions', label: 'Actions' }
]

const total = computed(() => categories.value.length)
const filteredCategories = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  if (!q) return categories.value
  return categories.value.filter((row) =>
    [row.name, row.slug, row.description, row.id]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q))
  )
})

async function loadCategories() {
  loading.value = true
  error.value = ''
  try {
    const data = await $fetch<CategoryRow[]>(`${config.public.apiBase}/categories`, {
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
    })
    categories.value = (data ?? []).map((row) => ({
      ...row,
      status: row.status || 'UNKNOWN',
      description: row.description || schemaDescription(row.schema_json) || 'No description provided.',
    }))
  } catch (e: any) {
    console.error('Admin categories fetch error:', e)
    categories.value = []
    const detail = e?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Failed to load Core categories.'
  } finally {
    loading.value = false
  }
}

function schemaDescription(schema?: Record<string, any>) {
  return typeof schema?.description === 'string' ? schema.description : ''
}

function schemaFieldCount(schema?: Record<string, any>) {
  const properties = schema?.properties
  if (!properties || typeof properties !== 'object') return 0
  return Object.keys(properties).length
}

function shortId(value: string) {
  return value ? value.slice(0, 8) : '—'
}

function formatDate(value?: string) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-PH', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(loadCategories)
</script>
