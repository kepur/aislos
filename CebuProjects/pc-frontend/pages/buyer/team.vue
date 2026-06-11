<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Team Members</h1>
        <p class="text-slate-500 mt-1">Manage who can access and act on behalf of your company account.</p>
      </div>
      <UButton color="indigo" icon="i-heroicons-user-plus" @click="showInvite = true">Invite Member</UButton>
    </div>

    <!-- Member list -->
    <UCard>
      <div v-if="loading" class="space-y-3">
        <div v-for="i in 3" :key="i" class="h-14 bg-slate-100 rounded-xl animate-pulse" />
      </div>
      <div v-else-if="members.length === 0" class="text-center py-10 text-slate-400">
        <div class="text-4xl mb-2">👥</div>
        <p class="text-sm">No team members yet. Invite someone to get started.</p>
      </div>
      <div v-else class="space-y-1">
        <div
          v-for="m in members"
          :key="m.id"
          class="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-50"
        >
          <UAvatar :src="`https://i.pravatar.cc/60?u=${m.email}`" size="sm" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-slate-900">{{ m.display_name || m.email }}</p>
            <p class="text-xs text-slate-400">{{ m.email }}</p>
          </div>
          <UBadge :color="m.role === 'OWNER' ? 'indigo' : 'gray'" variant="subtle" size="xs">{{ m.role }}</UBadge>
          <UBadge :color="m.status === 'ACTIVE' ? 'green' : 'yellow'" variant="subtle" size="xs">{{ m.status }}</UBadge>
          <UButton
            v-if="m.role !== 'OWNER'"
            size="xs"
            color="red"
            variant="ghost"
            icon="i-heroicons-trash"
            @click="removeMember(m)"
          />
        </div>
      </div>
    </UCard>

    <!-- Invite Modal -->
    <UModal v-model="showInvite">
      <UCard>
        <template #header>
          <h3 class="font-semibold text-slate-900">Invite Team Member</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Email Address">
            <UInput v-model="inviteEmail" type="email" placeholder="colleague@company.com" />
          </UFormGroup>
          <UFormGroup label="Role">
            <USelect v-model="inviteRole" :options="['MEMBER', 'MANAGER']" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showInvite = false">Cancel</UButton>
            <UButton color="indigo" :loading="inviting" @click="sendInvite">Send Invite</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['buyer'] })
const authStore = useAuthStore()
const config = useRuntimeConfig()
const toast = useToast()

const loading = ref(true)
const members = ref<any[]>([])
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('MEMBER')
const inviting = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await $fetch<any[]>(`${config.public.apiBase}/buyer/team/members`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    members.value = data ?? []
  } catch {
    // Fallback: show self as owner
    members.value = [{
      id: authStore.userId || 'me',
      email: authStore.email || '',
      display_name: authStore.displayName,
      role: 'OWNER',
      status: 'ACTIVE',
    }]
  } finally { loading.value = false }
}

async function sendInvite() {
  if (!inviteEmail.value) return
  inviting.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/team/invite`, {
      method: 'POST',
      body: { email: inviteEmail.value, role: inviteRole.value },
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    toast.add({ title: `Invitation sent to ${inviteEmail.value}`, color: 'green' })
    showInvite.value = false
    inviteEmail.value = ''
    await load()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Failed to send invite', color: 'red' })
  } finally { inviting.value = false }
}

async function removeMember(m: any) {
  if (!confirm(`Remove ${m.display_name || m.email} from the team?`)) return
  try {
    await $fetch(`${config.public.apiBase}/buyer/team/members/${m.id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    toast.add({ title: 'Member removed', color: 'green' })
    await load()
  } catch (e: any) {
    toast.add({ title: e?.data?.detail || 'Remove failed', color: 'red' })
  }
}

onMounted(() => load())
</script>
