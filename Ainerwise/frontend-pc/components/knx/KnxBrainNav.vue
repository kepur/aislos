<template>
  <div class="border-b" :style="{ borderColor: 'var(--hairline, rgba(255,255,255,.1))' }">
    <div class="container-main px-4 sm:px-6 lg:px-8">
      <nav class="flex flex-wrap gap-1 overflow-x-auto">
        <NuxtLink
          v-for="tab in tabs"
          :key="tab.to"
          :to="tab.to"
          class="knx-tab whitespace-nowrap"
          :class="isActive(tab.to) ? 'knx-tab-active' : ''"
        >{{ tab.label }}</NuxtLink>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { t } = useI18n()

const tabs = computed(() => [
  { to: '/ai-building-brain', label: t('brain.overviewNav') },
  { to: '/ai-building-brain/levels', label: t('brain.levelsNav') },
  { to: '/ai-building-brain/process', label: t('brain.processNav') },
  { to: '/ai-building-brain-demo', label: t('brain.demoNav') },
])

function isActive(to: string) {
  // The overview must not stay highlighted on its own children.
  const path = route.path.replace(/^\/(en|cn|rs|pl|de|ro|ba)(?=\/|$)/, '') || '/'
  return to === '/ai-building-brain' ? path === to : path.startsWith(to)
}
</script>

<style scoped>
.knx-tab {
  @apply border-b-2 border-transparent px-4 py-3 text-sm font-medium transition-colors;
  color: var(--ink-muted, #94a3b8);
}
.knx-tab:hover { color: var(--ink, #fff); }
.knx-tab-active {
  border-color: var(--brand, #0ea5e9);
  color: var(--brand-strong, #38bdf8);
}
</style>
