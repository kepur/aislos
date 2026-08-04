<template>
  <section class="relative overflow-hidden border-b" :style="{ borderColor: 'var(--hairline, rgba(255,255,255,.1))' }">
    <div class="container-main px-4 sm:px-6 lg:px-8 py-14 lg:py-20">
      <!-- Breadcrumb keeps deep sub-pages navigable, which is the point of
           splitting them out in the first place. -->
      <nav v-if="crumbs.length" class="mb-5 flex flex-wrap items-center gap-2 text-sm">
        <template v-for="(crumb, i) in crumbs" :key="crumb.to || crumb.label">
          <NuxtLink
            v-if="crumb.to"
            :to="crumb.to"
            class="text-slate-400 transition hover:text-[color:var(--brand-strong,#0ea5e9)]"
          >{{ crumb.label }}</NuxtLink>
          <span v-else class="text-slate-400">{{ crumb.label }}</span>
          <span v-if="i < crumbs.length - 1" class="text-slate-300">/</span>
        </template>
      </nav>

      <div class="grid gap-10 lg:grid-cols-[1.15fr_1fr] lg:items-center">
        <div>
          <span v-if="eyebrow" class="knx-eyebrow">{{ eyebrow }}</span>
          <h1 class="mt-3 text-3xl font-bold leading-tight tracking-tight text-white lg:text-5xl">
            {{ title }}
          </h1>
          <p v-if="subtitle" class="mt-5 max-w-2xl text-lg leading-relaxed text-slate-300">
            {{ subtitle }}
          </p>

          <div v-if="badges?.length" class="mt-6 flex flex-wrap gap-2">
            <span v-for="b in badges" :key="b.label" :class="b.ai ? 'knx-pill-ai' : 'knx-pill'">
              <span v-if="b.ai" aria-hidden="true">✦</span>{{ b.label }}
            </span>
          </div>

          <div v-if="$slots.actions" class="mt-8 flex flex-col gap-3 sm:flex-row">
            <slot name="actions" />
          </div>
        </div>

        <div v-if="$slots.aside" class="lg:justify-self-end lg:w-full">
          <slot name="aside" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Crumb { label: string; to?: string }
interface Badge { label: string; ai?: boolean }

withDefaults(
  defineProps<{
    title: string
    eyebrow?: string
    subtitle?: string
    crumbs?: Crumb[]
    badges?: Badge[]
  }>(),
  { crumbs: () => [], badges: () => [] }
)
</script>
