<template>
  <div class="space-y-4">
    <div class="flex items-center gap-3 flex-wrap">
      <select v-model="statusFilter" class="input w-36" @change="load">
        <option value="">{{ t('common.allStatus') }}</option>
        <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
      </select>
      <span class="ml-auto text-sm text-slate-500">{{ intents.length }} {{ t('intents.requests') }}</span>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead><tr>
          <th class="table-th">{{ t('intents.tableTitle') }}</th>
          <th class="table-th">{{ t('intents.qty') }}</th>
          <th class="table-th">{{ t('intents.budget') }}</th>
          <th class="table-th">{{ t('common.status') }}</th>
          <th class="table-th">{{ t('common.created') }}</th>
          <th class="table-th">{{ t('common.actions') }}</th>
        </tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
          <tr v-else-if="!intents.length"><td colspan="6" class="table-td text-center py-10 text-slate-400">{{ t('common.noData') }}</td></tr>
          <tr v-for="i in intents" :key="i.id" class="hover:bg-slate-50">
            <td class="table-td"><p class="font-medium text-slate-900 truncate max-w-xs">{{ i.title }}</p><p class="text-xs text-slate-400 font-mono">{{ i.id?.slice(0,8) }}</p></td>
            <td class="table-td">{{ i.qty }} {{ i.unit }}</td>
            <td class="table-td">{{ i.budget_max_minor ? fmtPrice(i.budget_max_minor, i.currency) : '—' }}</td>
            <td class="table-td"><span :class="intentBadge(i.status)" class="badge">{{ statusLabel(i.status) }}</span></td>
            <td class="table-td text-xs text-slate-400">{{ fmtDate(i.created_at) }}</td>
            <td class="table-td">
              <div class="flex gap-1">
                <button v-if="i.status==='ACTIVE'" class="btn btn-danger py-1 px-2 text-xs" @click="moderate(i.id, 'cancel')">{{ t('common.cancel') }}</button>
                <button v-if="i.status==='ACTIVE'" class="btn badge-amber py-1 px-2 text-xs" @click="moderate(i.id, 'flag')">{{ t('intents.flag') }}</button>
                <button v-if="i.status==='CANCELED'" class="btn btn-success py-1 px-2 text-xs" @click="moderate(i.id, 'restore')">{{ t('intents.restore') }}</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, fmtDate, fmtPrice } from '@/utils/api'

const { t } = useI18n()
const loading = ref(true)
const intents = ref([])
const statusFilter = ref('')

function intentBadge(s) {
  return { ACTIVE:'badge-blue', AWARDED:'badge-green', CLOSED:'badge-gray', CANCELED:'badge-red', EXPIRED:'badge-amber', DRAFT:'badge-gray' }[s] || 'badge-gray'
}

async function load() {
  loading.value = true
  const p = statusFilter.value ? `?status=${statusFilter.value}` : ''
  intents.value = await api.get(`/admin/intents${p}`).then(r => r.data)
  loading.value = false
}

async function moderate(id, action) {
  try {
    await api.post(`/admin/intents/${id}/moderate`, { action, reason: `Admin ${action}` })
    await load()
  } catch (e) { alert(e.response?.data?.detail || t('common.failed')) }
}

const statuses = ['ACTIVE', 'AWARDED', 'CLOSED', 'CANCELED', 'EXPIRED']

function statusLabel(status) {
  return t(`status.${status}`)
}

onMounted(load)
</script>
