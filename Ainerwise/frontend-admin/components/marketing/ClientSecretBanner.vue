<template>
  <div v-if="secret" class="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 space-y-2">
    <p class="text-sm font-semibold text-amber-200">{{ $t('marketingIntegration.secretOnceTitle') }}</p>
    <p class="text-xs text-amber-100/80">{{ $t('marketingIntegration.secretOnceHint') }}</p>
    <div class="flex flex-wrap items-center gap-2">
      <code class="flex-1 min-w-0 break-all rounded-lg bg-black/30 px-3 py-2 text-xs text-amber-100 font-mono">
        {{ secret }}
      </code>
      <button
        type="button"
        class="text-xs px-3 py-2 rounded-lg border border-amber-400/50 text-amber-200 hover:bg-amber-500/10"
        @click="copySecret"
      >
        {{ copied ? $t('marketingIntegration.copied') : $t('marketingIntegration.copySecret') }}
      </button>
      <button
        type="button"
        class="text-xs px-3 py-2 rounded-lg border border-white/20 text-slate-300 hover:bg-white/5"
        @click="$emit('dismiss')"
      >
        {{ $t('marketingIntegration.dismissSecret') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ secret: string | null }>()
defineEmits<{ dismiss: [] }>()

const copied = ref(false)

async function copySecret() {
  if (!props.secret) return
  try {
    await navigator.clipboard.writeText(props.secret)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // clipboard may be unavailable
  }
}
</script>
