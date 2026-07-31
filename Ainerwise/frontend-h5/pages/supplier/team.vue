<template>
  <div class="space-y-4 p-4">
    <div>
      <p class="text-[10px] font-bold uppercase tracking-widest text-emerald-600">Supplier workspace</p>
      <h1 class="text-xl font-bold text-slate-800">Team access</h1>
      <p class="mt-1 text-xs text-slate-500">Invite operators and control access to this supplier company.</p>
    </div>

    <form v-if="canManageTeam" class="m-card space-y-3" @submit.prevent="invite">
      <input v-model="form.full_name" class="m-input" placeholder="Full name" />
      <input v-model="form.email" class="m-input" type="email" required placeholder="Email" />
      <input v-model="form.phone" class="m-input" placeholder="Phone" />
      <button class="m-btn-primary w-full" :disabled="saving">
        {{ saving ? 'Inviting...' : 'Invite operator' }}
      </button>
      <p v-if="message" class="text-xs text-emerald-600">{{ message }}</p>
    </form>
    <p v-else class="m-card text-xs text-slate-500">Only the supplier company owner can invite or deactivate operators.</p>

    <div v-if="loading" class="m-card text-sm text-slate-400">Loading team...</div>
    <template v-else>
      <article v-for="item in items" :key="item.id" class="m-card space-y-3">
        <div>
          <div class="flex items-center justify-between gap-2">
            <p class="text-sm font-semibold text-slate-800">{{ item.full_name || item.email }}</p>
            <span :class="item.is_active ? 'text-emerald-600' : 'text-amber-600'" class="text-[10px] font-bold uppercase">
              {{ item.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-400">{{ item.email }}</p>
        </div>
        <button v-if="canManageTeam" type="button" class="m-card w-full py-2 text-xs font-semibold" :disabled="busyId === item.id" @click="setActive(item, !item.is_active)">
          {{ busyId === item.id ? 'Saving...' : item.is_active ? 'Deactivate' : 'Restore access' }}
        </button>
      </article>
    </template>
    <p v-if="!loading && !items.length" class="m-card text-sm text-slate-400">No supplier team members.</p>
    <p v-if="error" class="m-card text-sm text-red-600">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const { getSupplierAccount, listSupplierTeam, inviteSupplierTeamMember, updateSupplierTeamMember } = useCommerce()
const items = ref<any[]>([])
const loading = ref(true)
const saving = ref(false)
const busyId = ref('')
const error = ref('')
const message = ref('')
const canManageTeam = ref(false)
const form = reactive({ full_name: '', email: '', phone: '' })

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [team, account] = await Promise.all([listSupplierTeam(), getSupplierAccount()])
    items.value = team.items
    canManageTeam.value = account.permissions?.manage_team === true
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || 'Team could not be loaded.'
  } finally {
    loading.value = false
  }
}

async function invite() {
  saving.value = true
  error.value = ''
  message.value = ''
  try {
    await inviteSupplierTeamMember(form)
    Object.assign(form, { full_name: '', email: '', phone: '' })
    message.value = 'Member invited. Password recovery is required before first login.'
    await load()
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || 'Member could not be invited.'
  } finally {
    saving.value = false
  }
}

async function setActive(item: any, isActive: boolean) {
  busyId.value = item.id
  error.value = ''
  try {
    await updateSupplierTeamMember(item.id, { is_active: isActive })
    await load()
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || 'Member could not be updated.'
  } finally {
    busyId.value = ''
  }
}

onMounted(load)
</script>
