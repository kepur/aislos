<template>
  <div v-if="isLoggedIn && availableForFrontend.length" class="flex items-center gap-2">
    <select
      v-if="memberships.length > 1"
      :value="activeWorkspaceId || ''"
      class="rounded border border-white/10 bg-slate-900 px-2 py-1 text-xs text-slate-200"
      aria-label="Active workspace"
      @change="onWorkspaceChange"
    >
      <option value="" disabled>{{ $t('comp.selectWorkspace') }}</option>
      <option v-for="membership in memberships" :key="membership.id" :value="membership.workspace_id">
        {{ membership.membership_type }}
      </option>
    </select>
    <select
      :value="manifest?.portal_key || activePortalCookie || ''"
      class="rounded border border-white/10 bg-slate-900 px-2 py-1 text-xs text-slate-200"
      aria-label="Active portal"
      @change="onPortalChange"
    >
      <option v-for="item in availableForFrontend" :key="item.portal_key" :value="item.portal_key">
        {{ item.display_name }}
      </option>
    </select>
    <span v-if="error" class="text-xs text-red-400">{{ error }}</span>
  </div>
</template>

<script setup lang="ts">
const { isLoggedIn } = useAuth()
const {
  manifest,
  memberships,
  activeWorkspaceId,
  activePortalCookie,
  availableForFrontend,
  selectWorkspace,
  switchAndNavigate,
} = usePortalManifest()
const error = ref('')

function onWorkspaceChange(event: Event) {
  selectWorkspace((event.target as HTMLSelectElement).value || null)
}

async function onPortalChange(event: Event) {
  error.value = ''
  try {
    await switchAndNavigate((event.target as HTMLSelectElement).value)
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Unable to switch portal'
  }
}
</script>
