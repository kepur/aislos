<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <UButton variant="ghost" color="gray" icon="i-heroicons-arrow-left" to="/buyer/projects" />
      <div class="flex-1 min-w-0">
        <h1 class="text-xl font-bold text-slate-900 truncate flex items-center gap-2">
          <span class="text-xl">{{ projectTypeIcon(project?.project_type) }}</span>
          {{ project?.title || tt('project.loading') }}
        </h1>
        <div class="flex items-center gap-2 mt-0.5">
          <UBadge v-if="project" :color="statusColor(project.status)" variant="subtle" size="xs">
            {{ projectStatusLabel(project.status) }}
          </UBadge>
          <span v-if="project?.country" class="text-xs text-slate-400 flex items-center gap-1">
            <UIcon name="i-heroicons-map-pin" class="w-3 h-3" />
            {{ [project.city, project.country].filter(Boolean).join(', ') }}
          </span>
        </div>
      </div>
      <UButton
        v-if="canAnalyze"
        color="indigo"
        icon="i-heroicons-sparkles"
        :loading="analyzing"
        @click="startAnalysis"
      >
        {{ tt('project.aiAnalyze') }}
      </UButton>
      <UButton
        v-if="lineItems.length > 0"
        color="blue"
        variant="soft"
        icon="i-heroicons-chart-bar"
        :loading="estimatingPrices"
        @click="refreshPriceEstimate"
      >
        {{ tt('project.refreshPrices') }}
      </UButton>
      <UButton
        v-if="lineItems.length > 0 && canEdit"
        color="amber"
        variant="soft"
        icon="i-heroicons-lock-closed"
        :loading="freezingForm"
        @click="freezeForm"
      >
        {{ tt('project.freezeForm') }}
      </UButton>
      <UButton
        v-if="canPublish"
        color="green"
        icon="i-heroicons-rocket-launch"
        :loading="publishing"
        @click="publishProject"
      >
        {{ tt('project.publishItems', { count: publishableCount }) }}
      </UButton>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="bg-white rounded-2xl border p-12 text-center">
      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
      <p class="text-sm text-slate-400 mt-3">{{ tt('project.loadingProject') }}</p>
    </div>

    <template v-if="project && !loading">
      <!-- Idea Forge style workbench -->
      <section class="forge-shell">
        <div class="forge-hero">
          <div class="min-w-0">
            <div class="flex items-center gap-3">
              <span class="text-4xl">💡</span>
              <div class="min-w-0">
                <p class="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700">{{ tt('project.forge') }}</p>
                <h2 class="text-3xl font-black text-slate-950 truncate">{{ project.title }}</h2>
              </div>
            </div>
            <p class="mt-3 max-w-3xl text-sm text-slate-600">
              {{ tt('project.forgeDesc') }}
            </p>
          </div>
          <div class="forge-score">
            <span class="text-xs text-slate-500">{{ tt('project.progress') }}</span>
            <strong>{{ forgeProgress }}%</strong>
          </div>
        </div>

        <div class="forge-stagebar">
          <div
            v-for="stage in forgeStages"
            :key="stage.key"
            class="forge-stage"
            :class="stage.status"
          >
            <span class="stage-light"></span>
            <span class="stage-index">{{ stage.index }}</span>
            <span class="stage-label">{{ stage.label }}</span>
            <small>{{ stage.sub }}</small>
          </div>
          <div class="ml-auto flex items-center gap-4 text-sm text-slate-500">
            <span>📊 {{ forgeProgress }}%</span>
            <span>⚠️ {{ issueCount }} gaps</span>
            <span>📦 {{ lineItems.length }} items</span>
          </div>
        </div>

        <div class="forge-grid">
          <div class="forge-chat-panel">
            <div class="forge-panel-head">
              <div>
                <p class="text-xs font-bold uppercase tracking-wide text-indigo-600">{{ tt('project.langgraphIntake') }}</p>
                <h3 class="text-xl font-black text-slate-950">{{ tt('project.collectStep') }}</h3>
              </div>
              <div class="flex items-center gap-2">
                <UButton size="xs" color="gray" variant="soft" icon="i-heroicons-arrow-path" @click="loadConversationData">
                  {{ tt('project.refresh') }}
                </UButton>
                <UButton size="xs" color="indigo" variant="soft" icon="i-heroicons-sparkles" :loading="analyzing" @click="startAnalysis">
                  {{ tt('project.aiAnalyze') }}
                </UButton>
              </div>
            </div>

            <div class="forge-chat-canvas">
              <div v-if="messages.length === 0" class="forge-empty-chat">
                <p class="text-lg font-black text-slate-900">{{ tt('project.chatGoalTitle') }}</p>
                <p class="mt-1 text-sm text-slate-500">
                  {{ tt('project.chatGoalExample') }}
                </p>
                <div class="mt-4 flex flex-wrap gap-2">
                  <button
                    v-for="sample in samplePrompts"
                    :key="sample"
                    class="rounded-full border border-indigo-100 bg-white px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:border-indigo-300"
                    @click="chatInput = sample"
                  >
                    {{ sample }}
                  </button>
                </div>
              </div>
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="forge-message"
                :class="msg.role === 'USER' ? 'user' : msg.role === 'SYSTEM' ? 'system' : 'assistant'"
              >
                <div class="forge-message-bubble">
                  <p class="whitespace-pre-wrap">{{ msg.content }}</p>
                  <p v-if="msg.workflow_node" class="mt-2 text-[10px] opacity-60">{{ msg.workflow_node }}</p>
                </div>
              </div>
            </div>

            <div class="forge-composer">
              <UTextarea
                v-model="chatInput"
                :rows="3"
                class="flex-1"
                :placeholder="tt('project.chatPlaceholder')"
                @keydown.ctrl.enter.prevent="sendMessage"
              />
              <input ref="fileInput" type="file" multiple accept=".pdf,.txt,.docx,.doc,.jpg,.jpeg,.png,.webp" class="hidden" @change="handleFileSelect" />
              <div class="flex flex-col gap-2">
                <UButton color="gray" variant="soft" icon="i-heroicons-paper-clip" @click="fileInput?.click()">
                  {{ tt('project.attachFiles') }}
                </UButton>
                <UButton color="indigo" :loading="sendingMessage" :disabled="!chatInput.trim()" icon="i-heroicons-paper-airplane" @click="sendMessage">
                  {{ tt('project.send') }}
                </UButton>
                <UButton color="emerald" variant="soft" :loading="analyzing" icon="i-heroicons-arrow-right-circle" @click="startAnalysis">
                  {{ tt('project.proceed') }}
                </UButton>
              </div>
            </div>
            <div v-if="project.files?.length || uploading" class="mt-3 flex flex-wrap gap-2">
              <span v-if="uploading" class="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                <UIcon name="i-heroicons-arrow-path" class="w-3 h-3 animate-spin" />
                {{ tt('project.uploading') }}
              </span>
              <span
                v-for="f in project.files || []"
                :key="f.id"
                class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600"
              >
                {{ fileIcon(f.content_type) }} {{ f.file_name }}
                <button class="text-red-400 hover:text-red-600" @click.stop="deleteFile(f.id)">×</button>
              </span>
            </div>
            <p v-if="chatError" class="mt-3 rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-600">
              {{ chatError }}
            </p>
          </div>

          <aside class="forge-preview">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-black text-slate-950">📋 Project Preview</h3>
              <UBadge color="emerald" variant="subtle">{{ forgeProgress }}% complete</UBadge>
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="card in previewCards"
                :key="card.key"
                class="preview-card"
                :class="card.status"
              >
                <div class="flex min-w-0 flex-1 items-center gap-3">
                  <span class="preview-light"></span>
                  <span class="text-2xl">{{ card.icon }}</span>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-black text-slate-900">{{ card.title }}</p>
                    <p class="text-xs text-slate-500 truncate">{{ card.text }}</p>
                  </div>
                </div>
                <span class="preview-pill">{{ statusLabel(card.status) }}</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <!-- Project Info Card -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left: Project Details -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Description -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-slate-700">📋 Project Description</h3>
                <UButton v-if="canEdit" variant="ghost" size="xs" color="gray" icon="i-heroicons-pencil" @click="showEditDesc = !showEditDesc" />
              </div>
            </template>
            <div v-if="!showEditDesc">
              <p class="text-sm text-slate-600 whitespace-pre-wrap">{{ project.description || 'No description provided.' }}</p>
            </div>
            <div v-else class="space-y-3">
              <UTextarea v-model="editDesc" :rows="4" />
              <div class="flex gap-2 justify-end">
                <UButton variant="ghost" size="sm" @click="showEditDesc = false">Cancel</UButton>
                <UButton color="indigo" size="sm" :loading="saving" @click="saveDescription">Save</UButton>
              </div>
            </div>
          </UCard>

          <!-- AI Analysis Status -->
          <UCard v-if="aiRun" class="border-l-4" :class="aiRunBorderClass">
            <template #header>
              <h3 class="text-sm font-semibold text-slate-700 flex items-center gap-2">
                🤖 AI Analysis
                <UBadge :color="aiRunStatusColor" variant="subtle" size="xs">
                  {{ aiRun.status }}
                </UBadge>
              </h3>
            </template>
            <div v-if="isAiRunStale" class="space-y-3">
              <p class="text-sm text-amber-700">
                The previous AI analysis was interrupted or timed out. Start a fresh analysis with the current Admin AI Provider settings.
              </p>
              <UButton size="sm" color="amber" variant="soft" icon="i-heroicons-arrow-path" :loading="analyzing" @click="startAnalysis">
                Start New Analysis
              </UButton>
            </div>
            <div v-else-if="aiRun.status === 'RUNNING' || aiRun.status === 'PENDING'" class="flex items-center gap-3">
              <UIcon name="i-heroicons-arrow-path" class="w-5 h-5 text-indigo-500 animate-spin" />
              <p class="text-sm text-slate-600">AI is analyzing your project... This may take 30-60 seconds.</p>
            </div>
            <div v-else-if="aiRun.status === 'FAILED'" class="space-y-3">
              <p class="text-sm text-red-600">{{ normalizedAiError }}</p>
              <UButton size="sm" color="red" variant="soft" icon="i-heroicons-arrow-path" :loading="analyzing" @click="retryAnalysis">
                Retry Analysis
              </UButton>
            </div>
          </UCard>

          <!-- AI Summary -->
          <UCard v-if="project.ai_summary" class="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-100">
            <template #header>
              <h3 class="text-sm font-semibold text-indigo-700 flex items-center gap-2">
                <UIcon name="i-heroicons-sparkles" class="w-4 h-4" />
                AI Summary
              </h3>
            </template>
            <p class="text-sm text-slate-700 whitespace-pre-wrap">{{ project.ai_summary }}</p>
            <div v-if="project.missing_questions_jsonb?.length" class="mt-4">
              <h4 class="text-xs font-semibold text-amber-700 mb-2">⚠️ Missing Information</h4>
              <ul class="space-y-1">
                <li v-for="q in project.missing_questions_jsonb" :key="q.key" class="text-xs text-amber-600 flex items-start gap-2">
                  <UBadge :color="q.importance === 'HIGH' ? 'red' : q.importance === 'MEDIUM' ? 'yellow' : 'gray'" variant="subtle" size="xs">
                    {{ q.importance }}
                  </UBadge>
                  {{ q.question }}
                </li>
              </ul>
            </div>
          </UCard>

          <!-- Versioned Report Sheet -->
          <UCard v-if="showReportSheet" class="border-emerald-100">
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="text-sm font-semibold text-emerald-700 flex items-center gap-2">
                    <UIcon name="i-heroicons-table-cells" class="w-4 h-4" />
                    Versioned Quote Report Sheet
                  </h3>
                  <p class="text-xs text-slate-400 mt-0.5">
                    v{{ report.current_version?.version_number || 1 }} · {{ report.current_version?.status || 'DRAFT' }} · Excel-like editable estimate
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <select v-model="selectedReportVersionId" class="rounded-lg border border-slate-200 px-2 py-1 text-xs" @change="restoreReportVersion">
                    <option value="">Current version</option>
                    <option v-for="v in reportVersions" :key="v.id" :value="v.id">
                      v{{ v.version_number }} · {{ v.status }}
                    </option>
                  </select>
                  <UButton size="xs" color="gray" variant="soft" @click="addReportColumn">Add Column</UButton>
                  <UButton size="xs" color="gray" variant="soft" @click="addReportRow">Add Row</UButton>
                  <UButton size="xs" color="blue" variant="soft" :loading="reportBusy" @click="recalculateReport">Re-estimate</UButton>
                  <UButton size="xs" color="emerald" variant="soft" :loading="reportBusy" @click="freezeReport">Freeze</UButton>
                </div>
              </div>
            </template>

            <div class="space-y-4">
              <div class="grid grid-cols-2 md:grid-cols-6 gap-2">
                <div v-for="card in reportTotalCards" :key="card.key" class="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <p class="text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ card.label }}</p>
                  <p class="mt-1 text-sm font-black text-slate-900">{{ card.value }}</p>
                </div>
              </div>

              <div class="rounded-2xl border border-slate-200 overflow-x-auto">
                <table class="min-w-[1120px] w-full text-xs">
                  <thead class="bg-slate-50 text-slate-500">
                    <tr>
                      <th class="px-3 py-2 text-left">Item</th>
                      <th class="px-3 py-2 text-left">Qty</th>
                      <th class="px-3 py-2 text-left">Unit</th>
                      <th class="px-3 py-2 text-left">Tier</th>
                      <th class="px-3 py-2 text-right">Budget</th>
                      <th class="px-3 py-2 text-right">Mid</th>
                      <th class="px-3 py-2 text-right">Premium</th>
                      <th class="px-3 py-2 text-center">Total</th>
                      <th class="px-3 py-2 text-center">Buy</th>
                      <th class="px-3 py-2 text-left">Match</th>
                      <th v-for="col in customReportColumns" :key="col.id" class="px-3 py-2 text-left">{{ col.label }}</th>
                      <th class="px-3 py-2 text-left">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in report.rows" :key="row.id" class="border-t border-slate-100">
                      <td class="px-3 py-2">
                        <input class="report-cell min-w-[180px]" :value="row.name" @change="updateReportCell(row.id, 'name', eventValue($event))" />
                      </td>
                      <td class="px-3 py-2">
                        <input class="report-cell w-20" type="number" :value="row.qty" @change="updateReportCell(row.id, 'qty', eventNumber($event))" />
                      </td>
                      <td class="px-3 py-2">
                        <input class="report-cell w-20" :value="row.unit" @change="updateReportCell(row.id, 'unit', eventValue($event))" />
                      </td>
                      <td class="px-3 py-2">
                        <select class="report-cell w-28" :value="row.selected_tier" @change="updateReportCell(row.id, 'selected_tier', eventValue($event))">
                          <option value="BUDGET">Budget</option>
                          <option value="MID_RANGE">Mid</option>
                          <option value="PREMIUM">Premium</option>
                        </select>
                      </td>
                      <td class="px-3 py-2 text-right">₱{{ reportTierTotal(row, 'BUDGET').toLocaleString() }}</td>
                      <td class="px-3 py-2 text-right">₱{{ reportTierTotal(row, 'MID_RANGE').toLocaleString() }}</td>
                      <td class="px-3 py-2 text-right">₱{{ reportTierTotal(row, 'PREMIUM').toLocaleString() }}</td>
                      <td class="px-3 py-2 text-center">
                        <input type="checkbox" :checked="row.include_in_total" @change="updateReportCell(row.id, 'include_in_total', eventChecked($event))" />
                      </td>
                      <td class="px-3 py-2 text-center">
                        <input type="checkbox" :checked="row.selected_for_purchase" @change="updateReportCell(row.id, 'selected_for_purchase', eventChecked($event))" />
                      </td>
                      <td class="px-3 py-2">
                        <UBadge :color="row.match_status === 'MATCHED' ? 'green' : 'amber'" variant="subtle" size="xs">
                          {{ row.match_status }}
                        </UBadge>
                      </td>
                      <td v-for="col in customReportColumns" :key="`${row.id}-${col.key}`" class="px-3 py-2">
                        <input class="report-cell min-w-[120px]" :value="row.custom_values_jsonb?.[col.key] || ''" @change="updateReportCell(row.id, col.key, eventValue($event))" />
                      </td>
                      <td class="px-3 py-2">
                        <input class="report-cell min-w-[180px]" :value="row.notes || ''" @change="updateReportCell(row.id, 'notes', eventValue($event))" />
                      </td>
                    </tr>
                    <tr v-if="!report.rows?.length">
                      <td colspan="12" class="px-3 py-8 text-center text-slate-400">No report rows yet. Run AI analysis or add a row manually.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4">
                <div class="flex gap-2">
                  <UTextarea v-model="reportChatInput" :rows="2" class="flex-1" placeholder="Example: add a brand preference column / exclude cement from totals / set PVC quantity to 200 m" />
                  <UButton color="indigo" :loading="reportBusy" @click="createReportPatch">Preview Patch</UButton>
                </div>
                <div v-if="pendingReportPatch" class="mt-3 rounded-xl border border-indigo-200 bg-white p-3">
                  <p class="text-xs font-bold text-indigo-700">Patch Preview</p>
                  <pre class="mt-2 max-h-36 overflow-auto text-[11px] text-slate-600">{{ JSON.stringify(pendingReportPatch.patch_jsonb, null, 2) }}</pre>
                  <div class="mt-3 flex justify-end gap-2">
                    <UButton size="xs" color="gray" variant="soft" @click="rejectReportPatch">Reject</UButton>
                    <UButton size="xs" color="indigo" @click="applyReportPatch">Apply Version</UButton>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Line Items -->
          <UCard v-if="lineItems.length > 0">
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-slate-700">
                  📦 Procurement Line Items ({{ lineItems.length }})
                </h3>
                <div class="flex items-center gap-2">
                  <UBadge color="green" variant="subtle" size="xs">{{ confirmedCount }} Confirmed</UBadge>
                  <UBadge color="gray" variant="subtle" size="xs">{{ draftCount }} Draft</UBadge>
                </div>
              </div>
            </template>

            <div class="space-y-3">
              <div
                v-for="item in lineItems"
                :key="item.id"
                class="rounded-xl border p-4 transition-all"
                :class="item.status === 'REMOVED' ? 'opacity-40 border-slate-100' : item.status === 'CONFIRMED' ? 'border-green-200 bg-green-50/30' : 'border-slate-200 hover:border-indigo-200'"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <h4 v-if="editingItem !== item.id" class="text-sm font-semibold text-slate-900">{{ item.name }}</h4>
                      <UInput v-else v-model="editForm.name" size="sm" class="flex-1" />
                      <UBadge :color="item.source === 'AI' ? 'indigo' : 'gray'" variant="subtle" size="xs">
                        {{ item.source }}
                      </UBadge>
                      <UBadge v-if="item.confidence" color="blue" variant="subtle" size="xs">
                        {{ (item.confidence * 100).toFixed(0) }}% conf
                      </UBadge>
                      <UBadge :color="matchedSamplesForItem(item.id).length ? 'green' : 'amber'" variant="subtle" size="xs">
                        {{ matchedSamplesForItem(item.id).length ? `${matchedSamplesForItem(item.id).length} matched` : 'Unmatched slot' }}
                      </UBadge>
                    </div>
                    <p v-if="item.category_hint" class="text-xs text-slate-400 mt-1">
                      Category: {{ item.category_hint }}
                    </p>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      v-if="item.status !== 'REMOVED'"
                      class="rounded-full px-3 py-1 text-xs font-semibold transition-colors"
                      :class="item.include_in_estimate !== false ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500 border border-slate-200'"
                      @click="toggleIncludeInEstimate(item)"
                    >
                      {{ item.include_in_estimate !== false ? 'Included' : 'Excluded' }}
                    </button>
                    <template v-if="editingItem === item.id">
                      <UButton size="xs" color="green" variant="soft" icon="i-heroicons-check" @click="saveLineItem(item)" />
                      <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-x-mark" @click="editingItem = null" />
                    </template>
                    <template v-else-if="item.status !== 'REMOVED'">
                      <UButton size="xs" variant="ghost" icon="i-heroicons-pencil" @click="startEditItem(item)" />
                      <UButton
                        v-if="item.status === 'DRAFT'"
                        size="xs" color="green" variant="soft" icon="i-heroicons-check"
                        @click="confirmItem(item)"
                      >Confirm</UButton>
                      <UButton
                        v-if="item.status === 'CONFIRMED'"
                        size="xs" color="gray" variant="soft"
                        @click="unconfirmItem(item)"
                      >Undo</UButton>
                      <UButton size="xs" variant="ghost" color="red" icon="i-heroicons-trash" @click="removeItem(item.id)" />
                    </template>
                  </div>
                </div>

                <!-- Editing inline -->
                <div v-if="editingItem === item.id" class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                  <UFormGroup label="Qty" size="xs">
                    <UInput v-model.number="editForm.qty" type="number" />
                  </UFormGroup>
                  <UFormGroup label="Unit" size="xs">
                    <UInput v-model="editForm.unit" />
                  </UFormGroup>
                  <UFormGroup label="Unit Price" size="xs">
                    <UInput v-model.number="editForm.estimated_unit_price" type="number" />
                  </UFormGroup>
                  <UFormGroup label="Total Price" size="xs">
                    <UInput v-model.number="editForm.estimated_total_price" type="number" />
                  </UFormGroup>
                </div>

                <!-- Display row -->
                <div v-else class="mt-2 space-y-2">
                  <div class="flex items-center gap-4 text-xs text-slate-500">
                    <span>{{ item.qty }} {{ item.unit }}</span>
                    <span v-if="item.estimated_unit_price">
                      ₱{{ item.estimated_unit_price?.toLocaleString() }}/{{ item.unit }}
                    </span>
                    <span v-if="item.estimated_total_price" class="font-semibold text-slate-700">
                      Total: ₱{{ item.estimated_total_price?.toLocaleString() }}
                    </span>
                    <span>{{ item.quality_tier?.replace(/_/g, ' ') }}</span>
                  </div>

                  <div class="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
                    <template v-if="matchedSamplesForItem(item.id).length">
                      <p class="font-semibold text-slate-700">Matched database products</p>
                      <div class="mt-1.5 flex flex-wrap gap-1.5">
                        <UBadge
                          v-for="sample in matchedSamplesForItem(item.id).slice(0, 4)"
                          :key="sample.catalog_item_id || sample.title"
                          color="indigo"
                          variant="subtle"
                          size="xs"
                        >
                          {{ sample.title || sample.catalog_item_title || 'Catalog item' }}
                          <span v-if="sample.unit_price"> · ₱{{ Number(sample.unit_price).toLocaleString() }}</span>
                        </UBadge>
                      </div>
                    </template>
                    <template v-else>
                      <p class="font-semibold text-amber-700">No matched catalog product yet. A purchase placeholder is kept.</p>
                      <p class="mt-0.5 text-slate-500">The user can add a manual price, wait for suppliers, or exclude this item from totals.</p>
                    </template>
                  </div>

                  <!-- Multi-tier pricing -->
                  <div v-if="item.price_tiers_jsonb" class="grid grid-cols-3 gap-2 mt-1">
                    <div
                      v-for="tier in ['BUDGET', 'MID_RANGE', 'PREMIUM']"
                      :key="tier"
                      class="rounded-lg px-2.5 py-2 text-center"
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
                      <p class="text-[10px] font-bold uppercase tracking-wide"
                        :class="{
                          'text-green-600': tier === 'BUDGET',
                          'text-blue-600': tier === 'MID_RANGE',
                          'text-purple-600': tier === 'PREMIUM',
                        }"
                      >
                        {{ tier === 'MID_RANGE' ? 'Mid-Range' : tier === 'BUDGET' ? '💰 Budget' : '👑 Premium' }}
                      </p>
                      <p class="text-xs font-bold text-slate-800 mt-0.5">
                        ₱{{ (item.price_tiers_jsonb[tier]?.total_price || 0).toLocaleString() }}
                      </p>
                      <p class="text-[10px] text-slate-400 mt-0.5 line-clamp-1">
                        {{ item.price_tiers_jsonb[tier]?.notes || '' }}
                      </p>
                    </div>
                  </div>
                </div>

                <p v-if="item.sourcing_notes && editingItem !== item.id" class="text-xs text-slate-400 mt-1.5 line-clamp-2">
                  {{ item.sourcing_notes }}
                </p>
              </div>
            </div>
          </UCard>

          <!-- Comparison / price environment -->
          <UCard v-if="comparisonItems.length > 0" class="border-blue-100">
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-blue-700">📊 Supplier Comparison & Real Price Tiers</h3>
                <UButton size="xs" color="blue" variant="soft" :loading="estimatingPrices" @click="refreshPriceEstimate">
                  Recalculate
                </UButton>
              </div>
            </template>
            <div class="space-y-3">
              <div v-for="row in comparisonItems" :key="row.line_item.id" class="rounded-xl border border-slate-200 p-3">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <h4 class="text-sm font-semibold text-slate-900">{{ row.line_item.name }}</h4>
                    <p class="text-xs text-slate-400 mt-0.5">
                      {{ row.price_snapshot.source_summary }} · {{ row.price_snapshot.sample_count }} samples
                    </p>
                  </div>
                  <UBadge color="blue" variant="subtle" size="xs">
                    Median ₱{{ (row.price_snapshot.median_unit_price || 0).toLocaleString() }}
                  </UBadge>
                </div>
                <div class="grid grid-cols-3 gap-2 mt-3">
                  <div v-for="tier in ['BUDGET', 'MID_RANGE', 'PREMIUM']" :key="tier" class="rounded-lg bg-slate-50 p-2">
                    <p class="text-[10px] font-bold text-slate-500">{{ tier }}</p>
                    <p class="text-sm font-bold text-slate-900">
                      ₱{{ (row.line_item.price_tiers?.[tier]?.total_price || 0).toLocaleString() }}
                    </p>
                    <p class="text-[10px] text-slate-400 line-clamp-1">{{ row.line_item.price_tiers?.[tier]?.source || 'N/A' }}</p>
                  </div>
                </div>
                <div v-if="row.suppliers?.length" class="mt-3 flex flex-wrap gap-1">
                  <UBadge v-for="supplier in row.suppliers.slice(0, 3)" :key="supplier.catalog_item_id" color="indigo" variant="subtle" size="xs">
                    {{ supplier.catalog_item_title || supplier.company_name || 'Supplier' }}
                  </UBadge>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Published Intents -->
          <UCard v-if="publishedItems.length > 0">
            <template #header>
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  🚀 Published Requests ({{ publishedItems.length }})
                </h3>
                <UButton size="xs" color="indigo" variant="soft" icon="i-heroicons-magnifying-glass" @click="loadMatches" :loading="loadingMatches">
                  Check Matches
                </UButton>
              </div>
            </template>
            <div class="space-y-3">
              <NuxtLink
                v-for="item in publishedItems"
                :key="item.id"
                :to="item.intent_id ? `/buyer/requests/${item.intent_id}` : '#'"
                class="block rounded-xl border border-indigo-100 bg-indigo-50/30 p-3 hover:border-indigo-300 transition-colors"
              >
                <div class="flex items-center justify-between gap-2">
                  <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-medium text-slate-900 truncate">{{ item.name }}</h4>
                    <p class="text-xs text-slate-500 mt-0.5">{{ item.qty }} {{ item.unit }}</p>
                  </div>
                  <UBadge color="indigo" variant="subtle" size="xs">{{ item.status }}</UBadge>
                  <span v-if="itemMatches[item.id]" class="text-xs text-green-600 font-semibold">
                    {{ itemMatches[item.id] }} supplier{{ itemMatches[item.id] > 1 ? 's' : '' }}
                  </span>
                  <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-4 h-4 text-indigo-400" />
                </div>
              </NuxtLink>
            </div>
          </UCard>
        </div>

        <!-- Right: Sidebar -->
        <div class="space-y-6">
          <!-- Project Info -->
          <UCard>
            <template #header>
              <h3 class="text-sm font-semibold text-slate-700">Project Info</h3>
            </template>
            <dl class="space-y-3 text-sm">
              <div>
                <dt class="text-xs text-slate-400">Type</dt>
                <dd class="font-medium text-slate-900">{{ project.project_type }}</dd>
              </div>
              <div v-if="project.area_value">
                <dt class="text-xs text-slate-400">Area</dt>
                <dd class="font-medium text-slate-900">{{ project.area_value }} {{ project.area_unit }}</dd>
              </div>
              <div>
                <dt class="text-xs text-slate-400">Quality</dt>
                <dd class="font-medium text-slate-900">{{ project.quality_preference?.replace(/_/g, ' ') }}</dd>
              </div>
              <div v-if="project.budget_min || project.budget_max">
                <dt class="text-xs text-slate-400">Budget</dt>
                <dd class="font-medium text-slate-900">
                  ₱{{ (project.budget_min || 0).toLocaleString() }} — ₱{{ (project.budget_max || 0).toLocaleString() }}
                </dd>
              </div>
              <div>
                <dt class="text-xs text-slate-400">Created</dt>
                <dd class="font-medium text-slate-900">{{ new Date(project.created_at).toLocaleDateString() }}</dd>
              </div>
            </dl>
          </UCard>

          <!-- Metrics -->
          <UCard v-if="metrics">
            <template #header>
              <h3 class="text-sm font-semibold text-slate-700">Collected Indicators</h3>
            </template>
            <div v-if="metrics.missing_required?.length" class="mb-3 rounded-lg bg-amber-50 border border-amber-100 p-2">
              <p class="text-xs font-semibold text-amber-700">Missing required</p>
              <p class="text-xs text-amber-600 mt-1">
                {{ metrics.missing_required.map(m => m.label).join(', ') }}
              </p>
            </div>
            <dl class="space-y-2 text-xs">
              <div v-for="metric in metrics.values" :key="metric.id" class="flex justify-between gap-3">
                <dt class="text-slate-400">{{ metric.label || metric.key }}</dt>
                <dd class="font-medium text-slate-700 text-right">{{ metricDisplay(metric.value_jsonb) }}</dd>
              </div>
              <p v-if="!metrics.values?.length" class="text-xs text-slate-400">No indicators collected yet.</p>
            </dl>
          </UCard>

          <!-- Estimated Budget from AI -->
          <UCard v-if="project.estimated_budget_jsonb" class="bg-gradient-to-br from-green-50 to-emerald-50 border-green-100">
            <template #header>
              <h3 class="text-sm font-semibold text-green-700">💰 AI Budget Estimate</h3>
            </template>
            <div class="text-center py-2">
              <p class="text-2xl font-bold text-green-800">
                ₱{{ (project.estimated_budget_jsonb.min || 0).toLocaleString() }}
                —
                ₱{{ (project.estimated_budget_jsonb.max || 0).toLocaleString() }}
              </p>
              <p class="text-xs text-green-600 mt-1">
                {{ project.estimated_budget_jsonb.currency || 'PHP' }}
                · {{ ((project.estimated_budget_jsonb.confidence || 0) * 100).toFixed(0) }}% confidence
              </p>
            </div>

            <!-- Per-tier budget -->
            <div v-if="project.estimated_budget_jsonb.by_tier" class="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-green-200/60">
              <div class="text-center rounded-lg bg-green-100/50 py-2 px-1">
                <p class="text-[10px] font-bold text-green-700 uppercase">💰 Budget</p>
                <p class="text-xs font-bold text-green-900 mt-1">
                  ₱{{ (project.estimated_budget_jsonb.by_tier.BUDGET?.min || 0).toLocaleString() }}
                </p>
                <p class="text-[10px] text-green-600">
                  ~ ₱{{ (project.estimated_budget_jsonb.by_tier.BUDGET?.max || 0).toLocaleString() }}
                </p>
              </div>
              <div class="text-center rounded-lg bg-blue-100/50 py-2 px-1">
                <p class="text-[10px] font-bold text-blue-700 uppercase">⭐ Mid-Range</p>
                <p class="text-xs font-bold text-blue-900 mt-1">
                  ₱{{ (project.estimated_budget_jsonb.by_tier.MID_RANGE?.min || 0).toLocaleString() }}
                </p>
                <p class="text-[10px] text-blue-600">
                  ~ ₱{{ (project.estimated_budget_jsonb.by_tier.MID_RANGE?.max || 0).toLocaleString() }}
                </p>
              </div>
              <div class="text-center rounded-lg bg-purple-100/50 py-2 px-1">
                <p class="text-[10px] font-bold text-purple-700 uppercase">👑 Premium</p>
                <p class="text-xs font-bold text-purple-900 mt-1">
                  ₱{{ (project.estimated_budget_jsonb.by_tier.PREMIUM?.min || 0).toLocaleString() }}
                </p>
                <p class="text-[10px] text-purple-600">
                  ~ ₱{{ (project.estimated_budget_jsonb.by_tier.PREMIUM?.max || 0).toLocaleString() }}
                </p>
              </div>
            </div>
          </UCard>

          <!-- Risk Notes -->
          <UCard v-if="project.risk_notes_jsonb?.length" class="border-amber-100">
            <template #header>
              <h3 class="text-sm font-semibold text-amber-700">⚡ Risk Notes</h3>
            </template>
            <ul class="space-y-2">
              <li v-for="(note, i) in project.risk_notes_jsonb" :key="i" class="text-xs text-amber-600 flex items-start gap-2">
                <span class="text-amber-400 mt-0.5">•</span>
                {{ note }}
              </li>
            </ul>
          </UCard>

          <!-- Assumptions -->
          <UCard v-if="project.assumptions_jsonb?.length">
            <template #header>
              <h3 class="text-sm font-semibold text-slate-700">📝 AI Assumptions</h3>
            </template>
            <ul class="space-y-2">
              <li v-for="(a, i) in project.assumptions_jsonb" :key="i" class="text-xs text-slate-500 flex items-start gap-2">
                <span class="text-slate-300 mt-0.5">•</span>
                {{ a }}
              </li>
            </ul>
          </UCard>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'buyer', middleware: ['buyer'] })

