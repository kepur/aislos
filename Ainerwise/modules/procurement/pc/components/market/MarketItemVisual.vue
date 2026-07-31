<template>
  <div class="relative h-full w-full overflow-hidden" :style="{ background: palette.background }">
    <div class="absolute inset-0 opacity-70" :style="{ background: palette.mesh }"></div>
    <div class="absolute left-5 top-5 rounded-full border border-white/50 bg-white/70 px-3 py-1 text-[11px] font-semibold text-slate-700 shadow-sm backdrop-blur">
      {{ shortCategory }}
    </div>
    <div class="absolute inset-x-6 top-1/2 -translate-y-1/2 rounded-3xl border border-white/60 bg-white/75 p-5 shadow-xl shadow-slate-900/10 backdrop-blur">
      <div class="flex items-center gap-4">
        <div class="grid h-16 w-16 place-items-center rounded-2xl" :style="{ background: palette.accent }">
          <svg class="h-9 w-9 text-white" viewBox="0 0 48 48" fill="none" aria-hidden="true">
            <path d="M8 17.5 24 9l16 8.5v17L24 43 8 34.5v-17Z" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/>
            <path d="m8 17.5 16 8.5 16-8.5M24 26v17" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="min-w-0 flex-1">
          <div class="h-2.5 w-11/12 rounded-full" :style="{ background: palette.lineStrong }"></div>
          <div class="mt-2 h-2 w-2/3 rounded-full bg-slate-200"></div>
          <div class="mt-4 grid grid-cols-5 items-end gap-1.5">
            <span v-for="bar in bars" :key="bar" class="rounded-t-full" :style="{ height: `${bar}px`, background: palette.accent }"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="absolute bottom-5 left-5 right-5 truncate rounded-2xl bg-slate-950/75 px-4 py-2 text-xs font-semibold text-white shadow-lg">
      {{ title || 'AISLOS Market Item' }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title?: string | null
  categoryName?: string | null
}>()

const palettes = [
  {
    background: 'linear-gradient(135deg, #eef2ff 0%, #dbeafe 45%, #f8fafc 100%)',
    mesh: 'radial-gradient(circle at 22% 20%, rgba(99,102,241,.38), transparent 28%), radial-gradient(circle at 80% 30%, rgba(14,165,233,.26), transparent 24%)',
    accent: 'linear-gradient(135deg, #4f46e5, #06b6d4)',
    lineStrong: '#818cf8',
  },
  {
    background: 'linear-gradient(135deg, #ecfdf5 0%, #e0f2fe 48%, #f8fafc 100%)',
    mesh: 'radial-gradient(circle at 20% 22%, rgba(16,185,129,.34), transparent 28%), radial-gradient(circle at 78% 30%, rgba(59,130,246,.24), transparent 24%)',
    accent: 'linear-gradient(135deg, #059669, #2563eb)',
    lineStrong: '#34d399',
  },
  {
    background: 'linear-gradient(135deg, #fff7ed 0%, #eef2ff 48%, #f8fafc 100%)',
    mesh: 'radial-gradient(circle at 22% 20%, rgba(249,115,22,.26), transparent 28%), radial-gradient(circle at 80% 30%, rgba(79,70,229,.30), transparent 24%)',
    accent: 'linear-gradient(135deg, #f97316, #4f46e5)',
    lineStrong: '#fb923c',
  },
]

const hash = computed(() => {
  const value = `${props.categoryName || ''}${props.title || ''}`
  return [...value].reduce((sum, char) => sum + char.charCodeAt(0), 0)
})

const palette = computed(() => palettes[hash.value % palettes.length])
const bars = computed(() => [18, 30, 22, 42, 26].map((height, index) => height + ((hash.value + index * 7) % 12)))
const shortCategory = computed(() => (props.categoryName || 'AISLOS').split(/[\/&]/)[0].trim().slice(0, 18))
</script>
