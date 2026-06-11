<template>
  <div class="space-y-6">
    <!-- Filters -->
    <div class="card p-4 flex flex-wrap items-center gap-3">
      <input
        v-model="search"
        @keyup.enter="load(true)"
        type="text"
        placeholder="Search products..."
        class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm outline-none focus:border-indigo-400 w-56"
      />
      <select v-model="marketMode" @change="load(true)" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white">
        <option value="">All modes</option>
        <option value="B2B">B2B</option>
        <option value="B2C">B2C</option>
        <option value="BOTH">BOTH</option>
      </select>
      <select v-model="statusFilter" @change="load(true)" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white">
        <option value="">All statuses</option>
        <option value="ACTIVE">Active</option>
        <option value="INACTIVE">Inactive</option>
        <option value="PENDING_REVIEW">Pending Review</option>
        <option value="REJECTED">Rejected</option>
      </select>
      <select v-model="categoryFilter" @change="load(true)" class="border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white">
        <option value="">All categories</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
      </select>
      <button @click="load(true)" class="btn-primary text-sm">Search</button>
      <span class="text-xs text-slate-400 ml-auto">{{ total }} items total</span>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Product</th>
            <th class="table-th">Company</th>
            <th class="table-th">Category</th>
            <th class="table-th">Mode</th>
            <th class="table-th">Price</th>
            <th class="table-th">Stock</th>
            <th class="table-th">Status</th>
            <th class="table-th">Stats</th>
            <th class="table-th text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="table-td text-center py-10 text-slate-400">Loading...</td>
          </tr>
          <tr v-else-if="!items.length">
            <td colspan="9" class="table-td text-center py-10 text-slate-400">No products found</td>
          </tr>
          <tr v-for="item in items" :key="item.id" class="hover:bg-slate-50">
            <td class="table-td">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg overflow-hidden flex-shrink-0 bg-slate-100">
                  <img v-if="item.images?.[0]" :src="item.images[0]" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full flex items-center justify-center text-lg">📦</div>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-slate-800 truncate max-w-[180px]">{{ item.title }}</p>
                  <p class="text-xs text-slate-400">{{ item.origin_country ?? '—' }}</p>
                </div>
              </div>
            </td>
            <td class="table-td">
              <span class="text-sm text-slate-600">{{ item.company_name ?? '—' }}</span>
            </td>
            <td class="table-td">
              <span class="text-xs text-slate-500">{{ item.category_name ?? '—' }}</span>
            </td>
            <td class="table-td">
              <span :class="['badge text-xs', item.market_mode === 'B2C' ? 'badge-green' : item.market_mode === 'B2B' ? 'badge-blue' : 'badge-gray']">
                {{ item.market_mode }}
              </span>
            </td>
            <td class="table-td">
              <span class="text-sm font-semibold text-slate-800">{{ formatPrice(item.price_minor, item.currency) }}</span>
              <span class="text-xs text-slate-400">/{{ item.unit }}</span>
            </td>
            <td class="table-td">
              <span :class="item.stock_qty > 0 ? 'text-green-600 text-sm' : 'text-red-500 text-sm'">
                {{ item.stock_qty.toLocaleString() }}
              </span>
            </td>
            <td class="table-td">
              <span :class="['badge text-xs', statusClass(item.status)]">{{ item.status }}</span>
            </td>
            <td class="table-td">
              <div class="text-xs text-slate-400 space-y-0.5">
                <div>👁 {{ item.view_count.toLocaleString() }}</div>
                <div>📦 {{ item.order_count }} orders</div>
              </div>
            </td>
            <td class="table-td">
              <div class="flex justify-end gap-2">
                <button
                  v-if="item.status !== 'ACTIVE'"
                  @click="setStatus(item, 'ACTIVE')"
                  class="btn-secondary text-xs text-green-600"
                >Activate</button>
                <button
                  v-if="item.status === 'ACTIVE'"
                  @click="setStatus(item, 'INACTIVE')"
                  class="btn-secondary text-xs"
                >Disable</button>
                <button
                  v-if="item.status !== 'REJECTED'"
                  @click="rejectItem(item)"
                  class="btn-secondary text-xs text-red-600"
                >Reject</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
        <button :disabled="page === 1" @click="page--; load()" class="btn-secondary text-xs disabled:opacity-40">← Prev</button>
        <span class="text-xs text-slate-500">Page {{ page }} of {{ Math.ceil(total / pageSize) }}</span>
        <button :disabled="!hasNext" @click="page++; load()" class="btn-secondary text-xs disabled:opacity-40">Next →</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const API = import.meta.env.VITE_API_BASE

const items = ref([])
const categories = ref([])
const total = ref(0)
const loading = ref(false)
const hasNext = ref(false)
const page = ref(1)
const pageSize = 20

const search = ref('')
const marketMode = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')

onMounted(async () => {
  try {
    const f = await fetch(`${API}/marketplace/filters`, { headers: authHeaders() })
    const data = await f.json()
    categories.value = data.categories ?? []
  } catch {}
  await load(true)
})

async function load(reset = false) {
  if (reset) page.value = 1
  loading.value = true
  try {
    const params = new URLSearchParams({ page: page.value, page_size: pageSize })
    if (search.value.trim()) params.set('keyword', search.value.trim())
    if (marketMode.value) params.set('market_mode', marketMode.value)
    if (categoryFilter.value) params.set('category_id', categoryFilter.value)

    // Use feed endpoint — admin can see all via feed; status not exposed in public feed
    // For admin we use the feed (public) as the primary view, since admin catalog endpoint may differ
    const r = await fetch(`${API}/marketplace/feed?${params}&sort=newest`, { headers: authHeaders() })
    const data = await r.json()
    items.value = data.items ?? []
    total.value = data.total ?? 0
    hasNext.value = data.has_next ?? false
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function setStatus(item, newStatus) {
  try {
    // Use merchant catalog update — we need company context; for admin use a direct approach
    const r = await fetch(`${API}/merchant/catalog/${item.id}`, {
      method: 'PATCH',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
    if (r.ok) {
      item.status = newStatus
    } else {
      const err = await r.json()
      alert(err.detail ?? 'Failed to update status')
    }
  } catch (e) {
    alert('Network error')
  }
}

async function rejectItem(item) {
  if (!confirm(`Reject "${item.title}"? It will be removed from the marketplace.`)) return
  await setStatus(item, 'REJECTED')
}

function authHeaders() {
  return { Authorization: `Bearer ${auth.token}` }
}

function formatPrice(minor, currency) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(minor / 100)
}

function statusClass(status) {
  const map = {
    ACTIVE: 'badge-green',
    INACTIVE: 'badge-gray',
    PENDING_REVIEW: 'badge-amber',
    REJECTED: 'badge-red',
  }
  return map[status] ?? 'badge-gray'
}
</script>
