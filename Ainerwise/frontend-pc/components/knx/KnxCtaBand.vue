<template>
  <section class="py-14 lg:py-20">
    <div class="container-main px-4 sm:px-6 lg:px-8">
      <div class="knx-cta knx-on-dark rounded-2xl px-8 py-12 text-center lg:px-16">
        <h2 class="text-2xl font-bold tracking-tight lg:text-3xl">{{ title }}</h2>
        <p v-if="subtitle" class="mx-auto mt-3 max-w-2xl leading-relaxed opacity-90">{{ subtitle }}</p>
        <div class="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <NuxtLink :to="primaryTo" class="knx-cta-primary">{{ primaryLabel }}</NuxtLink>
          <NuxtLink v-if="secondaryTo" :to="secondaryTo" class="knx-cta-secondary">{{ secondaryLabel }}</NuxtLink>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  primaryTo: string
  primaryLabel: string
  secondaryTo?: string
  secondaryLabel?: string
}>()
</script>

<style scoped>
.knx-cta {
  background: var(--brand, #0284c7);
  color: #fff;
}
.knx-cta-primary {
  @apply inline-flex items-center justify-center rounded-full px-8 py-3 text-sm font-semibold transition;
  background: #fff;
  color: var(--brand-strong, #0369a1);
}
.knx-cta-primary:hover { opacity: 0.9; }
.knx-cta-secondary {
  @apply inline-flex items-center justify-center rounded-full border px-8 py-3 text-sm font-semibold text-white transition;
  border-color: rgba(255, 255, 255, 0.5);
}
.knx-cta-secondary:hover { background: rgba(255, 255, 255, 0.12); }
</style>
