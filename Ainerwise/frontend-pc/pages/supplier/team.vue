<template>
  <section class="space-y-5">
    <div>
      <p class="text-xs font-semibold uppercase tracking-widest text-emerald-300">{{ $t('supplier.workspace') }}</p>
      <h1 class="mt-1 text-2xl font-bold text-white">{{ $t('supTeam.title') }}</h1>
      <p class="mt-1 text-sm text-slate-400">{{ $t('supTeam.subtitle') }}</p>
    </div>

    <form v-if="canManageTeam" class="pc-card grid gap-3 md:grid-cols-3" @submit.prevent="invite">
      <input v-model="form.full_name" class="input-field" :placeholder="$t('supTeam.fullNamePh')" />
      <input v-model="form.email" class="input-field" type="email" required :placeholder="$t('supTeam.emailPh')" />
      <input v-model="form.phone" class="input-field" :placeholder="$t('supTeam.phonePh')" />
      <button class="btn-primary md:col-span-3" :disabled="saving">
        {{ saving ? $t('supTeam.inviting') : $t('supTeam.invite') }}
      </button>
      <p v-if="message" class="text-sm text-emerald-300 md:col-span-3">{{ message }}</p>
    </form>
    <p v-else class="pc-card text-sm text-slate-300">{{ $t('supTeam.ownerOnly') }}</p>

    <div v-if="loading" class="pc-card text-sm text-slate-400">{{ $t('supTeam.loading') }}</div>
    <div v-else class="grid gap-3">
      <article v-for="item in items" :key="item.id" class="pc-card flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <p class="font-semibold text-white">{{ item.full_name || item.email }}</p>
            <span :class="item.is_active ? 'text-emerald-300' : 'text-amber-300'" class="text-xs font-semibold">
              {{ item.is_active ? $t('supTeam.active') : $t('supTeam.inactive') }}
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
          {{ busyId === item.id ? $t('supTeam.saving') : item.is_active ? $t('supTeam.deactivate') : $t('supTeam.restore') }}
        </button>
      </article>
      <p v-if="!items.length" class="pc-card text-sm text-slate-400">{{ $t('supTeam.noMembers') }}</p>
    </div>
    <p v-if="error" class="pc-card text-sm text-red-300">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'procurement', middleware: ['auth'] })

const { t } = useI18n()
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
    error.value = cause?.data?.detail || cause?.message || t('supTeam.loadFailed')
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
    message.value = t('supTeam.invited')
    await load()
  } catch (cause: any) {
    error.value = cause?.data?.detail || cause?.message || t('supTeam.inviteFailed')
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
    error.value = cause?.data?.detail || cause?.message || t('supTeam.updateFailed')
  } finally {
    busyId.value = ''
  }
}

onMounted(load)
</script>
