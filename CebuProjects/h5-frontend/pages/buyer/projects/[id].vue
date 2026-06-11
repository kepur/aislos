<template>
  <div>
    <!-- Header -->
    <header class="bg-white border-b border-slate-100 px-4 flex items-center justify-between sticky top-0 z-40" style="height: 56px; padding-top: var(--safe-area-top)">
      <NuxtLink to="/buyer/projects" class="text-slate-500">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </NuxtLink>
      <h1 class="text-sm font-bold text-slate-900 truncate max-w-[60%]">{{ project?.title || $t('common.loading') }}</h1>
      <div class="w-5"></div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="p-6 text-center">
      <div class="text-3xl animate-pulse">🤖</div>
      <p class="text-sm text-slate-400 mt-2">{{ $t('project.loading_project') }}</p>
    </div>

    <div v-if="project && !loading" class="space-y-4 p-4 pb-32">
      <!-- Mobile Forge Progress -->
      <div class="card bg-gradient-to-r from-emerald-50 to-blue-50 border-emerald-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-[10px] font-bold uppercase tracking-wide text-emerald-700">{{ $t('project.forge') }}</p>
            <h2 class="text-base font-black text-slate-900">{{ $t('project.forge_headline') }}</h2>
          </div>
          <div class="text-right">
            <p class="text-[10px] text-slate-400">{{ $t('project.progress') }}</p>
            <p class="text-lg font-black text-emerald-700">{{ forgeProgress }}%</p>
          </div>
        </div>
        <div class="mt-3 flex gap-2 overflow-x-auto pb-1">
          <div
            v-for="stage in forgeStages"
            :key="stage.key"
            class="min-w-[72px] rounded-xl px-2 py-2 text-center border"
            :class="stage.status === 'done' ? 'bg-white border-green-200 text-green-700' : stage.status === 'active' ? 'bg-primary-600 border-primary-600 text-white' : 'bg-white/60 border-slate-200 text-slate-400'"
          >
            <span class="mx-auto mb-1 block h-2 w-2 rounded-full" :class="stage.status === 'done' ? 'bg-green-500 animate-pulse' : stage.status === 'active' ? 'bg-amber-300' : 'bg-slate-300'"></span>
            <p class="text-[10px] font-bold">{{ stage.label }}</p>
          </div>
        </div>
      </div>

      <!-- Status & Type -->
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-lg">{{ typeIcon(project.project_type) }}</span>
        <span :class="badgeClass(project.status)" class="text-[11px] px-2 py-0.5 rounded-full font-medium">
          {{ statusLabel(project.status) }}
        </span>
        <span v-if="project.country" class="text-[11px] text-slate-400 flex items-center gap-1">
          📍 {{ [project.city, project.country].filter(Boolean).join(', ') }}
        </span>
      </div>

      <!-- Description -->
      <div class="card">
        <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">📋 {{ $t('project.description') }}</h3>
        <p class="text-sm text-slate-700 whitespace-pre-wrap">{{ project.description || $t('project.no_description') }}</p>
        <div v-if="project.area_value || project.budget_max" class="flex gap-3 mt-3 text-xs text-slate-500">
          <span v-if="project.area_value">📐 {{ project.area_value }} {{ project.area_unit || 'sqm' }}</span>
          <span v-if="project.budget_max">💰 ₱{{ project.budget_max?.toLocaleString() }}</span>
          <span>{{ project.quality_preference?.replace(/_/g, ' ') }}</span>
        </div>
      </div>

      <!-- Conversation -->
      <div class="card border-primary-100">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-xs font-semibold text-primary-700 uppercase tracking-wide">💬 {{ $t('project.chat') }}</h3>
          <button @click="loadConversationData" class="text-[11px] text-slate-400">{{ $t('common.refresh') }}</button>
        </div>
        <div class="max-h-52 overflow-y-auto bg-slate-50 rounded-xl p-2 space-y-2">
          <p v-if="messages.length === 0" class="text-xs text-slate-400 text-center py-5">{{ $t('project.chat_empty') }}</p>
          <div v-for="msg in messages" :key="msg.id" class="flex" :class="msg.role === 'USER' ? 'justify-end' : 'justify-start'">
            <div class="max-w-[82%] rounded-2xl px-3 py-2 text-xs" :class="msg.role === 'USER' ? 'bg-primary-600 text-white' : msg.role === 'SYSTEM' ? 'bg-amber-50 text-amber-800' : 'bg-white text-slate-700 border border-slate-200'">
              <p class="whitespace-pre-wrap">{{ msg.content }}</p>
            </div>
          </div>
        </div>
        <div class="flex gap-2 mt-3">
          <textarea v-model="chatInput" rows="2" :placeholder="$t('project.chat_placeholder')" class="input-field flex-1 text-xs"></textarea>
          <button @click="sendMessage" :disabled="sendingMessage || !chatInput.trim()" class="px-3 rounded-xl bg-primary-600 text-white text-xs font-semibold disabled:opacity-40">
            {{ $t('project.send') }}
          </button>
        </div>
      </div>

      <!-- Metrics -->
      <div v-if="metrics" class="card">
        <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">📐 {{ $t('project.metrics') }}</h3>
        <div v-if="metrics.missing_required?.length" class="rounded-xl bg-amber-50 border border-amber-100 p-2 mb-2">
          <p class="text-[11px] font-semibold text-amber-700">{{ $t('project.missing') }}: {{ metrics.missing_required.map(m => m.label).join(', ') }}</p>
        </div>
        <div v-if="metrics.values?.length" class="space-y-1">
          <div v-for="metric in metrics.values" :key="metric.id" class="flex justify-between gap-3 text-xs">
            <span class="text-slate-400">{{ metric.label || metric.key }}</span>
            <span class="font-medium text-slate-700 text-right">{{ metricDisplay(metric.value_jsonb) }}</span>
          </div>
        </div>
        <p v-else class="text-xs text-slate-400">{{ $t('project.no_metrics') }}</p>
      </div>

      <!-- File Upload -->
      <div class="card">
        <h3 class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">📎 {{ $t('project.files') }} ({{ project.files?.length || 0 }})</h3>
        <label class="block border-2 border-dashed border-slate-200 rounded-xl p-4 text-center active:bg-slate-50 cursor-pointer">
          <div class="text-2xl mb-1">📤</div>
          <p class="text-xs text-slate-500">{{ $t('project.upload_hint') }}</p>
          <input type="file" multiple accept=".pdf,.txt,.docx,.doc,.jpg,.jpeg,.png,.webp" class="hidden" @change="handleFileSelect" />
        </label>
        <div v-if="uploading" class="text-xs text-primary-600 mt-2 flex items-center gap-1">
          <svg class="w-3 h-3 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M4 12a8 8 0 018-8" /></svg>
          {{ $t('project.uploading') }}
        </div>
        <div v-if="project.files?.length" class="mt-3 space-y-2">
          <div v-for="f in project.files" :key="f.id" class="flex items-center gap-2 bg-slate-50 rounded-xl px-3 py-2">
            <span class="text-base">{{ fileIcon(f.content_type) }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-medium text-slate-700 truncate">{{ f.file_name }}</p>
              <p class="text-[10px] text-slate-400">{{ (f.file_size / 1024).toFixed(1) }}KB</p>
            </div>
            <span :class="f.status === 'EXTRACTED' ? 'text-green-500' : f.status === 'FAILED' ? 'text-red-500' : 'text-slate-400'" class="text-[10px] font-medium">{{ f.status }}</span>
            <button @click="deleteFile(f.id)" class="text-red-400 active:text-red-600 p-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- AI Analysis Status -->
      <div v-if="aiRun" class="card" :class="aiRun.status === 'FAILED' ? 'border-red-200' : aiRun.status === 'SUCCESS' ? 'border-green-200' : 'border-blue-200'">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-base">🤖</span>
          <h3 class="text-xs font-semibold text-slate-600">{{ $t('project.ai_analysis') }}</h3>
          <span :class="aiStatusBadge" class="text-[11px] px-2 py-0.5 rounded-full font-medium ml-auto">
            {{ aiRun.status }}
          </span>
        </div>
        <div v-if="['RUNNING', 'PENDING'].includes(aiRun.status)" class="flex items-center gap-2 text-xs text-blue-600">
          <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M4 12a8 8 0 018-8" /></svg>
          {{ $t('project.analyzing') }}
        </div>
        <p v-if="aiRun.status === 'FAILED'" class="text-xs text-red-600">{{ normalizedAiError }}</p>
        <button
          v-if="aiRun.status === 'FAILED'"
          @click="retryAnalysis"
          :disabled="analyzing"
          class="mt-2 text-xs font-semibold px-4 py-2 rounded-xl bg-red-50 text-red-600 active:bg-red-100 disabled:opacity-50"
        >
          🔄 {{ $t('project.retry_analysis') }}
        </button>
      </div>

      <!-- AI Summary -->
      <div v-if="project.ai_summary" class="card bg-gradient-to-r from-primary-50 to-purple-50 border-primary-100">
        <h3 class="text-xs font-semibold text-primary-700 mb-2 flex items-center gap-1">✨ {{ $t('project.ai_summary') }}</h3>
        <p class="text-sm text-slate-700 whitespace-pre-wrap">{{ project.ai_summary }}</p>
      </div>

      <!-- Missing Questions -->
      <div v-if="project.missing_questions_jsonb?.length" class="card border-amber-100">
        <h3 class="text-xs font-semibold text-amber-700 mb-2">⚠️ {{ $t('project.missing_info') }}</h3>
        <div v-for="q in project.missing_questions_jsonb" :key="q.key" class="flex items-start gap-2 mb-2">
          <span :class="q.importance === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'" class="text-[9px] px-1.5 py-0.5 rounded-full font-bold flex-shrink-0 mt-0.5">
            {{ q.importance }}
          </span>
          <p class="text-xs text-slate-600">{{ q.question }}</p>
        </div>
      </div>

      <!-- Budget Estimate -->
      <div v-if="project.estimated_budget_jsonb" class="card bg-gradient-to-r from-green-50 to-emerald-50 border-green-100 text-center">
        <h3 class="text-xs font-semibold text-green-700 mb-2">💰 {{ $t('project.budget_estimate') }}</h3>
        <p class="text-xl font-bold text-green-800">
          ₱{{ (project.estimated_budget_jsonb.min || 0).toLocaleString() }}
          —
          ₱{{ (project.estimated_budget_jsonb.max || 0).toLocaleString() }}
        </p>
        <p class="text-[10px] text-green-600 mt-1">
          {{ ((project.estimated_budget_jsonb.confidence || 0) * 100).toFixed(0) }}% {{ $t('project.confidence') }}
        </p>

        <!-- Per-tier budget -->
        <div v-if="project.estimated_budget_jsonb.by_tier" class="grid grid-cols-3 gap-1.5 mt-3 pt-3 border-t border-green-200/60">
          <div class="rounded-lg bg-green-100/60 py-1.5 px-1">
            <p class="text-[9px] font-bold text-green-700">💰 Budget</p>
            <p class="text-[11px] font-bold text-green-900">₱{{ (project.estimated_budget_jsonb.by_tier.BUDGET?.min || 0).toLocaleString() }}</p>
          </div>
          <div class="rounded-lg bg-blue-100/60 py-1.5 px-1">
            <p class="text-[9px] font-bold text-blue-700">⭐ Mid</p>
            <p class="text-[11px] font-bold text-blue-900">₱{{ (project.estimated_budget_jsonb.by_tier.MID_RANGE?.min || 0).toLocaleString() }}</p>
          </div>
          <div class="rounded-lg bg-purple-100/60 py-1.5 px-1">
            <p class="text-[9px] font-bold text-purple-700">👑 Premium</p>
            <p class="text-[11px] font-bold text-purple-900">₱{{ (project.estimated_budget_jsonb.by_tier.PREMIUM?.min || 0).toLocaleString() }}</p>
          </div>
        </div>
      </div>

      <!-- Versioned Quote Report -->
      <div v-if="showReportSheet" class="card border-indigo-100">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div>
            <h3 class="text-xs font-semibold text-indigo-700 uppercase tracking-wide">📊 {{ $t('project.quote_report') }}</h3>
            <p class="text-[11px] text-slate-400 mt-0.5">
              v{{ report.current_version?.version_number || 1 }} · {{ report.current_version?.status || 'DRAFT' }}
            </p>
          </div>
          <div class="flex gap-1">
            <button
              @click="recalculateReport"
              :disabled="reportBusy"
              class="rounded-xl bg-indigo-50 px-2.5 py-1.5 text-[11px] font-semibold text-indigo-700 disabled:opacity-40"
            >
              {{ $t('project.reestimate') }}
            </button>
            <button
              @click="freezeReport"
              :disabled="reportBusy"
              class="rounded-xl bg-amber-50 px-2.5 py-1.5 text-[11px] font-semibold text-amber-700 disabled:opacity-40"
            >
              {{ $t('project.freeze') }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 mb-3">
          <div v-for="card in reportTotalCards" :key="card.key" class="rounded-xl bg-slate-50 px-3 py-2">
            <p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{{ card.label }}</p>
            <p class="text-sm font-black text-slate-900">₱{{ card.value.toLocaleString() }}</p>
          </div>
        </div>

        <div class="space-y-2">
          <div v-for="row in report.rows" :key="row.id" class="rounded-2xl border border-slate-100 bg-white p-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <input
                  :value="row.name"
                  class="w-full bg-transparent text-sm font-bold text-slate-900 outline-none"
                  :placeholder="$t('project.item_name')"
                  @change="updateReportCell(row.id, 'name', eventValue($event))"
                />
                <p class="text-[10px] text-slate-400 mt-1">{{ row.category_hint || $t('project.uncategorized') }} · {{ row.match_status }}</p>
              </div>
              <span class="rounded-full px-2 py-0.5 text-[10px] font-bold" :class="row.match_status === 'MATCHED' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'">
                {{ row.match_status === 'MATCHED' ? $t('project.matched') : $t('project.open') }}
              </span>
            </div>

            <div class="grid grid-cols-2 gap-2 mt-3">
              <label class="text-[10px] font-semibold text-slate-400">
                {{ $t('project.qty') }}
                <input
                  :value="row.qty"
                  type="number"
                  min="0"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-indigo-300"
                  @change="updateReportCell(row.id, 'qty', eventNumber($event))"
                />
              </label>
              <label class="text-[10px] font-semibold text-slate-400">
                {{ $t('project.unit') }}
                <input
                  :value="row.unit"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-indigo-300"
                  @change="updateReportCell(row.id, 'unit', eventValue($event))"
                />
              </label>
            </div>

            <div class="grid grid-cols-3 gap-1.5 mt-3">
              <button
                v-for="tier in ['BUDGET', 'MID_RANGE', 'PREMIUM']"
                :key="tier"
                type="button"
                class="rounded-xl border px-1.5 py-2 text-center"
                :class="row.selected_tier === tier ? 'border-indigo-500 bg-indigo-50 text-indigo-700' : 'border-slate-100 bg-slate-50 text-slate-500'"
                @click="updateReportCell(row.id, 'selected_tier', tier)"
              >
                <p class="text-[9px] font-bold">{{ tier === 'MID_RANGE' ? 'MID' : tier }}</p>
                <p class="text-[11px] font-black">₱{{ reportTierTotal(row, tier).toLocaleString() }}</p>
              </button>
            </div>

            <div class="grid grid-cols-2 gap-2 mt-3">
              <label class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[11px] font-semibold text-slate-600">
                <input
                  type="checkbox"
                  :checked="row.include_in_total"
                  class="h-4 w-4 rounded border-slate-300 text-indigo-600"
                  @change="updateReportCell(row.id, 'include_in_total', eventChecked($event))"
                />
                {{ $t('project.count_total') }}
              </label>
              <label class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-[11px] font-semibold text-slate-600">
                <input
                  type="checkbox"
                  :checked="row.selected_for_purchase"
                  class="h-4 w-4 rounded border-slate-300 text-indigo-600"
                  @change="updateReportCell(row.id, 'selected_for_purchase', eventChecked($event))"
                />
                {{ $t('project.buy') }}
              </label>
            </div>
          </div>
        </div>

        <div class="mt-3 rounded-2xl bg-slate-50 p-3">
          <p class="text-[11px] font-semibold text-slate-500 mb-2">{{ $t('project.chat_edit_report') }}</p>
          <textarea
            v-model="reportChatInput"
            rows="2"
            class="input-field text-xs"
            :placeholder="$t('project.chat_edit_placeholder')"
          ></textarea>
          <button
            @click="createReportPatch"
            :disabled="reportBusy || !reportChatInput.trim()"
            class="mt-2 w-full rounded-xl bg-indigo-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-40"
          >
            {{ $t('project.preview_patch') }}
          </button>

          <div v-if="pendingReportPatch" class="mt-3 rounded-xl border border-indigo-100 bg-white p-3">
            <p class="text-[11px] font-bold text-slate-700">{{ $t('project.patch_preview') }}</p>
            <pre class="mt-1 max-h-36 overflow-auto whitespace-pre-wrap text-[11px] text-slate-500">{{ JSON.stringify(pendingReportPatch.patch_jsonb, null, 2) }}</pre>
            <div class="mt-2 flex gap-2">
              <button @click="applyReportPatch" :disabled="reportBusy" class="flex-1 rounded-xl bg-green-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-40">{{ $t('project.apply') }}</button>
              <button @click="rejectReportPatch" :disabled="reportBusy" class="flex-1 rounded-xl bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-600 disabled:opacity-40">{{ $t('project.reject') }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Line Items -->
      <div v-if="lineItems.length > 0" class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-bold text-slate-900">📦 {{ $t('project.line_items') }} ({{ lineItems.length }})</h3>
          <div class="flex gap-1">
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-semibold">{{ confirmedCount }} ✓</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">{{ draftCount }} {{ $t('project.draft') }}</span>
          </div>
        </div>

        <div
          v-for="item in lineItems"
          :key="item.id"
          class="card"
          :class="[item.status === 'CONFIRMED' ? 'border-green-200 bg-green-50/30' : '', item.include_in_estimate === false ? 'opacity-70' : '']"
        >
          <div class="flex items-start justify-between gap-2 mb-1.5">
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-slate-900">{{ item.name }}</h4>
              <p v-if="item.category_hint" class="text-[10px] text-slate-400 mt-0.5">{{ item.category_hint }}</p>
              <p class="text-[10px] mt-1" :class="matchedSamplesForItem(item.id).length ? 'text-green-600' : 'text-amber-600'">
                {{ matchedSamplesForItem(item.id).length ? `${matchedSamplesForItem(item.id).length} ${$t('project.matched_products')}` : $t('project.unmatched_placeholder') }}
              </p>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <span v-if="item.source === 'AI'" class="text-[9px] px-1.5 py-0.5 rounded-full bg-primary-100 text-primary-700 font-semibold">AI</span>
              <span v-if="item.confidence" class="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 font-semibold">
                {{ (item.confidence * 100).toFixed(0) }}%
              </span>
            </div>
          </div>

          <div class="flex items-center gap-3 text-xs text-slate-500">
            <span>{{ item.qty }} {{ item.unit }}</span>
            <span v-if="item.estimated_unit_price">₱{{ item.estimated_unit_price?.toLocaleString() }}/{{ item.unit }}</span>
            <span v-if="item.estimated_total_price" class="font-semibold text-slate-700">₱{{ item.estimated_total_price?.toLocaleString() }}</span>
          </div>

          <button
            @click="toggleIncludeInEstimate(item)"
            class="mt-2 w-full rounded-xl border px-3 py-2 text-xs font-semibold"
            :class="item.include_in_estimate !== false ? 'border-green-200 bg-green-50 text-green-700' : 'border-slate-200 bg-slate-50 text-slate-500'"
          >
            {{ item.include_in_estimate !== false ? `✓ ${$t('project.included_total')}` : $t('project.excluded_total') }}
          </button>

          <!-- Multi-tier pricing -->
          <div v-if="item.price_tiers_jsonb" class="grid grid-cols-3 gap-1.5 mt-2">
            <div
              v-for="tier in ['BUDGET', 'MID_RANGE', 'PREMIUM']"
              :key="tier"
              class="rounded-lg px-2 py-1.5 text-center"
              :class="{
                'bg-green-50 border border-green-200': tier === 'BUDGET',
                'bg-blue-50 border border-blue-200': tier === 'MID_RANGE',
                'bg-purple-50 border border-purple-200': tier === 'PREMIUM',
                'ring-2 ring-offset-1': tier === item.quality_tier,
                'ring-green-400': tier === item.quality_tier && tier === 'BUDGET',
                'ring-blue-400': tier === item.quality_tier && tier === 'MID_RANGE',
                'ring-purple-400': tier === item.quality_tier && tier === 'PREMIUM',
              }"
            >
              <p class="text-[9px] font-bold uppercase"
                :class="{
                  'text-green-600': tier === 'BUDGET',
                  'text-blue-600': tier === 'MID_RANGE',
                  'text-purple-600': tier === 'PREMIUM',
                }"
              >{{ tier === 'MID_RANGE' ? 'Mid' : tier === 'BUDGET' ? '💰' : '👑' }}</p>
              <p class="text-[11px] font-bold text-slate-800">₱{{ (item.price_tiers_jsonb[tier]?.total_price || 0).toLocaleString() }}</p>
            </div>
          </div>

          <p v-if="item.sourcing_notes" class="text-[11px] text-slate-400 mt-1.5 line-clamp-2">{{ item.sourcing_notes }}</p>

          <!-- Actions -->
          <div class="flex gap-2 mt-3">
            <button
              v-if="item.status === 'DRAFT'"
              @click="confirmItem(item)"
              class="flex-1 text-center text-xs font-semibold px-3 py-2 rounded-xl bg-green-500 text-white active:bg-green-600"
            >✓ {{ $t('project.confirm') }}</button>
            <button
              v-if="item.status === 'CONFIRMED'"
              @click="unconfirmItem(item)"
              class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-xl bg-slate-100 text-slate-600 active:bg-slate-200"
            >{{ $t('project.undo') }}</button>
            <button
              @click="removeItem(item.id)"
              class="text-xs font-medium px-3 py-2 rounded-xl bg-red-50 text-red-500 active:bg-red-100"
            >{{ $t('project.remove') }}</button>
          </div>
        </div>
      </div>

      <!-- Comparison -->
      <div v-if="comparisonItems.length > 0" class="card border-blue-100">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-xs font-semibold text-blue-700 uppercase tracking-wide">📊 {{ $t('project.price_comparison') }}</h3>
          <button @click="refreshPriceEstimate" :disabled="estimatingPrices" class="text-[11px] text-blue-600 font-semibold disabled:opacity-40">{{ $t('project.recalc') }}</button>
        </div>
        <div v-for="row in comparisonItems" :key="row.line_item.id" class="border-t border-slate-100 py-2 first:border-t-0">
          <div class="flex justify-between gap-2">
            <p class="text-xs font-semibold text-slate-800">{{ row.line_item.name }}</p>
            <span class="text-[10px] text-slate-400">{{ row.price_snapshot.sample_count }} {{ $t('project.samples') }}</span>
          </div>
          <div class="grid grid-cols-3 gap-1.5 mt-2">
            <div v-for="tier in ['BUDGET', 'MID_RANGE', 'PREMIUM']" :key="tier" class="rounded-lg bg-slate-50 p-1.5 text-center">
              <p class="text-[9px] font-bold text-slate-500">{{ tier === 'MID_RANGE' ? 'MID' : tier }}</p>
              <p class="text-[11px] font-bold text-slate-800">₱{{ (row.line_item.price_tiers?.[tier]?.total_price || 0).toLocaleString() }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Risk Notes -->
      <div v-if="project.risk_notes_jsonb?.length" class="card border-amber-100">
        <h3 class="text-xs font-semibold text-amber-700 mb-2">⚡ {{ $t('project.risk_notes') }}</h3>
        <ul class="space-y-1">
          <li v-for="(note, i) in project.risk_notes_jsonb" :key="i" class="text-xs text-amber-600">• {{ note }}</li>
        </ul>
      </div>
    </div>

    <!-- Bottom Actions -->
    <div v-if="project && !loading" class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-100 px-4 py-3 z-40 flex gap-3" style="padding-bottom: max(12px, var(--safe-area-bottom))">
      <button
        v-if="canAnalyze"
        @click="startAnalysis"
        :disabled="analyzing"
        class="flex-1 py-3 rounded-xl text-sm font-semibold bg-primary-600 text-white active:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <svg v-if="analyzing" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M4 12a8 8 0 018-8" /></svg>
        🤖 {{ analyzing ? $t('project.analyzing') : $t('project.ai_analyze') }}
      </button>
      <button
        v-if="canPublish"
        @click="publishProject"
        :disabled="publishing"
        class="flex-1 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white active:bg-green-700 disabled:opacity-50"
      >
        🚀 {{ $t('project.publish_items', { count: publishableCount }) }}
      </button>
      <button
        v-if="lineItems.length > 0 && canAnalyze"
        @click="freezeForm"
        :disabled="freezingForm"
        class="flex-1 py-3 rounded-xl text-sm font-semibold bg-amber-100 text-amber-700 active:bg-amber-200 disabled:opacity-50"
      >
        🔒 {{ $t('project.freeze') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

definePageMeta({ layout: 'buyer', middleware: ['buyer'] })
const { t } = useI18n({ useScope: 'global' })
useHead({ title: t('project.detail_title') })

const route = useRoute()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const projectId = route.params.id as string

const loading = ref(true)
const analyzing = ref(false)
const publishing = ref(false)
const uploading = ref(false)
const sendingMessage = ref(false)
const estimatingPrices = ref(false)
const freezingForm = ref(false)
const project = ref<any>(null)
const aiRun = ref<any>(null)
const lineItems = ref<any[]>([])
const messages = ref<any[]>([])
const metrics = ref<any>(null)
const comparisonItems = ref<any[]>([])
const chatInput = ref('')
const report = ref<any>(null)
const reportVersions = ref<any[]>([])
const reportBusy = ref(false)
const reportChatInput = ref('')
const pendingReportPatch = ref<any>(null)

const headers = computed(() => ({ Authorization: `Bearer ${authStore.accessToken}` }))
const confirmedCount = computed(() => lineItems.value.filter(i => i.status === 'CONFIRMED').length)
const draftCount = computed(() => lineItems.value.filter(i => i.status === 'DRAFT').length)
const publishableCount = computed(() => lineItems.value.filter(i => i.status === 'CONFIRMED' && i.include_in_estimate !== false).length)
const canAnalyze = computed(() => project.value && ['DRAFT', 'COLLECTING_INFO', 'AI_ANALYZED'].includes(project.value.status))
const canPublish = computed(() => project.value && publishableCount.value > 0 && ['AI_ANALYZED', 'READY_FOR_SOURCING'].includes(project.value.status))
const forgeStages = computed(() => {
  const hasMessages = messages.value.length > 0 || Boolean(project.value?.description)
  const hasMetrics = Boolean(metrics.value?.values?.length) && !(metrics.value?.missing_required?.length)
  const hasFiles = Boolean(project.value?.files?.length)
  const hasItems = lineItems.value.length > 0
  const hasComparison = comparisonItems.value.length > 0
  const frozen = ['READY_FOR_SOURCING', 'SOURCING', 'ORDERING', 'COMPLETED'].includes(project.value?.status)
  return [
    { key: 'collect', label: t('project.stage.collect'), done: hasMessages, active: !hasMessages },
    { key: 'metrics', label: t('project.stage.metrics'), done: hasMetrics, active: hasMessages && !hasMetrics },
    { key: 'files', label: t('project.stage.files'), done: hasFiles, active: hasMetrics && !hasFiles },
    { key: 'items', label: t('project.stage.items'), done: hasItems, active: (hasFiles || hasMetrics) && !hasItems },
    { key: 'quote', label: t('project.stage.quote'), done: hasComparison, active: hasItems && !hasComparison },
    { key: 'freeze', label: t('project.stage.freeze'), done: frozen, active: hasComparison && !frozen },
  ].map(stage => ({ ...stage, status: stage.done ? 'done' : stage.active ? 'active' : 'pending' }))
})
const forgeProgress = computed(() => Math.round((forgeStages.value.filter(s => s.status === 'done').length / forgeStages.value.length) * 100))
const reportTotalCards = computed(() => {
  const totals = report.value?.current_version?.totals_jsonb || {}
  return [
    { key: 'selected', label: t('project.selected'), value: Number(totals.selected_total || 0) },
    { key: 'budget', label: t('project.quality_option.BUDGET'), value: Number(totals.BUDGET || 0) },
    { key: 'mid', label: t('project.quality_option.MID_RANGE'), value: Number(totals.MID_RANGE || 0) },
    { key: 'premium', label: t('project.quality_option.PREMIUM'), value: Number(totals.PREMIUM || 0) },
    { key: 'excluded', label: t('project.excluded'), value: Number(totals.excluded_total || 0) },
    { key: 'unmatched', label: t('project.unmatched'), value: Number(totals.unmatched_total || 0) },
  ]
})
const showReportSheet = computed(() => {
  const status = project.value?.status
  return Boolean(report.value) && (
    lineItems.value.length > 0 ||
    (report.value?.rows?.length || 0) > 0 ||
    ['AI_ANALYZED', 'READY_FOR_SOURCING', 'SOURCING', 'ORDERING', 'COMPLETED'].includes(status)
  )
})

const aiStatusBadge = computed(() => {
  const m: Record<string, string> = { PENDING: 'badge-gray', RUNNING: 'badge-primary', SUCCESS: 'badge-success', FAILED: 'badge-danger' }
  return m[aiRun.value?.status] || 'badge-gray'
})
const normalizedAiError = computed(() => {
  const message = aiRun.value?.error_message || 'Analysis failed.'
  if (message.includes('OPENAI_API_KEY') || message.includes('backend/.env')) {
    return t('project.provider_missing')
  }
  return message
})

function typeIcon(type: string) {
  return { CONSTRUCTION: '🏗️', SOLAR: '☀️', TECH_BUILD: '💻', RENOVATION: '🔨', GENERAL: '📦' }[type] || '📦'
}

function badgeClass(status: string) {
  return { DRAFT: 'badge-gray', ANALYZING: 'badge-warning', AI_ANALYZED: 'badge-success', SOURCING: 'badge-primary' }[status] || 'badge-gray'
}

function statusLabel(status: string) {
  return t(`project.status.${status}`)
}

function fileIcon(ct: string) {
  if (ct.startsWith('image/')) return '🖼️'
  if (ct.includes('pdf')) return '📄'
  if (ct.includes('word') || ct.includes('docx')) return '📝'
  return '📃'
}

function comparisonForItem(itemId: string) {
  return comparisonItems.value.find(row => row.line_item?.id === itemId)
}

function matchedSamplesForItem(itemId: string) {
  const row = comparisonForItem(itemId)
  return row?.price_snapshot?.samples || row?.suppliers || []
}

async function loadProject() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}`, { headers: headers.value })
    project.value = data
    lineItems.value = (data.line_items || []).filter((i: any) => i.status !== 'REMOVED')
    aiRun.value = data.latest_ai_run
    await Promise.all([loadConversationData(), loadComparison(), loadReport()])
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function loadConversationData() {
  try {
    const [msgs, metricData] = await Promise.all([
      $fetch<any[]>(`${config.public.apiBase}/buyer/projects/${projectId}/messages`, { headers: headers.value }),
      $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/metrics`, { headers: headers.value }),
    ])
    messages.value = msgs || []
    metrics.value = metricData
  } catch (e) { console.error(e) }
}

