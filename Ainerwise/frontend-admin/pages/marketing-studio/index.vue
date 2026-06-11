<template>
  <div>
    <div class="mb-6">
      <h1 class="admin-page-title">Marketing Studio</h1>
      <p class="admin-page-desc">AI content & SEO pages from your own products/cases. Everything reviewed before publishing.</p>
    </div>

    <div class="grid gap-4 md:grid-cols-2 mb-6">
      <div class="admin-panel p-4">
        <h2 class="font-medium text-gray-900 mb-3">Generate content</h2>
        <div class="space-y-2">
          <input v-model="genForm.product_id" placeholder="Product ID (or leave empty and use Case ID)" class="input-field w-full" />
          <input v-model="genForm.case_id" placeholder="Case ID" class="input-field w-full" />
          <div class="flex gap-2">
            <select v-model="genForm.channel" class="input-field flex-1">
              <option v-for="c in ['linkedin','facebook','instagram','blog','email','tiktok']" :key="c" :value="c">{{ c }}</option>
            </select>
            <select v-model="genForm.lang" class="input-field w-24">
              <option v-for="l in ['en','zh','sr','pl']" :key="l" :value="l">{{ l }}</option>
            </select>
          </div>
          <button class="btn-primary text-sm px-4 py-2" :disabled="busy || (!genForm.product_id && !genForm.case_id)" @click="generate">Generate draft</button>
        </div>
      </div>

      <div class="admin-panel p-4">
        <h2 class="font-medium text-gray-900 mb-3">Generate SEO page</h2>
        <div class="space-y-2">
          <input v-model="seoForm.target_keyword" placeholder="Target keyword (e.g. KNX installer Warsaw)" class="input-field w-full" />
          <select v-model="seoForm.lang" class="input-field w-24">
            <option v-for="l in ['en','zh','sr','pl']" :key="l" :value="l">{{ l }}</option>
          </select>
          <button class="btn-primary text-sm px-4 py-2" :disabled="busy || !seoForm.target_keyword" @click="generateSeo">Generate page</button>
        </div>
        <h3 class="font-medium text-gray-900 mt-4 mb-2 text-sm">SEO pages</h3>
        <div class="space-y-1 text-sm max-h-48 overflow-y-auto">
          <div v-for="p in seoPages" :key="p.id" class="flex items-center justify-between border-b py-1.5">
            <span class="text-gray-800 truncate mr-2">{{ p.title }}</span>
            <div class="flex items-center gap-2 shrink-0">
              <StatusBadge :status="p.status" />
              <button v-if="p.status !== 'published'" class="text-xs text-primary-600 hover:underline" :disabled="busy" @click="publishSeo(p)">Publish</button>
              <a v-else :href="`http://localhost:4099/insights/${p.slug}`" target="_blank" class="text-xs text-gray-500 hover:underline">View</a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="admin-panel">
      <div class="flex items-center justify-between px-4 pt-4">
        <h2 class="font-medium text-gray-900">Marketing assets</h2>
        <select v-model="assetFilter" class="input-field max-w-40" @change="loadAssets">
          <option value="">All statuses</option>
          <option v-for="s in ['in_review','approved','scheduled','published']" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <table class="admin-table w-full text-sm mt-2">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Channel / lang</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Content</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in assets" :key="a.id" class="border-b align-top">
            <td class="px-4 py-3 text-gray-600 whitespace-nowrap">{{ a.channel || a.kind }} · {{ a.lang }}</td>
            <td class="px-4 py-3 max-w-md">
              <p class="font-medium text-gray-900">{{ a.title }}</p>
              <p class="text-xs text-gray-500 line-clamp-3 whitespace-pre-wrap">{{ a.content }}</p>
            </td>
            <td class="px-4 py-3"><StatusBadge :status="a.status" /></td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex gap-2">
                <button v-if="a.status === 'in_review'" class="btn-primary text-xs px-3 py-1.5" :disabled="busy" @click="approve(a)">Approve</button>
                <button v-if="a.status === 'approved'" class="text-xs px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50" :disabled="busy" @click="schedule(a)">Schedule</button>
              </div>
            </td>
          </tr>
          <tr v-if="!assets.length"><td colspan="4" class="px-4 py-8 text-center text-gray-500">No assets yet — generate some above.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const assets = ref<any[]>([])
const seoPages = ref<any[]>([])
const assetFilter = ref('')
const busy = ref(false)
const genForm = ref<any>({ product_id: '', case_id: '', channel: 'linkedin', lang: 'en' })
const seoForm = ref<any>({ target_keyword: '', lang: 'en' })

async function loadAssets() {
  const params = assetFilter.value ? `?status=${assetFilter.value}` : ''
  const res = await apiFetch<any>(`/admin/marketing/assets${params}`)
  assets.value = res.items || []
}

async function loadSeo() {
  const res = await apiFetch<any>('/admin/seo/pages')
  seoPages.value = res.items || []
}

async function generate() {
  busy.value = true
  try {
    await apiFetch('/admin/marketing/generate', {
      method: 'POST',
      body: {
        product_id: genForm.value.product_id || null,
        case_id: genForm.value.case_id || null,
        channels: [genForm.value.channel],
        langs: [genForm.value.lang],
      },
    })
    await loadAssets()
  } finally {
    busy.value = false
  }
}

async function generateSeo() {
  busy.value = true
  try {
    await apiFetch('/admin/seo/pages/generate', { method: 'POST', body: seoForm.value })
    seoForm.value.target_keyword = ''
    await loadSeo()
  } finally {
    busy.value = false
  }
}

async function publishSeo(p: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/seo/pages/${p.id}/publish`, { method: 'POST' })
    await loadSeo()
  } finally {
    busy.value = false
  }
}

async function approve(a: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/marketing/assets/${a.id}/approve`, { method: 'POST', body: {} })
    await loadAssets()
  } finally {
    busy.value = false
  }
}

async function schedule(a: any) {
  const when = window.prompt('Publish at (ISO, e.g. 2026-06-11T09:00:00+00:00):', new Date(Date.now() + 3600e3).toISOString())
  if (!when) return
  busy.value = true
  try {
    await apiFetch(`/admin/marketing/assets/${a.id}/schedule`, {
      method: 'POST',
      body: { platform: a.channel || 'linkedin', scheduled_at: when },
    })
    await loadAssets()
  } finally {
    busy.value = false
  }
}

onMounted(() => Promise.all([loadAssets(), loadSeo()]))
</script>
