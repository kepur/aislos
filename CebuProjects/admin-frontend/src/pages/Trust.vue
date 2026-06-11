<template>
  <div class="space-y-4">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
      <div class="card p-4">
        <p class="text-xs font-semibold text-slate-500 uppercase">Profiles</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ profiles.length }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs font-semibold text-slate-500 uppercase">Avg Score</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ avgScore }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs font-semibold text-slate-500 uppercase">Gold+</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ goldPlus }}</p>
      </div>
      <div class="card p-4">
        <p class="text-xs font-semibold text-slate-500 uppercase">Frozen</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ frozen }}</p>
      </div>
    </div>

    <div class="flex items-center gap-3 flex-wrap">
      <input v-model="search" type="search" placeholder="Search entity id or tier..." class="input max-w-xs" />
      <select v-model="tierFilter" class="input w-40">
        <option value="">All tiers</option>
        <option value="BRONZE">Bronze</option>
        <option value="SILVER">Silver</option>
        <option value="GOLD">Gold</option>
        <option value="PLATINUM">Platinum</option>
        <option value="DIAMOND">Diamond</option>
      </select>
      <button class="btn-secondary ml-auto" :disabled="loading" @click="load">Refresh</button>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead>
          <tr>
            <th class="table-th">Entity</th>
            <th class="table-th">Score</th>
            <th class="table-th">Tier</th>
            <th class="table-th">Completion</th>
            <th class="table-th">Deals</th>
            <th class="table-th">Deposit</th>
            <th class="table-th">Risk</th>
            <th class="table-th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="8" class="table-td text-center py-10 text-slate-400">Loading...</td></tr>
          <tr v-else-if="!filtered.length"><td colspan="8" class="table-td text-center py-10 text-slate-400">No trust profiles found</td></tr>
          <tr v-for="p in filtered" :key="p.id" class="hover:bg-slate-50">
            <td class="table-td">
              <p class="font-mono text-xs text-slate-700">{{ p.entity_id.slice(0, 8).toUpperCase() }}</p>
              <p class="text-xs text-slate-400">{{ p.entity_type }}</p>
            </td>
            <td class="table-td">
              <div class="font-bold text-slate-900">{{ p.trust_score }}</div>
              <div class="h-1.5 w-24 bg-slate-100 rounded-full mt-1 overflow-hidden">
                <div class="h-full bg-primary-600" :style="{ width: `${Math.min(p.trust_score / 10, 100)}%` }"></div>
              </div>
            </td>
            <td class="table-td"><span :class="tierBadge(p.trust_tier)" class="badge">{{ tierLabel(p.trust_tier) }}</span></td>
            <td class="table-td">{{ p.profile_completion_rate }}%</td>
            <td class="table-td">
              <p>{{ p.deal_completion_rate }}% completion</p>
              <p class="text-xs text-slate-400">{{ p.successful_deals_count }} success / {{ p.canceled_deals_count }} canceled</p>
            </td>
            <td class="table-td">{{ fmtPrice(p.deposit_amount_minor, p.deposit_currency) }}</td>
            <td class="table-td">
              <p class="text-xs">Dispute {{ p.dispute_rate }}%</p>
              <p class="text-xs">Refund {{ p.refund_rate }}%</p>
            </td>
            <td class="table-td">
              <div class="flex gap-2">
                <button class="btn-secondary py-1 px-3 text-xs" @click="recalculate(p)">Recalc</button>
                <button class="btn-secondary py-1 px-3 text-xs" @click="adjust(p)">Adjust</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, fmtPrice } from '@/utils/api'

const loading = ref(true)
const profiles = ref([])
const search = ref('')
const tierFilter = ref('')

const filtered = computed(() => profiles.value.filter(p => {
  const q = search.value.toLowerCase()
  return (!q || p.entity_id.toLowerCase().includes(q) || p.trust_tier.toLowerCase().includes(q))
    && (!tierFilter.value || p.trust_tier === tierFilter.value)
}))

const avgScore = computed(() => {
  if (!profiles.value.length) return 0
  return Math.round(profiles.value.reduce((sum, p) => sum + p.trust_score, 0) / profiles.value.length)
})
const goldPlus = computed(() => profiles.value.filter(p => ['GOLD', 'PLATINUM', 'DIAMOND'].includes(p.trust_tier)).length)
const frozen = computed(() => profiles.value.filter(p => p.status === 'FROZEN').length)

function tierLabel(tier) {
  return {
    BRONZE: '青铜',
    SILVER: '白银',
    GOLD: '黄金',
    PLATINUM: '铂金',
    DIAMOND: '钻石',
  }[tier] || tier
}

function tierBadge(tier) {
  return {
    BRONZE: 'badge-amber',
    SILVER: 'badge-gray',
    GOLD: 'badge-amber',
    PLATINUM: 'badge-blue',
    DIAMOND: 'badge-green',
  }[tier] || 'badge-gray'
}

async function load() {
  loading.value = true
  try {
    profiles.value = await api.get('/admin/trust/users').then(r => r.data)
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to load trust profiles')
    profiles.value = []
  } finally {
    loading.value = false
  }
}

async function recalculate(profile) {
  try {
    const { data } = await api.post(`/admin/trust/users/${profile.entity_id}/recalculate`)
    replaceProfile(data)
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to recalculate')
  }
}

async function adjust(profile) {
  const raw = window.prompt('Score delta (-1000 to 1000)', '0')
  if (raw === null) return
  const scoreDelta = Number(raw)
  if (!Number.isFinite(scoreDelta)) return alert('Invalid score delta')
  const reason = window.prompt('Reason for adjustment')
  if (!reason) return
  try {
    const { data } = await api.post(`/admin/trust/${profile.entity_type}/${profile.entity_id}/adjust`, {
      score_delta: scoreDelta,
      reason,
    })
    replaceProfile(data)
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to adjust trust score')
  }
}

function replaceProfile(profile) {
  const idx = profiles.value.findIndex(p => p.id === profile.id)
  if (idx >= 0) profiles.value[idx] = profile
  else profiles.value.unshift(profile)
}

onMounted(load)
</script>
