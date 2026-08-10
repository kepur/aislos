<template>
  <div :class="['grid gap-4', columnsClass]">
    <component
      :is="item.to ? resolveLink : 'div'"
      v-for="item in items"
      :key="item.key || item.label"
      :to="localized(item.to)"
      class="knx-tile group"
    >
      <span
        class="flex h-12 w-12 items-center justify-center rounded-xl transition-colors"
        :style="{ backgroundColor: 'var(--brand-soft, rgba(14,165,233,.12))' }"
      >
        <FeatureIcon
          :name="item.icon"
          class="transition-transform group-hover:scale-110"
          :style="{ color: 'var(--brand-strong, #38bdf8)' }"
        />
      </span>
      <span class="text-sm font-semibold leading-snug">{{ item.label }}</span>
      <span v-if="item.hint" class="text-xs leading-relaxed text-slate-400">{{ item.hint }}</span>
      <span v-if="item.ai" class="knx-pill-ai !text-[10px]">✦ AI</span>
    </component>
  </div>
</template>

<script setup lang="ts">
const { localized } = useLocalizedLink()
import { resolveComponent } from 'vue'

interface GridItem {
  key?: string
  icon: string
  label: string
  hint?: string
  to?: string
  /** Marks a capability that exists because of the AI brain, not the bus. */
  ai?: boolean
}

const props = withDefaults(
  defineProps<{ items: GridItem[]; columns?: 2 | 3 | 4 }>(),
  { columns: 4 }
)

const resolveLink = resolveComponent('NuxtLink')

const columnsClass = computed(
  () =>
    ({
      2: 'grid-cols-1 sm:grid-cols-2',
      3: 'grid-cols-2 lg:grid-cols-3',
      4: 'grid-cols-2 lg:grid-cols-4',
    })[props.columns]
)
</script>
