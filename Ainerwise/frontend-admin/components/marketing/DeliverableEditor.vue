<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-200">{{ $t('marketingIntegration.deliverables') }}</h3>
      <button
        v-if="!readonly"
        type="button"
        class="text-xs px-3 py-1.5 rounded-lg border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10"
        @click="addRow"
      >
        + {{ $t('marketingIntegration.addDeliverable') }}
      </button>
    </div>

    <p v-if="!model.length" class="text-sm text-slate-500">{{ $t('marketingIntegration.noDeliverables') }}</p>

    <div
      v-for="(row, index) in model"
      :key="index"
      class="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-3"
    >
      <div class="flex items-center justify-between gap-2">
        <p class="text-xs uppercase tracking-wider text-slate-500">
          {{ $t('marketingIntegration.deliverable') }} #{{ index + 1 }}
        </p>
        <button
          v-if="!readonly"
          type="button"
          class="text-xs text-red-400 hover:text-red-300"
          @click="removeRow(index)"
        >
          {{ $t('common.delete') }}
        </button>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Key</span>
          <input
            v-model="row.key"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
            placeholder="instagram-square-en-v1"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Media type</span>
          <select
            v-model="row.media_type"
            :disabled="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          >
            <option value="image">image</option>
            <option value="video">video</option>
            <option value="audio">audio</option>
          </select>
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Channel</span>
          <input
            v-model="row.channel"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Language</span>
          <input
            v-model="row.language"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Format</span>
          <input
            v-model="row.format"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Variants</span>
          <input
            v-model.number="row.variant_count"
            type="number"
            min="1"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Width</span>
          <input
            v-model.number="row.width"
            type="number"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Height</span>
          <input
            v-model.number="row.height"
            type="number"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
        <label class="block">
          <span class="text-[10px] uppercase tracking-wider text-slate-500">Duration (s)</span>
          <input
            v-model.number="row.duration_seconds"
            type="number"
            :readonly="readonly"
            class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
          />
        </label>
      </div>

      <label class="block">
        <span class="text-[10px] uppercase tracking-wider text-slate-500">Notes</span>
        <textarea
          v-model="row.notes"
          :readonly="readonly"
          rows="2"
          class="mt-1 w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-200"
        />
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DeliverableSpec } from '~/composables/useMarketingIntegration'
import { emptyDeliverable } from '~/composables/useMarketingIntegration'

const model = defineModel<DeliverableSpec[]>({ required: true })
defineProps<{ readonly?: boolean }>()

function addRow() {
  model.value = [...model.value, emptyDeliverable()]
}

function removeRow(index: number) {
  model.value = model.value.filter((_, i) => i !== index)
}
</script>
