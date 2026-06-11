<template>
  <div class="min-h-screen bg-slate-50 pb-safe-tab">
    <slot />
    <SupplierBottomTabs />
  </div>
</template>

<script setup lang="ts">
import SupplierBottomTabs from "~/components/layout/SupplierBottomTabs.vue";

defineOptions({ name: "SupplierLayout" });
</script>
