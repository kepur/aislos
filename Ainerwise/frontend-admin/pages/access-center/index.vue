<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-500">Shared Auth & SSO Middleware V1</p>
        <h1 class="admin-page-title mt-1">Access Center</h1>
        <p class="mt-2 max-w-3xl text-sm text-slate-500">
          One AinerWise account controls PC, H5, Admin, Marketing, Procurement, Partner, Supplier, and Worker access.
          This page is the control-room view; role editing stays on the user management page until fine-grained Portal Grant editing is added.
        </p>
      </div>
      <NuxtLink
        to="/users"
        class="inline-flex items-center justify-center rounded-xl border border-cyan-500/40 px-4 py-2 text-sm font-semibold text-cyan-400 hover:bg-cyan-500/10"
      >
        Manage User Roles
      </NuxtLink>
    </div>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div v-for="card in summaryCards" :key="card.label" class="rounded-2xl border border-white/10 bg-slate-900/80 p-5 shadow-sm">
        <p class="text-xs uppercase tracking-[0.22em] text-slate-500">{{ card.label }}</p>
        <p class="mt-3 text-2xl font-black text-white">{{ card.value }}</p>
        <p class="mt-2 text-xs text-slate-400">{{ card.note }}</p>
      </div>
    </div>

    <section class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-lg font-bold text-white">Current Session Portal Grants</h2>
          <p class="mt-1 text-sm text-slate-500">
            Loaded from <code>/auth/me/portals</code>. These are the real portals available to the current logged-in account.
          </p>
        </div>
        <button
          class="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-300 hover:bg-white/5"
          :disabled="accessLoading"
          @click="refreshAccess"
        >
          {{ accessLoading ? 'Refreshing...' : 'Refresh Grants' }}
        </button>
      </div>

      <p v-if="accessError" class="mt-4 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-300">{{ accessError }}</p>

      <div v-if="availablePortals.length" class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <div v-for="portal in availablePortals" :key="portal.portal_key" class="rounded-xl border border-white/10 bg-slate-950/60 p-4">
          <p class="font-semibold text-white">{{ portal.display_name }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ portal.portal_key }} · {{ portal.physical_frontend }}</p>
          <p class="mt-3 text-xs text-slate-400">Home: <code>{{ portal.home_route }}</code></p>
        </div>
      </div>
      <p v-else class="mt-4 rounded-lg bg-slate-950/60 px-4 py-6 text-center text-sm text-slate-500">
        No portal grant is loaded for this account.
      </p>
    </section>

    <section class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
      <h2 class="text-lg font-bold text-white">Default Role Profiles</h2>
      <p class="mt-1 text-sm text-slate-500">
        This is the intended default mapping. Actual access must still be enforced by Membership, Portal Grant, route allowlist, workspace, and region.
      </p>
      <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <div v-for="profile in roleProfiles" :key="profile.role" class="rounded-xl border border-white/10 bg-slate-950/60 p-4">
          <div class="flex items-center justify-between gap-3">
            <p class="font-semibold text-white">{{ roleLabel(profile.role) }}</p>
            <span class="rounded-full bg-cyan-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-cyan-300">
              {{ profile.surface }}
            </span>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <span v-for="portal in profile.portals" :key="portal" class="rounded-full bg-white/5 px-2 py-1 text-xs text-slate-300">
              {{ portal }}
            </span>
          </div>
          <p class="mt-3 text-xs text-slate-500">{{ profile.note }}</p>
        </div>
      </div>
    </section>

    <section class="rounded-2xl border border-white/10 bg-slate-900/80 p-5">
      <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-lg font-bold text-white">Accounts Snapshot</h2>
          <p class="mt-1 text-sm text-slate-500">
            Real users from <code>/users</code>. Change role/active status in <NuxtLink class="text-cyan-400 hover:underline" to="/users">User Management</NuxtLink>.
          </p>
        </div>
        <button
          class="rounded-lg border border-white/10 px-3 py-2 text-xs font-semibold text-slate-300 hover:bg-white/5"
          :disabled="loadingUsers"
          @click="loadUsers"
        >
          {{ loadingUsers ? 'Loading...' : 'Refresh Users' }}
        </button>
      </div>

      <p v-if="userError" class="mt-4 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-300">{{ userError }}</p>

      <div class="mt-4 overflow-hidden rounded-xl border border-white/10">
        <table class="w-full text-left text-sm">
          <thead class="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th class="px-4 py-3">Account</th>
              <th class="px-4 py-3">Role</th>
              <th class="px-4 py-3">Default Access</th>
              <th class="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/10">
            <tr v-for="account in users" :key="account.id" class="bg-slate-900/50">
              <td class="px-4 py-3">
                <p class="font-medium text-white">{{ account.full_name || account.email }}</p>
                <p class="text-xs text-slate-500">{{ account.email }}</p>
              </td>
              <td class="px-4 py-3 text-slate-300">{{ roleLabel(account.role) }}</td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-2">
                  <span v-for="portal in portalsForRole(account.role)" :key="portal" class="rounded-full bg-cyan-500/10 px-2 py-1 text-xs text-cyan-200">
                    {{ portal }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span
                  class="rounded-full px-2 py-1 text-xs font-semibold"
                  :class="account.is_active ? 'bg-emerald-500/10 text-emerald-300' : 'bg-red-500/10 text-red-300'"
                >
                  {{ account.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
            </tr>
            <tr v-if="loadingUsers && !users.length">
              <td colspan="4" class="px-4 py-8 text-center text-slate-500">Loading accounts...</td>
            </tr>
            <tr v-else-if="!users.length">
              <td colspan="4" class="px-4 py-8 text-center text-slate-500">No accounts are available to this operator.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

type UserRow = {
  id: string
  email: string
  full_name?: string | null
  role: string
  is_active: boolean
}

const { apiFetch } = useApi()
const { user: currentUser } = useAuth()
const {
  availablePortals,
  memberships,
  activeWorkspaceId,
  accessError,
  loadAccess,
} = usePortalManifest()

const users = ref<UserRow[]>([])
const loadingUsers = ref(false)
const accessLoading = ref(false)
const userError = ref('')

const roleProfiles = [
  { role: 'super_admin', surface: 'All', portals: ['All Admin', 'PC', 'H5', 'Procurement'], note: 'Break-glass role. Keep limited to founders/operators.' },
  { role: 'admin', surface: 'Backoffice', portals: ['Admin', 'Cebu Admin', 'Marketing', 'AI Supervisor'], note: 'General operator with broad workbench access.' },
  { role: 'marketing_operator', surface: 'Marketing', portals: ['Marketing PC', 'Marketing H5'], note: 'Creates briefs, reviews assets, schedules publishing.' },
  { role: 'project_manager', surface: 'Delivery', portals: ['Project', 'Field Ops', 'Partner'], note: 'Owns work packages, crews, acceptance, and exceptions.' },
  { role: 'finance', surface: 'Finance', portals: ['Finance', 'Commerce', 'Settlement'], note: 'Reviews margins, payments, escrow, and reconciliation.' },
  { role: 'buyer', surface: 'Customer', portals: ['AinerWise PC', 'Customer H5', 'Procurement Buyer'], note: 'Customer shopping, solution intake, RFQ, order, and support.' },
  { role: 'vendor', surface: 'Supplier', portals: ['Supplier PC', 'Supplier H5'], note: 'Catalog, offers, orders, messages, payouts, KYC.' },
  { role: 'service_partner', surface: 'Partner', portals: ['Partner PC', 'Partner H5'], note: 'Partner company work packages, crews, and delivery coordination.' },
  { role: 'partner_worker', surface: 'Worker H5', portals: ['Field Worker PWA'], note: 'Task-driven mobile worker, no desktop backoffice required.' },
]

const profileByRole = computed(() => Object.fromEntries(roleProfiles.map(profile => [profile.role, profile])))
const adminPortalCount = computed(() => availablePortals.value.filter(portal => portal.physical_frontend === 'admin').length)
const physicalFrontends = computed(() => new Set(availablePortals.value.map(portal => portal.physical_frontend)).size)

const summaryCards = computed(() => [
  {
    label: 'Physical Admin',
    value: '1',
    note: 'Only frontend-admin is the backoffice shell.',
  },
  {
    label: 'Current Portals',
    value: String(availablePortals.value.length),
    note: `${adminPortalCount.value} admin workbench grants loaded.`,
  },
  {
    label: 'Workspaces',
    value: String(memberships.value.length),
    note: activeWorkspaceId.value ? `Active workspace ${activeWorkspaceId.value}` : 'No active workspace selected.',
  },
  {
    label: 'SSO Surface',
    value: String(physicalFrontends.value || 0),
    note: currentUser.value ? `Signed in as ${currentUser.value.email}` : 'Sign in to load Core session.',
  },
])

onMounted(async () => {
  await Promise.all([refreshAccess(), loadUsers()])
})

function roleLabel(role: string) {
  return role.split('_').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ')
}

function portalsForRole(role: string) {
  return profileByRole.value[role]?.portals || ['Manual Grant Required']
}

async function refreshAccess() {
  accessLoading.value = true
  try {
    await loadAccess(true)
  } finally {
    accessLoading.value = false
  }
}

async function loadUsers() {
  loadingUsers.value = true
  userError.value = ''
  try {
    const res = await apiFetch<{ items?: UserRow[] }>(`/users?skip=0&limit=50`)
    users.value = res.items || []
  } catch (e: any) {
    users.value = []
    userError.value = e?.data?.detail || e?.message || 'Unable to load accounts'
  } finally {
    loadingUsers.value = false
  }
}
</script>
