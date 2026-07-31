<template>
  <div v-if="isLoggedIn && availableForFrontend.length > 1" class="flex items-center gap-1">
    <select
      v-if="memberships.length > 1"
      :value="activeWorkspaceId || ''"
      class="max-w-24 rounded-md border border-slate-200 bg-white px-1 py-1 text-[10px] text-slate-600"
      aria-label="Active workspace"
      @change="selectWorkspace(($event.target as HTMLSelectElement).value || null)"
    >
      <option value="" disabled>Workspace</option>
      <option v-for="membership in memberships" :key="membership.id" :value="membership.workspace_id">
        {{ membership.membership_type }}
      </option>
    </select>
    <select
      :value="manifest?.portal_key || activePortalCookie || ''"
      class="max-w-28 rounded-md border border-slate-200 bg-white px-1 py-1 text-[10px] text-slate-600"
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
    await navigateTo({ path: '/access-denied', query: { reason: e?.data?.detail || e?.message } })
  }
}
</script>
