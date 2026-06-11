<template>
  <div class="space-y-6">
    <!-- Tabs -->
    <div class="flex gap-2 border-b border-slate-200">
      <button v-for="t in tabs" :key="t.key" class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        :class="tab===t.key ? 'border-primary-600 text-primary-700' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="tab=t.key; load()">{{ t.label }}</button>
    </div>

    <!-- Payment Events -->
    <div v-if="tab==='events'" class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">{{ t('orders.order') }}</th>
          <th class="table-th">{{ t('payments.type') }}</th>
          <th class="table-th">{{ t('orders.amount') }}</th>
          <th class="table-th">{{ t('payments.provider') }}</th>
          <th class="table-th">{{ t('common.status') }}</th>
          <th class="table-th">{{ t('common.date') }}</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
          <tr v-else-if="!items.length"><td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('payments.noEvents') }}</td></tr>
          <tr v-for="e in items" :key="e.id" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs">{{ e.order_id?.slice(0,8) }}</td>
            <td class="table-td"><span class="badge badge-blue">{{ e.event_type }}</span></td>
            <td class="table-td font-medium">{{ fmtPrice(e.amount_minor, e.currency) }}</td>
            <td class="table-td text-xs text-slate-500">{{ e.provider || '—' }}</td>
            <td class="table-td"><span :class="evtBadge(e.status)" class="badge">{{ e.status }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDatetime(e.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Payouts -->
    <div v-if="tab==='payouts'" class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">{{ t('orders.supplier') }}</th>
          <th class="table-th">{{ t('orders.order') }}</th>
          <th class="table-th">{{ t('orders.amount') }}</th>
          <th class="table-th">{{ t('payments.method') }}</th>
          <th class="table-th">{{ t('common.status') }}</th>
          <th class="table-th">{{ t('common.date') }}</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
          <tr v-else-if="!items.length"><td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('payments.noPayouts') }}</td></tr>
          <tr v-for="p in items" :key="p.id" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs">{{ p.supplier_id?.slice(0,8) || '—' }}</td>
            <td class="table-td font-mono text-xs">{{ p.order_id?.slice(0,8) || '—' }}</td>
            <td class="table-td font-medium">{{ fmtPrice(p.amount_minor, p.currency) }}</td>
            <td class="table-td text-xs">{{ p.method || '—' }}</td>
            <td class="table-td"><span :class="payoutBadge(p.status)" class="badge">{{ p.status }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDatetime(p.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Deposit Review -->
    <div v-if="tab==='deposits'" class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">User</th>
          <th class="table-th">Amount</th>
          <th class="table-th">Network</th>
          <th class="table-th">TX Hash</th>
          <th class="table-th">{{ t('common.status') }}</th>
          <th class="table-th">{{ t('common.date') }}</th>
          <th class="table-th text-right">Action</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="7" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
          <tr v-else-if="!items.length"><td colspan="7" class="table-td text-center py-10 text-slate-400">No deposit records</td></tr>
          <tr v-for="d in items" :key="d.id" class="hover:bg-slate-50">
            <td class="table-td font-mono text-xs">{{ d.owner_user_id?.slice(0,8) }}</td>
            <td class="table-td font-medium">{{ fmtPrice(d.amount_minor, d.currency) }}</td>
            <td class="table-td text-xs">{{ d.network }}</td>
            <td class="table-td font-mono text-xs max-w-48 truncate">{{ d.tx_hash || '—' }}</td>
            <td class="table-td"><span :class="depositBadge(d.status)" class="badge">{{ d.status }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDatetime(d.created_at) }}</td>
            <td class="table-td">
              <div class="flex justify-end gap-2">
                <button
                  class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-green-50 text-green-700 hover:bg-green-100 disabled:opacity-50"
                  :disabled="actingId===d.id || !canDecide(d.status)"
                  @click="decideDeposit(d.id, 'verify')"
                >
                  Verify
                </button>
                <button
                  class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-50 text-red-700 hover:bg-red-100 disabled:opacity-50"
                  :disabled="actingId===d.id || !canDecide(d.status)"
                  @click="decideDeposit(d.id, 'reject')"
                >
                  Reject
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Settlement Events -->
    <div v-if="tab==='settlements'" class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">Provider</th>
          <th class="table-th">Reference</th>
          <th class="table-th">Gross</th>
          <th class="table-th">Fees</th>
          <th class="table-th">Net</th>
          <th class="table-th">{{ t('common.status') }}</th>
          <th class="table-th">{{ t('common.date') }}</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="7" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
          <tr v-else-if="!items.length"><td colspan="7" class="table-td text-center py-10 text-slate-400">No settlement events</td></tr>
          <tr v-for="s in items" :key="s.id" class="hover:bg-slate-50">
            <td class="table-td text-xs">{{ s.provider }}</td>
            <td class="table-td font-mono text-xs">{{ s.provider_reference || '—' }}</td>
            <td class="table-td font-medium">{{ fmtPrice(s.gross_amount_minor, s.currency) }}</td>
            <td class="table-td">{{ fmtPrice(s.fee_amount_minor, s.currency) }}</td>
            <td class="table-td font-medium">{{ fmtPrice(s.net_amount_minor, s.currency) }}</td>
            <td class="table-td"><span class="badge badge-blue">{{ s.status }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDatetime(s.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Region Payment Configs -->
    <div v-if="tab==='regions'" class="space-y-4">
      <div class="card overflow-hidden">
        <table class="w-full">
          <thead><tr>
            <th class="table-th">Country</th>
            <th class="table-th">Local</th>
            <th class="table-th">Enabled Currencies</th>
            <th class="table-th">Cross-border</th>
            <th class="table-th">Mode</th>
            <th class="table-th">USD Bridge</th>
            <th class="table-th">{{ t('common.status') }}</th>
            <th class="table-th text-right">Action</th>
          </tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
            <tr v-else-if="!items.length"><td colspan="8" class="table-td text-center py-10 text-slate-400">No region configs</td></tr>
            <tr v-for="r in items" :key="r.id" class="hover:bg-slate-50">
              <td class="table-td font-medium">{{ r.country_code }} · {{ r.country_name }}</td>
              <td class="table-td font-semibold">{{ r.local_currency }}</td>
              <td class="table-td text-xs">{{ (r.enabled_currencies || []).join(', ') }}</td>
              <td class="table-td text-xs">{{ (r.cross_border_currencies || []).join(', ') }}</td>
              <td class="table-td text-xs">{{ r.default_transaction_mode }}</td>
              <td class="table-td">{{ r.force_usd_bridge ? 'Yes' : 'No' }}</td>
              <td class="table-td"><span :class="r.is_active ? 'badge-green' : 'badge-gray'" class="badge">{{ r.is_active ? 'ACTIVE' : 'OFF' }}</span></td>
              <td class="table-td text-right">
                <button class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200" @click="toggleRegion(r)">
                  {{ r.is_active ? 'Disable' : 'Enable' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-xs text-slate-500">
        Default operation: each country only exposes its local currency. Cross-border modes and USD bridge can be enabled per region without changing buyer checkout code.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, fmtPrice, fmtDatetime } from '@/utils/api'

const { t } = useI18n()
const tabs = computed(() => [
  { key:'events', label: t('payments.events') },
  { key:'payouts', label: t('payments.payouts') },
  { key:'deposits', label: 'Deposits' },
  { key:'settlements', label: 'Settlements' },
  { key:'regions', label: 'Region Configs' },
])
const tab = ref('events')
const loading = ref(true)
const items = ref([])
const actingId = ref(null)

function evtBadge(s) {
  return { SUCCESS:'badge-green', PENDING:'badge-amber', FAILED:'badge-red' }[s] || 'badge-gray'
}
function payoutBadge(s) {
  return { COMPLETED:'badge-green', PENDING:'badge-amber', PROCESSING:'badge-blue', FAILED:'badge-red' }[s] || 'badge-gray'
}
function depositBadge(s) {
  return { VERIFIED:'badge-green', UNDER_REVIEW:'badge-blue', PENDING_TX:'badge-amber', REJECTED:'badge-red', EXPIRED:'badge-gray' }[s] || 'badge-gray'
}
function canDecide(s) {
  return ['UNDER_REVIEW', 'PENDING_TX'].includes(s)
}

async function load() {
  loading.value = true
  try {
    const url = tab.value === 'events'
      ? '/admin/payment-events'
      : tab.value === 'payouts'
        ? '/admin/payouts'
        : tab.value === 'deposits'
          ? '/admin/deposits'
          : tab.value === 'settlements'
            ? '/admin/settlement-events'
            : '/admin/payment-region-configs'
    items.value = await api.get(url).then(r => r.data)
  } catch { items.value = [] }
  loading.value = false
}

async function toggleRegion(region) {
  actingId.value = region.id
  try {
    await api.patch(`/admin/payment-region-configs/${region.id}`, { is_active: !region.is_active })
    await load()
  } finally {
    actingId.value = null
  }
}

async function decideDeposit(id, action) {
  actingId.value = id
  try {
    await api.post(`/admin/deposits/${id}/${action}`, {
      admin_note: action === 'verify' ? 'Verified from admin payment console' : 'Rejected from admin payment console',
    })
    await load()
  } finally {
    actingId.value = null
  }
}

onMounted(load)
</script>