const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()
const config = useRuntimeConfig()

const projectId = route.params.id as string
const loading = ref(true)
const analyzing = ref(false)
const publishing = ref(false)
const saving = ref(false)
const uploading = ref(false)
const sendingMessage = ref(false)
const estimatingPrices = ref(false)
const freezingForm = ref(false)
const dragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const project = ref<any>(null)
const aiRun = ref<any>(null)
const lineItems = ref<any[]>([])
const messages = ref<any[]>([])
const metrics = ref<any>(null)
const comparisonItems = ref<any[]>([])
const report = ref<any>(null)
const reportVersions = ref<any[]>([])
const selectedReportVersionId = ref('')
const reportBusy = ref(false)
const reportChatInput = ref('')
const pendingReportPatch = ref<any>(null)
const chatInput = ref('')
const chatError = ref('')

const showEditDesc = ref(false)
const editDesc = ref('')
const editingItem = ref<string | null>(null)
const editForm = reactive({ name: '', qty: 0, unit: '', estimated_unit_price: 0, estimated_total_price: 0 })

const loadingMatches = ref(false)
const itemMatches = ref<Record<string, number>>({})

const headers = computed(() => ({ Authorization: `Bearer ${authStore.accessToken}` }))

function tt(key: string, params: Record<string, string | number> = {}) {
  return appStore.t(key, params)
}

