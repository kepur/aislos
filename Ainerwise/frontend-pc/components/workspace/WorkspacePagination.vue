<template>
  <div v-if="totalPages > 1" class="mt-6 flex flex-wrap items-center justify-between gap-3">
    <p class="text-xs ws-faint">
      {{ $t('pagination.showing', { from: rangeFrom, to: rangeTo, total }) }}
    </p>
    <div class="flex items-center gap-1.5">
      <button class="ws-chip !px-3 !py-1.5" :disabled="page <= 1" @click="go(page - 1)">
        {{ $t('pagination.prev') }}
      </button>
      <button
        v-for="entry in pageEntries"
        :key="entry.key"
        class="ws-chip !min-w-[2.25rem] !px-2.5 !py-1.5 tabular-nums"
        :class="{ 'ws-chip-active': entry.value === page }"
        :disabled="entry.value === null"
        @click="entry.value !== null && go(entry.value)"
      >{{ entry.label }}</button>
      <button class="ws-chip !px-3 !py-1.5" :disabled="page >= totalPages" @click="go(page + 1)">
        {{ $t('pagination.next') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  page: number
  pageSize: number
  total: number
}>()
const emit = defineEmits<{ (e: 'update:page', value: number): void }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
const rangeFrom = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1))
const rangeTo = computed(() => Math.min(props.total, props.page * props.pageSize))

// Windowed page numbers with ellipses, so a long list does not produce a row
// of forty buttons.
const pageEntries = computed(() => {
  const total = totalPages.value
  const current = props.page
  const pages = new Set<number>([1, total, current, current - 1, current + 1])
  const sorted = [...pages].filter(n => n >= 1 && n <= total).sort((a, b) => a - b)
  const entries: Array<{ key: string; label: string; value: number | null }> = []
  let previous = 0
  for (const value of sorted) {
    if (previous && value - previous > 1) {
      entries.push({ key: `gap-${value}`, label: '…', value: null })
    }
    entries.push({ key: `p-${value}`, label: String(value), value })
    previous = value
  }
  return entries
})

function go(next: number) {
  const clamped = Math.min(Math.max(1, next), totalPages.value)
  if (clamped === props.page) return
  emit('update:page', clamped)
  if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>
