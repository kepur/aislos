<template>
  <nav class="mb-6 overflow-x-auto">
    <ol class="flex min-w-max gap-2">
      <li v-for="(step, index) in steps" :key="step.key">
        <button
          type="button"
          class="flex items-center gap-2 rounded-lg border px-3 py-2 text-left text-xs transition"
          :class="buttonClass(step.key, index)"
          @click="$emit('select', step.key)"
        >
          <span
            class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold"
            :class="index <= currentIndex ? 'bg-white/15 text-white' : 'bg-white/5 text-slate-500'"
          >
            {{ index + 1 }}
          </span>
          <span class="font-medium">{{ step.label }}</span>
        </button>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
export type WorkspaceStep = {
  key: string
  label: string
}

const props = defineProps<{
  steps: WorkspaceStep[]
  active: string
  accent?: string
}>()

defineEmits<{ select: [key: string] }>()

const currentIndex = computed(() => props.steps.findIndex(s => s.key === props.active))

function buttonClass(key: string, index: number) {
  if (key === props.active) {
    return 'border-white/25 bg-white/10 text-white'
  }
  if (index < currentIndex.value) {
    return 'border-white/10 bg-white/[0.03] text-slate-300 hover:bg-white/[0.06]'
  }
  return 'border-white/5 bg-transparent text-slate-500 hover:bg-white/[0.03]'
}
</script>
