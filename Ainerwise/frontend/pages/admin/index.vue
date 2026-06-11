<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-white">{{ $t('admin.dashboard') }}</h1>
      <p class="text-sm text-slate-400 mt-1">Real-time overview of your smart building platform</p>
    </div>

    <!-- Stats row -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      <div v-for="stat in statCards" :key="stat.label" class="admin-card group">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-medium text-slate-500 uppercase tracking-wider">{{ stat.label }}</span>
          <div :class="['w-8 h-8 rounded-lg flex items-center justify-center', stat.bg]">
            <span class="text-lg">{{ stat.emoji }}</span>
          </div>
        </div>
        <p class="text-2xl font-bold text-white">{{ stat.value }}</p>
        <p class="text-xs text-slate-500 mt-1">{{ stat.sub }}</p>
      </div>
    </div>

    <!-- Main content grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Recent Leads — 2 cols -->
      <div class="lg:col-span-2 admin-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-white">Recent Leads</h2>
          <NuxtLink to="/admin/leads" class="text-xs text-cyan-400 hover:text-cyan-300 transition">View All →</NuxtLink>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-white/5">
                <th class="text-left py-2 px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Contact</th>
                <th class="text-left py-2 px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th class="text-left py-2 px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Country</th>
                <th class="text-left py-2 px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                <th class="text-left py-2 px-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lead in recentLeads" :key="lead.id"
                  class="border-b border-white/[0.03] hover:bg-white/[0.02] cursor-pointer transition-colors"
                  @click="navigateTo(`/admin/leads/${lead.id}`)">
                <td class="py-2.5 px-3 text-slate-300">{{ lead.contact_name || lead.contact_email || '-' }}</td>
                <td class="py-2.5 px-3 text-slate-400">{{ lead.project_type || '-' }}</td>
                <td class="py-2.5 px-3 text-slate-400">{{ lead.country || '-' }}</td>
                <td class="py-2.5 px-3"><StatusBadge :status="lead.status" /></td>
                <td class="py-2.5 px-3 text-slate-500 text-xs">{{ formatDate(lead.created_at) }}</td>
              </tr>
              <tr v-if="!recentLeads.length">
                <td colspan="5" class="py-8 text-center text-slate-500 text-sm">No leads yet</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent Vendor Applications — 1 col -->
      <div class="admin-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-white">Vendor Applications</h2>
          <NuxtLink to="/admin/vendors" class="text-xs text-cyan-400 hover:text-cyan-300 transition">View All →</NuxtLink>
        </div>
        <div v-if="recentVendors.length" class="space-y-3">
          <div v-for="vendor in recentVendors" :key="vendor.id"
               class="flex items-center justify-between p-3 rounded-lg border border-white/5 hover:border-white/10 transition cursor-pointer"
               @click="navigateTo(`/admin/vendors/${vendor.id}`)">
            <div>
              <p class="text-sm font-medium text-slate-300">{{ vendor.name }}</p>
              <p class="text-xs text-slate-500 mt-0.5">{{ vendor.country }}</p>
            </div>
            <StatusBadge :status="vendor.verification_status" />
          </div>
        </div>
        <div v-else class="text-center py-8">
          <p class="text-sm text-slate-500">No pending applications</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin', middleware: 'admin' })

const stats = reactive({
  new_leads: 0,
  pending_vendors: 0,
  pending_products: 0,
  active_projects: 0,
  open_tickets: 0,
})

const { apiFetch } = useApi()
const recentLeads = ref<any[]>([])
const recentVendors = ref<any[]>([])

const statCards = computed(() => [
  { label: 'New Leads', value: stats.new_leads, emoji: '📋', bg: 'bg-blue-500/10', sub: 'Awaiting review' },
  { label: 'Vendors', value: stats.pending_vendors, emoji: '🏢', bg: 'bg-amber-500/10', sub: 'Pending approval' },
  { label: 'Products', value: stats.pending_products, emoji: '📦', bg: 'bg-orange-500/10', sub: 'Need review' },
  { label: 'Projects', value: stats.active_projects, emoji: '🔧', bg: 'bg-emerald-500/10', sub: 'Active now' },
  { label: 'Tickets', value: stats.open_tickets, emoji: '🎫', bg: 'bg-red-500/10', sub: 'Open issues' },
])

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

onMounted(async () => {
  try {
    const data = await apiFetch<any>('/admin/dashboard')
    if (data.stats) Object.assign(stats, data.stats)
    recentLeads.value = data.recent_leads || []
    recentVendors.value = data.recent_vendors || []
  } catch {}
})
</script>
