<template>
  <section class="space-y-5">
    <div>
      <p class="text-xs font-semibold uppercase tracking-widest text-emerald-300">Supplier workspace</p>
      <h1 class="mt-1 text-2xl font-bold text-white">供应商团队</h1>
      <p class="mt-1 text-sm text-slate-400">邀请公司成员处理目录、需求匹配、报价与订单。</p>
    </div>

    <form v-if="canManageTeam" class="pc-card grid gap-3 md:grid-cols-3" @submit.prevent="invite">
      <input v-model="form.full_name" class="input-field" placeholder="Full name" />
      <input v-model="form.email" class="input-field" type="email" required placeholder="Email" />
      <input v-model="form.phone" class="input-field" placeholder="Phone" />
      <button class="btn-primary md:col-span-3" :disabled="saving">
        {{ saving ? 'Inviting...' : 'Invite supplier operator' }}
      </button>
      <p v-if="message" class="text-sm text-emerald-300 md:col-span-3">{{ message }}</p>
    </form>
    <p v-else class="pc-card text-sm text-slate-300">Team management is available to the supplier company owner. Your operator access remains active for daily work.</p>

    <div v-if="loading" class="pc-card text-sm text-slate-400">Loading team...</div>
    <div v-else class="grid gap-3">
      <article v-for="item in items" :key="item.id" class="pc-card flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <p class="font-semibold text-white">{{ item.full_name || item.email }}</p>
            <span :class="item.is_active ? 'text-emerald-300' : 'text-amber-300'" class="text-xs font-semibold">
              {{ item.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <p class="text-sm text-slate-400">{{ item.email }} · {{ item.role }}</p>
        </div>
        <button
          v-if="canManageTeam"
          type="button"
          class="btn-secondary"
          :disabled="busyId === item.id"
          @click="setActive(item, !item.is_active)"
        >
          {{ busyId === item.id ? 'Saving...' : item.is_active ? 'Deactivate' : 'Restore access' }}
        </button>
      </article>
      <p v-if="!items.length" class="pc-card text-sm text-slate-400">No supplier team members.</p>
    </div>
    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

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
    message.value = 'Member invited. They must use password recovery before first login.'
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