function projectStatusLabel(status: string) {
  return status ? status.replace(/_/g, ' ') : ''
}

const confirmedCount = computed(() => lineItems.value.filter(i => i.status === 'CONFIRMED').length)
const draftCount = computed(() => lineItems.value.filter(i => i.status === 'DRAFT').length)
const publishableCount = computed(() => lineItems.value.filter(i => i.status === 'CONFIRMED' && i.include_in_estimate !== false).length)
const publishedItems = computed(() => lineItems.value.filter(i => i.status === 'SOURCING' && i.intent_id))
const includedItemsCount = computed(() => lineItems.value.filter(i => i.include_in_estimate !== false).length)
const excludedItemsCount = computed(() => lineItems.value.filter(i => i.include_in_estimate === false).length)
const canEdit = computed(() => ['DRAFT', 'COLLECTING_INFO', 'AI_ANALYZED', 'READY_FOR_SOURCING'].includes(project.value?.status))
const canAnalyze = computed(() => project.value && ['DRAFT', 'COLLECTING_INFO', 'AI_ANALYZED'].includes(project.value.status))
const canPublish = computed(() => project.value && publishableCount.value > 0 && ['AI_ANALYZED', 'READY_FOR_SOURCING'].includes(project.value.status))
const customReportColumns = computed(() => (report.value?.columns || []).filter((col: any) => !col.system))
const showReportSheet = computed(() => {
  const status = project.value?.status
  return Boolean(report.value) && (
    lineItems.value.length > 0 ||
    (report.value?.rows?.length || 0) > 0 ||
    ['AI_ANALYZED', 'READY_FOR_SOURCING', 'SOURCING', 'ORDERING', 'COMPLETED'].includes(status)
  )
})
const reportTotalCards = computed(() => {
  const totals = report.value?.current_version?.totals_jsonb || {}
  return [
    { key: 'budget', label: 'Budget', value: `₱${Math.round(totals.BUDGET || 0).toLocaleString()}` },
    { key: 'mid', label: 'Mid', value: `₱${Math.round(totals.MID_RANGE || 0).toLocaleString()}` },
    { key: 'premium', label: 'Premium', value: `₱${Math.round(totals.PREMIUM || 0).toLocaleString()}` },
    { key: 'selected', label: 'Selected', value: `₱${Math.round(totals.selected_total || 0).toLocaleString()}` },
    { key: 'excluded', label: 'Excluded', value: `₱${Math.round(totals.excluded_total || 0).toLocaleString()}` },
    { key: 'unmatched', label: 'Unmatched', value: `${totals.unmatched_rows || 0} rows` },
  ]
})

