<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <span class="text-sm text-slate-500">{{ staff.length }} {{ t('staff.members') }}</span>
      <button class="btn btn-primary" @click="showInvite = true">{{ t('staff.invite') }}</button>
    </div>

    <div class="card overflow-hidden">
      <table class="w-full">
        <thead><tr><th class="table-th">{{ t('users.name') }}</th><th class="table-th">{{ t('users.role') }}</th><th class="table-th">{{ t('common.status') }}</th><th class="table-th">{{ t('common.actions') }}</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="4" class="table-td text-center py-10 text-slate-400">{{ t('common.loading') }}</td></tr>
          <tr v-for="s in staff" :key="s.id" class="hover:bg-slate-50">
            <td class="table-td"><p class="font-medium">{{ s.full_name || '—' }}</p><p class="text-xs text-slate-400">{{ s.email }}</p></td>
            <td class="table-td">
              <select class="input py-1 text-xs w-44" :value="s.role" @change="changeRole(s.id, $event.target.value)">
                <option v-for="r in adminRoles" :key="r" :value="r">{{ r }}</option>
              </select>
            </td>
            <td class="table-td"><span :class="s.status==='ACTIVE'?'badge-green':'badge-red'" class="badge">{{ s.status }}</span></td>
            <td class="table-td">
              <button v-if="s.status==='ACTIVE'" class="btn btn-danger py-1 px-3 text-xs" @click="setStatus(s, 'SUSPENDED')">{{ t('users.suspend') }}</button>
              <button v-else class="btn btn-success py-1 px-3 text-xs" @click="setStatus(s, 'ACTIVE')">{{ t('users.activate') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Invite modal -->
    <div v-if="showInvite" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showInvite=false">
      <div class="bg-white rounded-2xl w-full max-w-md p-6 space-y-4">
        <h3 class="font-bold text-lg text-slate-900">{{ t('staff.inviteTitle') }}</h3>
        <input v-model="inv.email" class="input" :placeholder="t('login.email')" />
        <input v-model="inv.full_name" class="input" :placeholder="t('staff.fullName')" />
        <input v-model="inv.password" type="password" class="input" :placeholder="t('staff.tempPassword')" />
        <select v-model="inv.role" class="input">
          <option v-for="r in adminRoles" :key="r" :value="r">{{ r }}</option>
        </select>
        <p v-if="invError" class="text-sm text-red-600">{{ invError }}</p>
        <div class="flex gap-3">
          <button class="btn btn-secondary flex-1" @click="showInvite=false">{{ t('common.cancel') }}</button>
          <button class="btn btn-primary flex-1" :disabled="inviting" @click="invite">{{ inviting ? t('staff.inviting') : t('staff.sendInvite') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '@/utils/api'

const { t } = useI18n()
const loading = ref(true)
const staff = ref([])
const showInvite = ref(false)
const inviting = ref(false)
const invError = ref('')
const adminRoles = ['ADMIN','SUPER_ADMIN','OPS_MANAGER','FINANCE_OFFICER','RISK_ANALYST','DISPUTE_AGENT','VERIFICATION_OFFICER','SUPPORT_AGENT','AUDITOR']
const inv = reactive({ email:'', full_name:'', password:'', role:'ADMIN' })

async function invite() {
  invError.value = ''
  if (!inv.email || !inv.full_name || inv.password.length < 8) { invError.value = t('staff.fillAll'); return }
  inviting.value = true
  try {
    const { data } = await api.post('/admin/staff/invite', inv)
    staff.value.push(data)
    showInvite.value = false
    inv.email = ''; inv.full_name = ''; inv.password = ''
  } catch (e) { invError.value = e.response?.data?.detail || 'Failed' }
  finally { inviting.value = false }
}

async function changeRole(id, role) {
  try {
    const { data } = await api.put(`/admin/staff/${id}/role`, { role, reason: 'Admin console update' })
    const idx = staff.value.findIndex(s => s.id === id)
    if (idx >= 0) staff.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

async function setStatus(user, status) {
  try {
    const { data } = await api.post(`/admin/users/${user.id}/status`, { status, reason_code:'ADMIN_ACTION', reason_text:'Staff action', notify_user:false })
    const idx = staff.value.findIndex(s => s.id === data.id)
    if (idx >= 0) staff.value[idx] = data
  } catch (e) { alert(e.response?.data?.detail || 'Failed') }
}

onMounted(async () => {
  staff.value = await api.get('/admin/staff').then(r => r.data)
  loading.value = false
})
</script>
