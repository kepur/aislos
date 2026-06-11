<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white">{{ $t('admin.leads') }}</h1>
        <p class="text-sm text-slate-400 mt-1">{{ total }} total leads</p>
      </div>
    </div>

    <!-- Table -->
    <div class="admin-card p-0 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-white/5 bg-white/[0.02]">
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Contact</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Type</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Country</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Budget</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{{ $t('common.status') }}</th>
              <th class="text-left py-3 px-4 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Date</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in leads" :key="lead.id"
                class="border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-colors"
                @click="navigateTo(`/admin/leads/${lead.id}`)">
              <td class="px-4 py-3">
                <span class="text-slate-200 font-medium">{{ lead.contact_name || '-' }}</span>
                <span v-if="lead.contact_email" class="block text-xs text-slate-500">{{ lead.contact_email }}</span>
              </td>
              <td class="px-4 py-3 text-slate-400">{{ lead.project_type || '-' }}</td>
              <td class="px-4 py-3 text-slate-400">{{ lead.country || '-' }}</td>
              <td class="px-4 py-3 text-slate-400">{{ lead.budget_range || '-' }}</td>
              <td class="px-4 py-3"><StatusBadge :status="lead.status" /></td>
              <td class="px-4 py-3 text-slate-500 text-xs">{{ new Date(lead.created_at).toLocaleDateString() }}</td>
            </tr>
            <tr v-if="!leads.length">
              <td colspan="6" class="px-4 py-12 text-center text-slate-500">{{ $t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const { apiFetch } = useApi()
const leads = ref<any[]>([])
const total = ref(0)

onMounted(async () => {
  try {
    const res = await apiFetch<any>('/leads')
    leads.value = res.items || res || []
    total.value = res.total || leads.value.length
  } catch {}
})
</script>