const samplePrompts = [
  'I want to build a 200 sqm villa in Cebu, premium quality, please draft a material list.',
  'I want to build a 10kW solar project. I have roof photos and a budget range.',
  'I want to build a hardware prototype with boards, power supply, sensors, and enclosure.',
]

const includedTotalByTier = computed<Record<string, number>>(() => {
  const totals: Record<string, number> = { BUDGET: 0, MID_RANGE: 0, PREMIUM: 0 }
  for (const item of lineItems.value) {
    if (item.include_in_estimate === false) continue
    const tiers = item.price_tiers_jsonb || {}
    for (const tier of Object.keys(totals)) {
      totals[tier] += Number(tiers[tier]?.total_price || item.estimated_total_price || 0)
    }
  }
  return {
    BUDGET: Math.round(totals.BUDGET),
    MID_RANGE: Math.round(totals.MID_RANGE),
    PREMIUM: Math.round(totals.PREMIUM),
  }
})

const issueCount = computed(() => {
  const missing = metrics.value?.missing_required?.length || 0
  const unmatched = lineItems.value.filter(i => matchedSamplesForItem(i.id).length === 0).length
  return missing + unmatched
})

const forgeStages = computed(() => {
  const hasMessages = messages.value.length > 0 || Boolean(project.value?.description)
  const hasMetrics = Boolean(metrics.value?.values?.length)
  const metricsDone = hasMetrics && !(metrics.value?.missing_required?.length)
  const hasFiles = Boolean(project.value?.files?.length)
  const hasItems = lineItems.value.length > 0
  const hasComparison = comparisonItems.value.length > 0
  const frozen = ['READY_FOR_SOURCING', 'SOURCING', 'ORDERING', 'COMPLETED'].includes(project.value?.status)
  const rows = [
    { key: 'collect', label: tt('project.stage.goal'), sub: tt('project.stage.coreNeed'), done: hasMessages, active: !hasMessages },
    { key: 'scenario', label: tt('project.stage.metrics'), sub: tt('project.stage.indicators'), done: metricsDone, active: hasMessages && !metricsDone },
    { key: 'files', label: tt('project.stage.files'), sub: tt('project.stage.optional'), done: hasFiles, active: hasMessages && !hasFiles && !hasItems },
    { key: 'model', label: tt('project.stage.demandModel'), sub: tt('project.stage.lineItems'), done: hasItems, active: (hasFiles || hasMetrics) && !hasItems },
    { key: 'quote', label: tt('project.stage.compare'), sub: tt('project.stage.pricing'), done: hasComparison, active: hasItems && !hasComparison },
    { key: 'freeze', label: tt('project.stage.finalReport'), sub: tt('project.stage.freeze'), done: frozen, active: hasComparison && !frozen },
  ]
  return rows.map((stage, index) => ({
    ...stage,
    index: index + 1,
    status: stage.done ? 'done' : stage.active ? 'active' : 'pending',
  }))
})

