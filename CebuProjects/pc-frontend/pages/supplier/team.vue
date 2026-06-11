<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Team</h1>
        <p class="text-slate-500 mt-1">Manage staff who can operate this supplier account.</p>
      </div>
      <UButton color="indigo" icon="i-heroicons-user-plus" @click="showInvite = true">Invite Member</UButton>
    </div>

    <UAlert
      color="blue"
      icon="i-heroicons-information-circle"
      title="Team permissions are staged"
      description="This page is now reachable from My Business. Full role permissions and email invites should connect to the admin staff model in the next backend pass."
    />

    <UCard>
      <div class="flex items-center gap-4 p-3 rounded-xl bg-slate-50">
        <UAvatar src="https://i.pravatar.cc/80?u=supplier-owner" size="md" />
        <div class="flex-1">
          <p class="font-semibold text-slate-900">{{ authStore.displayName }}</p>
          <p class="text-sm text-slate-500">Supplier account owner</p>
        </div>
        <UBadge color="indigo" variant="soft">OWNER</UBadge>
        <UBadge color="green" variant="soft">ACTIVE</UBadge>
      </div>
    </UCard>

    <UModal v-model="showInvite">
      <UCard>
        <template #header>
          <h3 class="font-semibold text-slate-900">Invite Supplier Team Member</h3>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Email">
            <UInput v-model="inviteEmail" type="email" placeholder="sales@company.com" />
          </UFormGroup>
          <UFormGroup label="Role">
            <USelect v-model="inviteRole" :options="['SUPPLIER_AGENT', 'SUPPLIER_ADMIN']" />
          </UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="showInvite = false">Cancel</UButton>
            <UButton color="indigo" @click="sendInvite">Send Invite</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'supplier' })

const authStore = useAuthStore()
const toast = useToast()
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('SUPPLIER_AGENT')

function sendInvite() {
  if (!inviteEmail.value) return
  toast.add({ title: `Invitation staged for ${inviteEmail.value}`, color: 'green' })
  showInvite.value = false
  inviteEmail.value = ''
}
</script>
