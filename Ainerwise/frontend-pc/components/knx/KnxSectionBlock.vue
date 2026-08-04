<template>
  <section :class="['py-14 lg:py-20', tinted ? 'knx-tinted' : '']">
    <div class="container-main px-4 sm:px-6 lg:px-8">
      <div :class="['mb-10', centered ? 'text-center' : 'max-w-3xl']">
        <span v-if="eyebrow" class="knx-eyebrow">{{ eyebrow }}</span>
        <h2 class="mt-3 text-2xl font-bold tracking-tight text-white lg:text-3xl">{{ title }}</h2>
        <p v-if="subtitle" :class="['mt-3 text-slate-300 leading-relaxed', centered ? 'mx-auto max-w-2xl' : '']">
          {{ subtitle }}
        </p>
      </div>
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    eyebrow?: string
    subtitle?: string
    centered?: boolean
    /** Alternating tint is what gives a long page its rhythm. */
    tinted?: boolean
  }>(),
  { centered: false, tinted: false }
)
</script>

<style scoped>
.knx-tinted {
  background-color: var(--surface-alt, transparent);
}
</style>