const forgeProgress = computed(() => Math.round((forgeStages.value.filter(s => s.status === 'done').length / forgeStages.value.length) * 100))

const previewCards = computed(() => [
  {
    key: 'need',
    icon: '📌',
    title: tt('project.preview.coreNeed'),
    text: project.value?.description || tt('project.preview.waitGoal'),
    status: forgeStages.value[0]?.status || 'pending',
  },
  {
    key: 'scenario',
    icon: '🔄',
    title: tt('project.preview.projectMetrics'),
    text: metrics.value?.missing_required?.length
      ? tt('project.preview.indicatorsMissing', { count: metrics.value.missing_required.length })
      : tt('project.preview.indicatorsCollected', { count: metrics.value?.values?.length || 0 }),
    status: forgeStages.value[1]?.status || 'pending',
  },
  {
    key: 'docs',
    icon: '📎',
    title: tt('project.preview.supportingFiles'),
    text: tt('project.preview.filesAttached', { count: project.value?.files?.length || 0 }),
    status: forgeStages.value[2]?.status || 'pending',
  },
  {
    key: 'model',
    icon: '🧱',
    title: tt('project.preview.demandForm'),
    text: tt('project.preview.itemsIncluded', { items: lineItems.value.length, included: includedItemsCount.value }),
    status: forgeStages.value[3]?.status || 'pending',
  },
  {
    key: 'quote',
    icon: '📊',
    title: tt('project.preview.matchingQuotes'),
    text: tt('project.preview.comparisonIssues', { groups: comparisonItems.value.length, issues: issueCount.value }),
    status: forgeStages.value[4]?.status || 'pending',
  },
  {
    key: 'freeze',
    icon: '✅',
    title: tt('project.stage.finalReport'),
    text: ['READY_FOR_SOURCING', 'SOURCING', 'ORDERING', 'COMPLETED'].includes(project.value?.status) ? tt('project.preview.frozenReady') : tt('project.preview.waitFreeze'),
    status: forgeStages.value[5]?.status || 'pending',
  },
])

