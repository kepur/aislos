<template>
  <div class="min-h-screen bg-slate-50 pb-safe-tab">
    <slot />
    <BuyerBottomTabs />
    <NuxtLink to="/buyer/post-request">
      <button class="floating-btn" aria-label="Post Request">
        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import BuyerBottomTabs from "~/components/layout/BuyerBottomTabs.vue";

defineOptions({ name: "BuyerLayout" });
</script>
