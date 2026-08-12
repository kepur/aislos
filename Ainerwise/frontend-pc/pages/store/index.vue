<template>
  <div class="section-padding">
    <div class="container-main glass-panel p-8 text-center text-slate-300">
      {{ $t('store.redirecting') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { getLocalePrefixFromPath, withLocalePrefix } from '~/utils/localeRoutes'

const route = useRoute()
const prefix = getLocalePrefixFromPath(route.path)
await navigateTo(prefix ? withLocalePrefix('/products', prefix) : '/products', {
  replace: true,
  redirectCode: 302,
})
</script>