const aiRunStatusColor = computed(() => {
  const map: Record<string, string> = { PENDING: 'gray', RUNNING: 'blue', SUCCESS: 'green', FAILED: 'red' }
  return map[aiRun.value?.status] || 'gray'
})
const aiRunBorderClass = computed(() => {
  const map: Record<string, string> = { PENDING: 'border-l-slate-300', RUNNING: 'border-l-blue-400', SUCCESS: 'border-l-green-400', FAILED: 'border-l-red-400' }
  return map[aiRun.value?.status] || 'border-l-slate-200'
})
const isAiRunStale = computed(() => {
  if (!aiRun.value || !['PENDING', 'RUNNING'].includes(aiRun.value.status)) return false
  const startedAt = aiRun.value.started_at || aiRun.value.created_at
  if (!startedAt) return false
  return Date.now() - new Date(startedAt).getTime() > 30 * 60 * 1000
})
const normalizedAiError = computed(() => {
  const message = aiRun.value?.error_message || 'Analysis failed. Please try again.'
  if (message.includes('api.deepseek.com/chat/completions')) {
    return tt('project.oldDeepseekEndpoint')
  }
  if (message.includes('OPENAI_API_KEY') || message.includes('backend/.env')) {
    return tt('project.providerMissing')
  }
  return message
})

function projectTypeIcon(type: string) {
  return { CONSTRUCTION: '🏗️', SOLAR: '☀️', TECH_BUILD: '💻', RENOVATION: '🔨', GENERAL: '📦' }[type] || '📦'
}

function statusColor(status: string) {
  return { DRAFT: 'gray', COLLECTING_INFO: 'blue', ANALYZING: 'yellow', AI_ANALYZED: 'green', READY_FOR_SOURCING: 'indigo', SOURCING: 'purple', ORDERING: 'orange', COMPLETED: 'green', CANCELED: 'red' }[status] || 'gray'
}

