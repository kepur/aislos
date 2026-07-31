<template>
  <div v-if="isLoggedIn && availableForFrontend.length" class="flex items-center gap-2">
    <select
      v-if="memberships.length > 1"
      :value="activeWorkspaceId || ''"
      class="max-w-36 rounded border border-white/10 bg-slate-900 px-2 py-1 text-xs text-slate-300"
      aria-label="Active workspace"
      @change="selectWorkspace(($event.target as HTMLSelectElement).value || null)"
    >
      <option value="" disabled>Select workspace</option>
      <option v-for="membership in memberships" :key="membership.id" :value="membership.workspace_id">
        {{ membership.membership_type }}
      </option>
    </select>
    <select
      :value="manifest?.portal_key || activePortalCookie || ''"
      class="max-w-48 rounded border border-white/10 bg-slate-900 px-2 py-1 text-xs text-slate-300"
      aria-label="Active portal"
      @change="onPortalChange"
    >
      <option v-for="item in availableForFrontend" :key="item.portal_key" :value="item.portal_key">
        {{ item.display_name }}
      </option>
    </select>
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

async function onPortalChange(event: Event) {
  try {
    await switchAndNavigate((event.target as HTMLSelectElement).value)
  } catch (e: any) {
    showError({ statusCode: 403, statusMessage: e?.data?.detail || e?.message || 'Portal access denied' })
  }
}
</script>