async function loadComparison() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/comparison`, { headers: headers.value })
    comparisonItems.value = data.items || []
  } catch { comparisonItems.value = [] }
}

async function loadReport() {
  try {
    const [reportData, versions] = await Promise.all([
      $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/report`, { headers: headers.value }),
      $fetch<any[]>(`${config.public.apiBase}/buyer/projects/${projectId}/report/versions`, { headers: headers.value }),
    ])
    report.value = reportData
    reportVersions.value = versions || []
  } catch (e) {
    console.error(e)
    report.value = null
    reportVersions.value = []
  }
}

function metricDisplay(value: any) {
  if (!value) return '-'
  if (typeof value.value !== 'undefined') return String(value.value)
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

async function sendMessage() {
  const content = chatInput.value.trim()
  if (!content) return
  sendingMessage.value = true
  try {
    const created = await $fetch<any[]>(`${config.public.apiBase}/buyer/projects/${projectId}/messages`, {
      method: 'POST',
      headers: headers.value,
      body: { content, file_ids: [] },
    })
    messages.value.push(...created)
    chatInput.value = ''
    await loadConversationData()
  } catch (e) { console.error(e) }
  finally { sendingMessage.value = false }
}

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  uploading.value = true
  for (const file of Array.from(input.files)) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/files`, {
        method: 'POST', headers: headers.value, body: formData,
      })
    } catch (e: any) { console.error(e) }
  }
  input.value = ''
  uploading.value = false
  await loadProject()
}

async function deleteFile(fileId: string) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/files/${fileId}`, { method: 'DELETE', headers: headers.value })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function startAnalysis() {
  analyzing.value = true
  try {
    const run = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/ai/analyze`, { method: 'POST', headers: headers.value })
    aiRun.value = run
    pollAnalysis(run.id)
  } catch (e: any) {
    console.error(e)
    analyzing.value = false
  }
}

async function retryAnalysis() {
  if (!aiRun.value) return
  analyzing.value = true
  try {
    const run = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/ai-runs/${aiRun.value.id}/retry`, { method: 'POST', headers: headers.value })
    aiRun.value = run
    pollAnalysis(run.id)
  } catch (e: any) {
    console.error(e)
    analyzing.value = false
  }
}

