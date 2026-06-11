<template>
  <div>
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
      <div>
        <h1 class="admin-page-title">Payment Plans</h1>
        <p class="admin-page-desc">Milestone bookkeeping (offline transfers). Mark funded when money arrives; retention auto-releases.</p>
      </div>
      <div class="flex gap-2">
        <input v-model="quoteId" placeholder="Quote ID" class="input-field max-w-72" />
        <input v-model.number="retentionPct" type="number" placeholder="Retention %" class="input-field max-w-28" />
        <button class="btn-primary text-sm px-4 py-2" :disabled="busy || !quoteId" @click="createPlan">Create plan</button>
      </div>
    </div>

    <div class="admin-panel mb-6">
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Plan</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Total</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Retention</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500">Status</th>
            <th class="text-left px-4 py-3 font-medium text-gray-500"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="plan in plans" :key="plan.id" class="border-b">
            <td class="px-4 py-3 font-mono text-xs text-gray-600">{{ plan.id.slice(0, 8) }}</td>
            <td class="px-4 py-3 font-medium">{{ plan.total }} {{ plan.currency }}</td>
            <td class="px-4 py-3 text-gray-600">{{ plan.retention_pct ?? '-' }}%</td>
            <td class="px-4 py-3"><StatusBadge :status="plan.status" /></td>
            <td class="px-4 py-3">
              <button class="text-xs text-primary-600 hover:underline" @click="open(plan.id)">Milestones</button>
            </td>
          </tr>
          <tr v-if="!plans.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-500">No payment plans yet.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="detail" class="admin-panel p-4">
      <h2 class="font-medium text-gray-900 mb-3">Milestones — plan {{ detail.id.slice(0, 8) }}</h2>
      <table class="admin-table w-full text-sm">
        <thead>
          <tr>
            <th class="text-left px-3 py-2 font-medium text-gray-500">#</th>
            <th class="text-left px-3 py-2 font-medium text-gray-500">Label</th>
            <th class="text-left px-3 py-2 font-medium text-gray-500">Amount</th>
            <th class="text-left px-3 py-2 font-medium text-gray-500">Status</th>
            <th class="text-left px-3 py-2 font-medium text-gray-500">Release due</th>
            <th class="text-left px-3 py-2 font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in detail.milestones" :key="m.id" class="border-b">
            <td class="px-3 py-2">{{ m.seq }}</td>
            <td class="px-3 py-2 font-medium">{{ m.label }} ({{ m.pct }}%)</td>
            <td class="px-3 py-2">{{ m.amount }} {{ detail.currency }}</td>
            <td class="px-3 py-2"><StatusBadge :status="m.status" /></td>
            <td class="px-3 py-2 text-gray-500">{{ m.release_due_at ? new Date(m.release_due_at).toLocaleDateString() : '-' }}</td>
            <td class="px-3 py-2">
              <div class="flex gap-2">
                <button v-if="['pending','invoiced'].includes(m.status)" class="btn-primary text-xs px-3 py-1" :disabled="busy" @click="fund(m)">Mark funded</button>
                <button v-if="m.status === 'funded'" class="text-xs px-3 py-1 rounded border border-gray-300 hover:bg-gray-50" :disabled="busy" @click="release(m)">Release</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <h3 class="font-medium text-gray-900 mt-4 mb-2 text-sm">Ledger</h3>
      <div class="text-xs text-gray-600 space-y-1 font-mono">
        <p v-for="(e, i) in detail.ledger" :key="i">
          {{ e.direction === 'debit' ? 'DR' : 'CR' }} {{ e.account }} — {{ e.amount }} {{ e.currency }} · {{ e.memo }}
        </p>
        <p v-if="!detail.ledger?.length" class="text-gray-400">No ledger entries yet.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { apiFetch } = useApi()
const plans = ref<any[]>([])
const detail = ref<any>(null)
const quoteId = ref('')
const retentionPct = ref<number | null>(null)
const busy = ref(false)

async function load() {
  const res = await apiFetch<any>('/admin/payments/plans')
  plans.value = res.items || []
}

async function open(id: string) {
  detail.value = await apiFetch<any>(`/admin/payments/plans/${id}`)
}

async function createPlan() {
  busy.value = true
  try {
    const plan = await apiFetch<any>('/admin/payments/plans', {
      method: 'POST',
      body: { quote_id: quoteId.value, retention_pct: retentionPct.value },
    })
    quoteId.value = ''
    await load()
    await open(plan.id)
  } finally {
    busy.value = false
  }
}

async function fund(m: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/payments/milestones/${m.id}/fund`, { method: 'POST', body: {} })
    await open(detail.value.id)
    await load()
  } finally {
    busy.value = false
  }
}

async function release(m: any) {
  busy.value = true
  try {
    await apiFetch(`/admin/payments/milestones/${m.id}/release`, { method: 'POST', body: {} })
    await open(detail.value.id)
    await load()
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