function fileIcon(ct: string) {
  if (ct.startsWith('image/')) return '🖼️'
  if (ct.includes('pdf')) return '📄'
  if (ct.includes('word') || ct.includes('docx')) return '📝'
  if (ct.includes('text')) return '📃'
  return '📎'
}

function statusLabel(status: string) {
  return status === 'done' ? tt('project.status.done') : status === 'active' ? tt('project.status.active') : tt('project.status.pending')
}

function comparisonForItem(itemId: string) {
  return comparisonItems.value.find(row => row.line_item?.id === itemId)
}

function matchedSamplesForItem(itemId: string) {
  const row = comparisonForItem(itemId)
  return row?.price_snapshot?.samples || row?.suppliers || []
}

function reportTierTotal(row: any, tier: string) {
  return Math.round(Number(row.price_tiers_jsonb?.[tier]?.total_price || 0))
}

function eventValue(event: Event) {
  return (event.target as HTMLInputElement | HTMLSelectElement).value
}

function eventNumber(event: Event) {
  return Number(eventValue(event) || 0)
}

function eventChecked(event: Event) {
  return Boolean((event.target as HTMLInputElement).checked)
}

async function loadProject() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}`, { headers: headers.value })
    project.value = data
    lineItems.value = (data.line_items || []).filter((i: any) => i.status !== 'REMOVED')
    aiRun.value = data.latest_ai_run
    editDesc.value = data.description || ''
    await Promise.all([loadConversationData(), loadComparison(), loadReport()])
  } catch (e) {
    console.error('Failed to load project:', e)
  } finally {
    loading.value = false
  }
}

async function loadConversationData() {
  try {
    const [msgs, metricData] = await Promise.all([
      $fetch<any[]>(`${config.public.apiBase}/buyer/projects/${projectId}/messages`, { headers: headers.value }),
      $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/metrics`, { headers: headers.value }),
    ])
    messages.value = msgs || []
    metrics.value = metricData
  } catch (e) {
    console.error('Failed to load conversation data:', e)
  }
}

async function loadComparison() {
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/comparison`, { headers: headers.value })
    comparisonItems.value = data.items || []
  } catch {
    comparisonItems.value = []
  }
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
    console.error('Failed to load project report:', e)
    report.value = null
    reportVersions.value = []
  }
}

async function updateReportCell(rowId: string, field: string, value: any) {
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/cells`, {
      method: 'PATCH',
      headers: headers.value,
      body: { changes: [{ row_id: rowId, field, value }], message: `Update ${field}` },
    })
    await loadReport()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function addReportColumn() {
  const label = window.prompt('Column label, e.g. Brand Preference')
  if (!label) return
  const key = label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || `custom_${Date.now()}`
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/columns`, {
      method: 'POST',
      headers: headers.value,
      body: { key, label, data_type: 'text' },
    })
    await loadReport()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function addReportRow() {
  const name = window.prompt('New item name')
  if (!name) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/rows`, {
      method: 'POST',
      headers: headers.value,
      body: { name, qty: 1, unit: 'pcs', currency: project.value?.currency || 'PHP' },
    })
    await loadReport()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function recalculateReport() {
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/recalculate`, {
      method: 'POST',
      headers: headers.value,
    })
    await loadReport()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function freezeReport() {
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/freeze`, {
      method: 'POST',
      headers: headers.value,
    })
    await loadReport()
    await loadProject()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function restoreReportVersion() {
  if (!selectedReportVersionId.value) {
    await loadReport()
    return
  }
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/versions/${selectedReportVersionId.value}/restore`, {
      method: 'POST',
      headers: headers.value,
    })
    selectedReportVersionId.value = ''
    await loadReport()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function createReportPatch() {
  const message = reportChatInput.value.trim()
  if (!message) return
  reportBusy.value = true
  try {
    pendingReportPatch.value = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/report/chat`, {
      method: 'POST',
      headers: headers.value,
      body: { message },
    })
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function applyReportPatch() {
  if (!pendingReportPatch.value) return
  reportBusy.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/patches/${pendingReportPatch.value.id}/apply`, {
      method: 'POST',
      headers: headers.value,
    })
    pendingReportPatch.value = null
    reportChatInput.value = ''
    await loadReport()
  } catch (e) { console.error(e) }
  finally { reportBusy.value = false }
}

async function rejectReportPatch() {
  if (!pendingReportPatch.value) return
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/report/patches/${pendingReportPatch.value.id}/reject`, {
      method: 'POST',
      headers: headers.value,
    })
    pendingReportPatch.value = null
  } catch (e) { console.error(e) }
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
  chatError.value = ''
  try {
    const created = await $fetch<any[]>(`${config.public.apiBase}/buyer/projects/${projectId}/messages`, {
      method: 'POST',
      headers: headers.value,
      body: { content, file_ids: [] },
    })
    messages.value.push(...created)
    chatInput.value = ''
    await loadConversationData()
  } catch (e: any) {
    console.error('Failed to send project message:', e)
    chatError.value = e?.data?.detail || e?.message || 'Failed to send message. Please retry.'
  } finally {
    sendingMessage.value = false
  }
}

async function saveDescription() {
  saving.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}`, {
      method: 'PATCH', headers: headers.value, body: { description: editDesc.value },
    })
    project.value.description = editDesc.value
    showEditDesc.value = false
  } catch (e) { console.error(e) }
  finally { saving.value = false }
}

async function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) await uploadFiles(Array.from(input.files))
  input.value = ''
}

async function handleDrop(e: DragEvent) {
  dragging.value = false
  if (e.dataTransfer?.files) await uploadFiles(Array.from(e.dataTransfer.files))
}

async function uploadFiles(files: File[]) {
  uploading.value = true
  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/files`, {
        method: 'POST', headers: headers.value, body: formData,
      })
    } catch (e: any) {
      console.error(`Upload failed for ${file.name}:`, e)
    }
  }
  uploading.value = false
  await loadProject()
}

async function deleteFile(fileId: string) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/files/${fileId}`, {
      method: 'DELETE', headers: headers.value,
    })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function startAnalysis() {
  analyzing.value = true
  try {
    const run = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/ai/analyze`, {
      method: 'POST', headers: headers.value,
    })
    aiRun.value = run
    pollAnalysis(run.id)
  } catch (e: any) {
    console.error('Analysis failed:', e)
    analyzing.value = false
  }
}

async function retryAnalysis() {
  if (!aiRun.value) return
  analyzing.value = true
  try {
    const run = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/ai-runs/${aiRun.value.id}/retry`, {
      method: 'POST', headers: headers.value,
    })
    aiRun.value = run
    pollAnalysis(run.id)
  } catch (e: any) {
    console.error('Retry failed:', e)
    analyzing.value = false
  }
}

async function loadMatches() {
  loadingMatches.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/matches`, { headers: headers.value })
    const map: Record<string, number> = {}
    for (const item of data.items || []) {
      map[item.line_item_id] = item.matched_suppliers
    }
    itemMatches.value = map
  } catch (e) { console.error(e) }
  finally { loadingMatches.value = false }
}