async function pollAnalysis(runId: string) {
  let attempts = 0
  const interval = setInterval(async () => {
    attempts++
    try {
      const run = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/ai-runs/${runId}`, { headers: headers.value })
      aiRun.value = run
      if (['SUCCESS', 'FAILED'].includes(run.status)) {
        clearInterval(interval)
        analyzing.value = false
        await loadProject()
        if (run.status === 'SUCCESS') await refreshPriceEstimate(false)
      }
    } catch { if (attempts > 30) { clearInterval(interval); analyzing.value = false } }
  }, 3000)
}

async function confirmItem(item: any) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${item.id}`, { method: 'PATCH', headers: headers.value, body: { status: 'CONFIRMED' } })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function unconfirmItem(item: any) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${item.id}`, { method: 'PATCH', headers: headers.value, body: { status: 'DRAFT' } })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function toggleIncludeInEstimate(item: any) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${item.id}`, {
      method: 'PATCH',
      headers: headers.value,
      body: { include_in_estimate: item.include_in_estimate === false },
    })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function removeItem(itemId: string) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${itemId}`, { method: 'DELETE', headers: headers.value })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function publishProject() {
  publishing.value = true
  try {
    const result = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/publish`, { method: 'POST', headers: headers.value })
    await loadProject()
    if (result.published_count > 0) {
      alert(`✅ ${t('project.published_items', { count: result.published_count })}`)
    }
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_publish'))
  } finally { publishing.value = false }
}

