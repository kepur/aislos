<template>
  <div class="space-y-6">
    <!-- What needs a human right now -->
    <div class="grid grid-cols-4 gap-4">
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">To publish</p>
        <p class="text-2xl font-bold text-amber-600">{{ counts.post }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">To take down</p>
        <p class="text-2xl font-bold text-rose-600">{{ counts.take_down }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">Failed</p>
        <p class="text-2xl font-bold text-slate-500">{{ counts.retry }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-slate-500 mb-1">Active channels</p>
        <p class="text-2xl font-bold text-green-600">{{ activeChannels }}</p>
      </div>
    </div>

    <!-- Operator queue -->
    <div class="card overflow-hidden">
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-3">
        <div>
          <h2 class="text-sm font-semibold text-slate-900">Action queue</h2>
          <p class="mt-0.5 text-xs text-slate-500">
            Channels without an official integration are published and removed by hand — this is that work.
          </p>
        </div>
        <button class="btn-primary" :disabled="loadingQueue" @click="loadQueue">
          {{ loadingQueue ? 'Refreshing…' : 'Refresh' }}
        </button>
      </div>

      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th w-32">Action</th>
            <th class="table-th">Item</th>
            <th class="table-th w-48">Channel</th>
            <th class="table-th w-56">External post</th>
            <th class="table-th w-56 text-right">Resolve</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loadingQueue">
            <td colspan="5" class="table-td py-10 text-center text-slate-400">Loading…</td>
          </tr>
          <tr v-else-if="!queue.length">
            <td colspan="5" class="table-td py-10 text-center text-slate-400">
              Nothing waiting — every channel is up to date.
            </td>
          </tr>
          <tr v-for="row in queue" :key="row.id" class="hover:bg-slate-50">
            <td class="table-td">
              <span :class="['rounded-full px-2 py-0.5 text-xs font-semibold', actionClass(row.action)]">
                {{ actionLabel(row.action) }}
              </span>
            </td>
            <td class="table-td">
              <p class="max-w-[280px] truncate text-sm font-medium text-slate-800">{{ row.listing_title }}</p>
              <p v-if="row.last_error" class="mt-0.5 max-w-[280px] truncate text-xs text-rose-500">{{ row.last_error }}</p>
            </td>
            <td class="table-td">
              <p class="text-sm text-slate-700">{{ row.channel_name }}</p>
              <p class="text-xs text-slate-400">{{ row.channel }}</p>
            </td>
            <td class="table-td">
              <a v-if="row.external_url" :href="row.external_url" target="_blank" rel="noopener"
                 class="text-xs text-primary-600 hover:underline">{{ row.external_id || 'open' }} ↗</a>
              <span v-else class="text-xs text-slate-400">{{ row.external_id || '—' }}</span>
            </td>
            <td class="table-td text-right">
              <!-- Posted by hand: record the channel's own post id -->
              <div v-if="row.action === 'post'" class="flex items-center justify-end gap-2">
                <input v-model="refDraft[row.id]" class="input !w-36 !py-1 text-xs" placeholder="their post id" />
                <button class="btn-primary !px-3 !py-1 text-xs" :disabled="busy" @click="recordRef(row)">
                  Mark posted
                </button>
              </div>
              <button v-else-if="row.action === 'take_down'" class="btn-primary !px-3 !py-1 text-xs"
                      :disabled="busy" @click="confirmTakedown(row)">
                Removed it
              </button>
              <button v-else class="btn-secondary !px-3 !py-1 text-xs" :disabled="busy" @click="retry(row)">
                Retry publish
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Channels -->
    <div class="card overflow-hidden">
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-3">
        <div>
          <h2 class="text-sm font-semibold text-slate-900">Channels</h2>
          <p class="mt-0.5 text-xs text-slate-500">One row per platform × region account.</p>
        </div>
        <button class="btn-primary" @click="showCreate = !showCreate">
          {{ showCreate ? 'Cancel' : 'Add channel' }}
        </button>
      </div>

      <div v-if="showCreate" class="border-b border-slate-200 bg-slate-50 p-5">
        <div class="grid grid-cols-4 gap-4">
          <label class="block">
            <span class="mb-1 block text-xs font-semibold text-slate-500">Platform key</span>
            <input v-model="draft.channel" class="input" placeholder="kupujemprodajem" />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-semibold text-slate-500">Display name</span>
            <input v-model="draft.name" class="input" placeholder="KupujemProdajem RS" />
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-semibold text-slate-500">How it publishes</span>
            <select v-model="draft.driver_kind" class="input">
              <option value="assisted">Assisted — a person posts it</option>
              <option value="feed">Merchant feed — the channel pulls</option>
              <option value="api">Official API (needs an agreement)</option>
              <option value="agent">AI agent (reviewed before sending)</option>
            </select>
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-semibold text-slate-500">Feed slug</span>
            <input v-model="draft.feed_slug" class="input" placeholder="olx-rs" :disabled="draft.driver_kind !== 'feed'" />
          </label>
        </div>
        <p class="mt-3 text-xs text-slate-500">
          Most classifieds forbid automated posting. <strong>api</strong> and <strong>agent</strong> stay
          assisted until an integration is registered for that platform, so nothing is ever posted
          automatically by accident.
        </p>
        <div class="mt-4 flex items-center gap-2">
          <button class="btn-primary" :disabled="busy || !draft.channel || !draft.name" @click="createChannel">
            {{ busy ? 'Saving…' : 'Create channel' }}
          </button>
          <span v-if="error" class="text-sm text-rose-600">{{ error }}</span>
        </div>
      </div>

      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Channel</th>
            <th class="table-th w-40">Publishes via</th>
            <th class="table-th w-48">Feed</th>
            <th class="table-th w-28">Status</th>
            <th class="table-th w-40 text-right">Category maps</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!channels.length">
            <td colspan="5" class="table-td py-10 text-center text-slate-400">
              No syndication channels yet.
            </td>
          </tr>
          <tr v-for="c in channels" :key="c.id" class="hover:bg-slate-50">
            <td class="table-td">
              <p class="text-sm font-semibold text-slate-800">{{ c.name }}</p>
              <p class="text-xs text-slate-400">{{ c.channel }}</p>
            </td>
            <td class="table-td">
              <span :class="['rounded-full px-2 py-0.5 text-xs font-medium', driverClass(c.driver_kind)]">
                {{ c.driver_kind }}
              </span>
            </td>
            <td class="table-td">
              <a v-if="c.feed_slug" :href="feedUrl(c.feed_slug)" target="_blank" rel="noopener"
                 class="font-mono text-xs text-primary-600 hover:underline">{{ c.feed_slug }}.xml ↗</a>
              <span v-else class="text-xs text-slate-400">—</span>
            </td>
            <td class="table-td">
              <span :class="['rounded-full px-2 py-0.5 text-xs font-medium',
                             c.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500']">
                {{ c.status }}
              </span>
            </td>
            <td class="table-td text-right">
              <button class="btn-secondary !px-3 !py-1 text-xs" @click="toggleMaps(c)">
                {{ openChannel === c.id ? 'Hide' : 'Manage' }}
              </button>
            </td>
          </tr>
          <tr v-if="openChannel">
            <td colspan="5" class="bg-slate-50 px-5 py-4">
              <p class="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Category mapping — our category to theirs
              </p>
              <div v-if="maps.length" class="mb-3 space-y-1">
                <div v-for="m in maps" :key="m.id" class="flex items-center gap-3 rounded-lg bg-white px-3 py-2 text-sm">
                  <span class="font-medium text-slate-800">{{ m.category_name }}</span>
                  <span class="text-slate-300">→</span>
                  <span class="font-mono text-xs text-slate-600">{{ m.external_category_code }}</span>
                  <span v-if="m.external_category_path" class="text-xs text-slate-400">{{ m.external_category_path }}</span>
                </div>
              </div>
              <p v-else class="mb-3 text-sm text-slate-400">No mapping yet — listings publish without a category.</p>

              <div class="grid grid-cols-4 gap-3">
                <select v-model="mapDraft.category_schema_id" class="input">
                  <option value="">Our category…</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
                </select>
                <input v-model="mapDraft.external_category_code" class="input" placeholder="their code e.g. 1234" />
                <input v-model="mapDraft.external_category_path" class="input" placeholder="their path (optional)" />
                <button class="btn-primary" :disabled="busy || !mapDraft.category_schema_id || !mapDraft.external_category_code"
                        @click="saveMap">Save mapping</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '@/utils/api'

const queue = ref([])
const channels = ref([])
const categories = ref([])
const maps = ref([])
const openChannel = ref(null)
const refDraft = reactive({})
const loadingQueue = ref(true)
const busy = ref(false)
const showCreate = ref(false)
const error = ref('')

const draft = reactive({ channel: '', name: '', driver_kind: 'assisted', feed_slug: '' })
const mapDraft = reactive({ category_schema_id: '', external_category_code: '', external_category_path: '' })

const counts = computed(() => ({
  post: queue.value.filter((r) => r.action === 'post').length,
  take_down: queue.value.filter((r) => r.action === 'take_down').length,
  retry: queue.value.filter((r) => r.action === 'retry').length,
}))
const activeChannels = computed(() => channels.value.filter((c) => c.status === 'active').length)

function actionLabel(a) {
  return { post: 'Publish', take_down: 'Take down', retry: 'Failed' }[a] || a
}
function actionClass(a) {
  return {
    post: 'bg-amber-100 text-amber-700',
    take_down: 'bg-rose-100 text-rose-700',
    retry: 'bg-slate-200 text-slate-600',
  }[a] || 'bg-slate-100 text-slate-500'
}
function driverClass(k) {
  return {
    feed: 'bg-sky-100 text-sky-700',
    assisted: 'bg-violet-100 text-violet-700',
    api: 'bg-green-100 text-green-700',
    agent: 'bg-indigo-100 text-indigo-700',
  }[k] || 'bg-slate-100 text-slate-500'
}
function feedUrl(slug) {
  return `/api/syndication/feed/${slug}.xml`
}

async function loadQueue() {
  loadingQueue.value = true
  try {
    const { data } = await api.get('/syndication/queue')
    queue.value = data.items || []
  } catch {
    queue.value = []
  } finally {
    loadingQueue.value = false
  }
}

async function loadChannels() {
  const { data } = await api.get('/syndication/channels').catch(() => ({ data: { items: [] } }))
  channels.value = data.items || []
}

async function loadCategories() {
  const { data } = await api.get('/categories').catch(() => ({ data: [] }))
  categories.value = Array.isArray(data) ? data : data.items || []
}

async function act(fn) {
  busy.value = true
  error.value = ''
  try {
    await fn()
    await Promise.all([loadQueue(), loadChannels()])
  } catch (e) {
    error.value = e.response?.data?.detail || 'Action failed'
  } finally {
    busy.value = false
  }
}

const createChannel = () =>
  act(async () => {
    await api.post('/syndication/channels', {
      channel: draft.channel.trim().toLowerCase(),
      name: draft.name.trim(),
      driver_kind: draft.driver_kind,
      feed_slug: draft.driver_kind === 'feed' ? draft.feed_slug || null : null,
    })
    Object.assign(draft, { channel: '', name: '', driver_kind: 'assisted', feed_slug: '' })
    showCreate.value = false
  })

const recordRef = (row) =>
  act(() =>
    api.post(`/syndication/channel-listings/${row.id}/external-ref`, {
      external_id: refDraft[row.id] || null,
      mark_published: true,
    })
  )

const confirmTakedown = (row) =>
  act(() => api.post(`/syndication/channel-listings/${row.id}/confirm-takedown`))

const retry = (row) =>
  act(() => api.post(`/syndication/listings/${row.listing_id}/publish`, { account_ids: [row.account_id], force: true }))

async function toggleMaps(channel) {
  if (openChannel.value === channel.id) {
    openChannel.value = null
    return
  }
  openChannel.value = channel.id
  const { data } = await api.get(`/syndication/channels/${channel.id}/category-maps`).catch(() => ({ data: { items: [] } }))
  maps.value = data.items || []
}

const saveMap = () =>
  act(async () => {
    await api.put(`/syndication/channels/${openChannel.value}/category-maps`, {
      category_schema_id: mapDraft.category_schema_id,
      external_category_code: mapDraft.external_category_code,
      external_category_path: mapDraft.external_category_path || null,
    })
    const id = openChannel.value
    openChannel.value = null
    Object.assign(mapDraft, { category_schema_id: '', external_category_code: '', external_category_path: '' })
    await toggleMaps({ id })
  })

onMounted(async () => {
  await Promise.all([loadQueue(), loadChannels(), loadCategories()])
})
</script>