async function pollAnalysis(runId: string) {
  let attempts = 0
  const interval = setInterval(async () => {
    attempts++
    try {
      const run = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/ai-runs/${runId}`, {
        headers: headers.value,
      })
      aiRun.value = run
      if (run.status === 'SUCCESS' || run.status === 'FAILED') {
        clearInterval(interval)
        analyzing.value = false
        await loadProject()
        if (run.status === 'SUCCESS') await refreshPriceEstimate(false)
      }
    } catch {
      if (attempts > 30) {
        clearInterval(interval)
        analyzing.value = false
      }
    }
  }, 3000)
}

function startEditItem(item: any) {
  editingItem.value = item.id
  Object.assign(editForm, {
    name: item.name,
    qty: item.qty,
    unit: item.unit,
    estimated_unit_price: item.estimated_unit_price || 0,
    estimated_total_price: item.estimated_total_price || 0,
  })
}

async function saveLineItem(item: any) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${item.id}`, {
      method: 'PATCH', headers: headers.value, body: editForm,
    })
    editingItem.value = null
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

async function confirmItem(item: any) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${item.id}`, {
      method: 'PATCH', headers: headers.value, body: { status: 'CONFIRMED' },
    })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function unconfirmItem(item: any) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${item.id}`, {
      method: 'PATCH', headers: headers.value, body: { status: 'DRAFT' },
    })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function removeItem(itemId: string) {
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/line-items/${itemId}`, {
      method: 'DELETE', headers: headers.value,
    })
    await loadProject()
  } catch (e) { console.error(e) }
}

async function publishProject() {
  publishing.value = true
  try {
    const result = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/publish`, {
      method: 'POST', headers: headers.value,
    })
    await loadProject()
    if (result.published_count > 0) {
      alert(`✅ Published ${result.published_count} items as procurement requests!`)
    }
  } catch (e: any) {
    console.error(e)
    alert(e?.data?.detail || 'Failed to publish')
  } finally {
    publishing.value = false
  }
}

async function freezeForm() {
  freezingForm.value = true
  try {
    const data = await $fetch<any>(`${config.public.apiBase}/buyer/projects/${projectId}/freeze-form`, {
      method: 'POST',
      headers: headers.value,
    })
    project.value = data
    lineItems.value = (data.line_items || []).filter((i: any) => i.status !== 'REMOVED')
    await loadConversationData()
  } catch (e: any) {
    alert(e?.data?.detail || 'Failed to freeze project form')
  } finally {
    freezingForm.value = false
  }
}

async function refreshPriceEstimate(showAlert = true) {
  estimatingPrices.value = true
  try {
    await $fetch(`${config.public.apiBase}/buyer/projects/${projectId}/price-estimate`, {
      method: 'POST',
      headers: headers.value,
    })
    await loadProject()
    await loadComparison()
    if (showAlert) alert('Price tiers refreshed from marketplace data.')
  } catch (e: any) {
    if (showAlert) alert(e?.data?.detail || 'Failed to refresh price estimate')
  } finally {
    estimatingPrices.value = false
  }
}

onMounted(loadProject)
</script>

<style scoped>
.forge-shell {
  border: 1px solid rgba(148, 163, 184, 0.32);
  border-radius: 24px;
  padding: 24px;
  background:
    linear-gradient(135deg, rgba(220, 252, 231, 0.9), rgba(219, 234, 254, 0.88)),
    #f8fafc;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
}

.report-cell {
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  padding: 6px 8px;
  color: #0f172a;
  outline: none;
}

.report-cell:hover,
.report-cell:focus {
  border-color: #c7d2fe;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.forge-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.forge-score {
  min-width: 112px;
  border-radius: 18px;
  border: 1px solid rgba(16, 185, 129, 0.22);
  background: rgba(255, 255, 255, 0.75);
  padding: 14px;
  text-align: center;
}

.forge-score strong {
  display: block;
  margin-top: 2px;
  color: #047857;
  font-size: 28px;
  line-height: 1;
}

.forge-stagebar {
  margin-top: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(248, 250, 252, 0.72);
  padding: 14px;
}

.forge-stage {
  position: relative;
  display: grid;
  grid-template-columns: auto auto;
  grid-template-areas:
    "index label"
    "index sub";
  align-items: center;
  min-width: 128px;
  gap: 0 10px;
  border-radius: 14px;
  padding: 12px 14px;
  border: 1px solid transparent;
  background: rgba(226, 232, 240, 0.72);
  color: #64748b;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}

.forge-stage.done {
  border-color: rgba(34, 197, 94, 0.38);
  background: rgba(240, 253, 244, 0.9);
  color: #166534;
}

.forge-stage.active {
  transform: translateY(-2px);
  border-color: #6366f1;
  background: #f59e0b;
  color: white;
  box-shadow: 0 10px 24px rgba(245, 158, 11, 0.24);
}

.stage-light {
  position: absolute;
  right: 10px;
  top: 10px;
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #cbd5e1;
}

.forge-stage.done .stage-light {
  background: #22c55e;
  box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.16);
  animation: forgePulse 1.8s infinite;
}

.stage-index {
  grid-area: index;
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.7);
  font-weight: 900;
  font-size: 18px;
}

.stage-label {
  grid-area: label;
  font-weight: 900;
  font-size: 13px;
}

.forge-stage small {
  grid-area: sub;
  font-size: 11px;
  opacity: 0.74;
}

.forge-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 20px;
  align-items: start;
}

.forge-chat-panel,
.forge-preview {
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.26);
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
}

.forge-chat-panel {
  display: flex;
  min-height: 560px;
  flex-direction: column;
}

.forge-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.forge-chat-canvas {
  flex: 1;
  min-height: 340px;
  max-height: 520px;
  overflow-y: auto;
  padding: 20px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.85), rgba(255, 255, 255, 0.9));
}

.forge-empty-chat {
  min-height: 280px;
  display: grid;
  align-content: center;
  justify-items: center;
  text-align: center;
}

.forge-message {
  display: flex;
  margin-bottom: 12px;
}

.forge-message.user {
  justify-content: flex-end;
}

.forge-message.system,
.forge-message.assistant {
  justify-content: flex-start;
}

.forge-message-bubble {
  max-width: 78%;
  border-radius: 20px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.55;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: white;
  color: #334155;
}

.forge-message.user .forge-message-bubble {
  border-color: #4f46e5;
  background: #4f46e5;
  color: white;
}

.forge-message.system .forge-message-bubble {
  border-color: rgba(245, 158, 11, 0.28);
  background: #fffbeb;
  color: #92400e;
}

.forge-composer {
  display: flex;
  gap: 12px;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
  padding: 16px;
}

.forge-preview {
  padding: 20px;
  min-width: 0;
  overflow: hidden;
}

.preview-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  background: rgba(255, 255, 255, 0.92);
  padding: 14px;
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
  min-width: 0;
}

.preview-card.done {
  border-color: rgba(34, 197, 94, 0.36);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.08);
}

.preview-card.active {
  border-color: rgba(99, 102, 241, 0.45);
  transform: translateX(2px);
}

.preview-light {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex: none;
  background: #cbd5e1;
}

.preview-card.done .preview-light {
  background: #22c55e;
  animation: forgePulse 1.8s infinite;
}

.preview-card.active .preview-light {
  background: #f59e0b;
}

.preview-pill {
  flex: none;
  border-radius: 999px;
  background: #f1f5f9;
  padding: 5px 9px;
  font-size: 11px;
  font-weight: 800;
  color: #64748b;
  max-width: 82px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-card.done .preview-pill {
  background: #dcfce7;
  color: #166534;
}

.preview-card.active .preview-pill {
  background: #fef3c7;
  color: #92400e;
}

@keyframes forgePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.36);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
  }
}

@media (max-width: 1280px) {
  .forge-grid {
    grid-template-columns: 1fr;
  }
}
</style>