async function freezeForm() {
  freezingForm.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/freeze-form`, { method: 'POST', headers: headers.value })
    await loadProject()
  } catch (e: any) { alert(e?.data?.detail || t('project.failed_freeze')) }
  finally { freezingForm.value = false }
}

async function refreshPriceEstimate(showAlert = true) {
  estimatingPrices.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/price-estimate`, { method: 'POST', headers: headers.value })
    await loadProject()
    await loadComparison()
    if (showAlert) alert(t('project.prices_refreshed'))
  } catch (e: any) {
    if (showAlert) alert(e?.data?.detail || t('project.failed_refresh_prices'))
  } finally { estimatingPrices.value = false }
}

function reportTierTotal(row: any, tier: string) {
  return Number(row?.price_tiers_jsonb?.[tier]?.total_price || row?.price_tiers_jsonb?.[tier]?.estimated_total || 0)
}

function eventValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value
}

function eventNumber(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  return Number.isFinite(value) ? value : 0
}

function eventChecked(event: Event) {
  return (event.target as HTMLInputElement).checked
}

async function updateReportCell(rowId: string, field: string, value: any) {
  if (!report.value?.current_version?.id) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/cells`, {
      method: 'PATCH',
      headers: headers.value,
      body: { changes: [{ row_id: rowId, field, value }], message: `Update ${field}` },
    })
    await loadReport()
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_update_report'))
  } finally {
    reportBusy.value = false
  }
}

async function recalculateReport() {
  if (!report.value?.current_version?.id) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/recalculate`, {
      method: 'POST',
      headers: headers.value,
    })
    await Promise.all([loadReport(), loadComparison()])
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_reestimate_report'))
  } finally {
    reportBusy.value = false
  }
}

