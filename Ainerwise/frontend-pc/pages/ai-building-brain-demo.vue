<template>
  <div class="min-h-screen bg-slate-950" aria-hidden="true"></div>
</template>

<script setup lang="ts">
import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

const route = useRoute()
const prefix = getLocalePrefixFromPath(route.path)
const target = prefix
  ? withLocalePrefix('/ai-building-brain#immersive-demo', prefix)
  : '/ai-building-brain#immersive-demo'

await navigateTo(target, { replace: true })
</script>