async function freezeReport() {
  if (!report.value?.current_version?.id) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/freeze`, {
      method: 'POST',
      headers: headers.value,
    })
    await loadReport()
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_freeze_report'))
  } finally {
    reportBusy.value = false
  }
}

async function createReportPatch() {
  const instruction = reportChatInput.value.trim()
  if (!instruction || !report.value?.current_version?.id) return
  reportBusy.value = true
  try {
    pendingReportPatch.value = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/report/chat`, {
      method: 'POST',
      headers: headers.value,
      body: { message: instruction },
    })
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_patch_preview'))
  } finally {
    reportBusy.value = false
  }
}

async function applyReportPatch() {
  if (!pendingReportPatch.value?.id) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/patches/${pendingReportPatch.value.id}/apply`, {
      method: 'POST',
      headers: headers.value,
    })
    pendingReportPatch.value = null
    reportChatInput.value = ''
    await loadReport()
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_apply_patch'))
  } finally {
    reportBusy.value = false
  }
}

async function rejectReportPatch() {
  if (!pendingReportPatch.value?.id) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/patches/${pendingReportPatch.value.id}/reject`, {
      method: 'POST',
      headers: headers.value,
    })
    pendingReportPatch.value = null
  } catch (e: any) {
    alert(e?.data?.detail || t('project.failed_reject_patch'))
  } finally {
    reportBusy.value = false
  }
}

onMounted(loadProject)
</script>
