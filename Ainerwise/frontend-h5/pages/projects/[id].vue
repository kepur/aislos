<template>
  <div class="px-4 py-4">
    <NuxtLink to="/projects" class="inline-flex items-center gap-1 text-xs font-medium text-blue-500 mb-4">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
      </svg>
      {{ $t('ws.backToProjects') }}
    </NuxtLink>

    <div v-if="project" class="space-y-4">
      <!-- Header -->
      <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
        <div class="flex items-start justify-between">
          <h1 class="text-lg font-bold text-slate-800">{{ project.title || project.name }}</h1>
          <span :class="['text-[10px] font-semibold px-2.5 py-1 rounded-full', statusClass(project.status)]">
            {{ project.status?.replace(/_/g, ' ') }}
          </span>
        </div>
        <div class="mt-4">
          <div class="flex items-center gap-0.5">
            <div v-for="(step, i) in statusSteps" :key="step.key" class="h-1.5 flex-1 rounded-full"
              :class="currentStepIndex >= i ? 'bg-blue-500' : 'bg-slate-100'" />
          </div>
          <div class="flex justify-between mt-1 text-[9px] text-slate-400">
            <span>Planning</span><span>Delivery</span><span>Closed</span>
          </div>
        </div>
      </div>

      <!-- Workspace tabs (FI.5.1) -->
      <div class="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4">
        <button v-for="tab in tabs" :key="tab.key" @click="setTab(tab.key)"
          class="flex-shrink-0 text-xs font-semibold px-3.5 py-2 rounded-full transition"
          :class="activeTab === tab.key ? 'bg-blue-500 text-white shadow-sm' : 'bg-white text-slate-500 border border-slate-200'">
          {{ tab.label }}
          <span v-if="tab.badge" class="ml-1 opacity-80">{{ tab.badge }}</span>
        </button>
      </div>

      <!-- OVERVIEW -->
      <template v-if="activeTab === 'overview'">
        <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.projectDetails') }}</h2>
          <dl class="space-y-2.5 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.region') }}</dt><dd class="font-medium text-slate-700">{{ project.region || '-' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.startDate') }}</dt><dd class="font-medium text-slate-700">{{ project.start_date || t('ws.notScheduled') }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.expectedDelivery') }}</dt><dd class="font-medium text-slate-700">{{ project.expected_delivery_date || t('ws.notScheduled') }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.created') }}</dt><dd class="font-medium text-slate-700">{{ new Date(project.created_at).toLocaleDateString() }}</dd></div>
          </dl>
        </div>

        <div v-if="storageguard" class="bg-white rounded-2xl p-4 border border-cyan-100 shadow-sm">
          <div class="flex items-center justify-between gap-2 mb-2">
            <h2 class="text-sm font-bold text-slate-800">{{ $t('ws.sgMonitoring') }}</h2>
            <span v-if="storageguard.sample" class="text-[9px] font-bold uppercase tracking-wider bg-cyan-50 text-cyan-600 px-2 py-1 rounded-full">Sample</span>
          </div>
          <p v-if="storageguard.scenario" class="text-[11px] leading-relaxed text-slate-500 mb-3">{{ storageguard.scenario }}</p>
          <div v-if="storageguard.economics" class="grid grid-cols-2 gap-2">
            <div class="rounded-xl bg-slate-50 p-3"><p class="text-[10px] text-slate-400">{{ $t('ws.initial') }}</p><p class="text-sm font-bold text-slate-800">{{ money(storageguard.economics.initial_cost_min, storageguard.economics.initial_cost_max, storageguard.economics.currency) }}</p></div>
            <div class="rounded-xl bg-slate-50 p-3"><p class="text-[10px] text-slate-400">ARR</p><p class="text-sm font-bold text-slate-800">{{ money(storageguard.economics.arr_min, storageguard.economics.arr_max, storageguard.economics.currency) }}</p></div>
          </div>
        </div>

        <div v-if="project.team_json?.length" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.team') }}</h2>
          <div class="space-y-2">
            <div v-for="(member, i) in project.team_json" :key="i" class="flex items-center gap-3 p-2 rounded-xl bg-slate-50">
              <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold">{{ (member.name || '?').charAt(0).toUpperCase() }}</div>
              <div><p class="text-sm font-medium text-slate-700">{{ member.name || '-' }}</p><p class="text-xs text-slate-400">{{ member.role || '-' }}</p></div>
            </div>
          </div>
        </div>
      </template>

      <!-- PROJECT SPACE / AI TEAM (Phase H) -->
      <template v-else-if="activeTab === 'space'">
        <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800">{{ $t('ws.aiTeam') }}</h2>
          <p class="text-xs text-slate-400 mt-1">{{ $t('ws.aiTeamDesc') }}</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span v-for="a in space.agents || []" :key="a.slug" class="text-[11px] bg-indigo-50 text-indigo-600 px-2.5 py-1.5 rounded-full">
              {{ a.name }} · {{ a.role_title }}
            </span>
            <span v-if="loaded.space && !(space.agents || []).length" class="text-xs text-slate-400">{{ $t('ws.noAgentsAuthorized') }}</span>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-bold text-slate-800">{{ $t('ws.missions') }}</h2>
            <button @click="showMissionForm = !showMissionForm" class="text-xs font-semibold bg-indigo-500 text-white px-3 py-1.5 rounded-full">
              {{ showMissionForm ? $t('ws.cancel') : $t('ws.newMission') }}
            </button>
          </div>
          <form v-if="showMissionForm" class="mt-3 space-y-3" @submit.prevent="submitMission">
            <textarea v-model="missionGoal" rows="4" required :placeholder="$t('ws.missionPlaceholder')" class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 resize-none"></textarea>
            <p class="text-[11px] text-amber-600 bg-amber-50 rounded-xl p-2.5">{{ $t('ws.missionReviewGate') }}</p>
            <button type="submit" :disabled="missionSaving || missionGoal.trim().length < 10" class="w-full text-sm font-semibold bg-gradient-to-r from-indigo-500 to-blue-500 text-white py-3 rounded-xl disabled:opacity-50">
              {{ missionSaving ? $t('ws.submitting') : $t('ws.submitMission') }}
            </button>
            <p v-if="missionError" class="text-xs text-red-500">{{ missionError }}</p>
          </form>

          <div class="mt-3 space-y-3">
            <div v-for="m in space.missions || []" :key="m.id" class="rounded-xl border border-slate-100 p-3">
              <div class="flex items-start justify-between gap-2">
                <p class="text-xs font-semibold text-slate-700">{{ m.goal }}</p>
                <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0', statusClass(m.status)]">{{ m.status.replace(/_/g, ' ') }}</span>
              </div>
              <div v-if="m.agents?.length" class="mt-2 flex flex-wrap gap-1">
                <span v-for="a in m.agents" :key="a" class="text-[10px] bg-slate-50 text-slate-500 px-2 py-0.5 rounded-full">{{ a }}</span>
              </div>
              <div v-if="m.final_report" class="mt-2 rounded-xl bg-emerald-50 p-3">
                <p class="text-[11px] font-semibold text-emerald-700">{{ $t('ws.approvedFinalReport') }}</p>
                <p class="text-[11px] text-emerald-700 mt-1">{{ m.final_report.manager_summary }}</p>
              </div>
            </div>
            <p v-if="loaded.space && !(space.missions || []).length" class="text-xs text-slate-400 text-center py-3">{{ $t('ws.noMissions') }}</p>
          </div>
        </div>

        <div v-if="(space.tasks || []).length" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.agentTasks') }}</h2>
          <div class="space-y-2">
            <div v-for="task in space.tasks" :key="task.id" class="flex items-center justify-between gap-3 rounded-xl bg-slate-50 p-3">
              <div><p class="text-xs font-semibold text-slate-700">{{ task.title }}</p><p class="text-[10px] text-slate-400">{{ task.agent_slug }}</p></div>
              <span :class="['text-[10px] px-2 py-0.5 rounded-full', statusClass(task.status)]">{{ task.status }}</span>
            </div>
          </div>
        </div>

        <div v-if="(space.files || []).length" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.files') }}</h2>
          <div class="space-y-2">
            <div v-for="f in space.files" :key="f.id" class="flex items-center justify-between rounded-xl bg-slate-50 p-3">
              <p class="text-xs text-slate-700 truncate">{{ f.name }}</p>
              <span class="text-[10px] text-slate-400">{{ f.kind }}<template v-if="f.version"> · v{{ f.version }}</template></span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.timeline') }}</h2>
          <div class="space-y-3">
            <div v-for="item in space.timeline || []" :key="`${item.type}-${item.created_at}-${item.title}`" class="flex gap-3">
              <div class="mt-1 w-2 h-2 rounded-full bg-blue-400 flex-shrink-0"></div>
              <div class="min-w-0"><p class="text-xs font-medium text-slate-700 truncate">{{ item.title }}</p><p class="text-[10px] text-slate-400">{{ item.type }} · {{ item.status }} · {{ new Date(item.created_at).toLocaleString() }}</p></div>
            </div>
          </div>
        </div>
      </template>

      <!-- MONITORING (FI.5.5) -->
      <template v-else-if="activeTab === 'monitoring'">
        <div v-if="monitoring.summary" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <div class="grid grid-cols-4 gap-2">
            <div class="rounded-xl bg-slate-50 p-2.5 text-center"><p class="text-base font-bold text-slate-800">{{ monitoring.summary.total }}</p><p class="text-[10px] text-slate-400">{{ $t('ws.points') }}</p></div>
            <div class="rounded-xl bg-emerald-50 p-2.5 text-center"><p class="text-base font-bold text-emerald-600">{{ monitoring.summary.active }}</p><p class="text-[10px] text-slate-400">{{ $t('ws.active') }}</p></div>
            <div class="rounded-xl p-2.5 text-center" :class="monitoring.summary.alerts ? 'bg-red-50' : 'bg-slate-50'"><p class="text-base font-bold" :class="monitoring.summary.alerts ? 'text-red-600' : 'text-slate-400'">{{ monitoring.summary.alerts }}</p><p class="text-[10px] text-slate-400">{{ $t('ws.alerts') }}</p></div>
            <div class="rounded-xl p-2.5 text-center" :class="monitoring.summary.calibration_due ? 'bg-amber-50' : 'bg-slate-50'"><p class="text-base font-bold" :class="monitoring.summary.calibration_due ? 'text-amber-600' : 'text-slate-400'">{{ monitoring.summary.calibration_due }}</p><p class="text-[10px] text-slate-400">{{ $t('ws.calDue') }}</p></div>
          </div>
        </div>
        <div v-for="site in monitoring.summary?.sites || []" :key="site.site" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-800">{{ site.site }}</h3>
            <span class="text-[11px] text-slate-400">{{ site.active }}/{{ site.total }} active</span>
          </div>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <span v-for="p in pointsForSite(site.site)" :key="p.id"
              class="text-[11px] px-2 py-1 rounded-lg" :class="p.status === 'fault' ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-slate-600'">
              {{ p.device_name || p.point_type }}<template v-if="p.threshold_min != null"> · {{ p.threshold_min }}–{{ p.threshold_max }}{{ p.unit }}</template>
            </span>
          </div>
        </div>
        <EmptyState v-if="loaded.monitoring && !monitoring.summary?.total" text="No monitoring points yet." />
      </template>

      <!-- AMC (FI.5.2) -->
      <template v-else-if="activeTab === 'amc'">
        <div v-for="amc in amc.items || []" :key="amc.id" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-800 capitalize">{{ amc.package }} AMC</h3>
            <span :class="['text-[10px] font-semibold px-2.5 py-1 rounded-full', amc.renewal_status === 'active' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600']">{{ amc.renewal_status }}</span>
          </div>
          <dl class="mt-3 space-y-2 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.amcAnnualFee') }}</dt><dd class="font-semibold text-slate-700">{{ amc.recurring_fee ? '€' + amc.recurring_fee.toLocaleString() : '—' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.term') }}</dt><dd class="text-slate-700">{{ amc.start_date }} → {{ amc.end_date }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.onsitePerYear') }}</dt><dd class="text-slate-700">{{ amc.included_visits_per_year ?? '—' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.responseTarget') }}</dt><dd class="text-slate-700">{{ amc.response_target_hours ? amc.response_target_hours + 'h' : '—' }}</dd></div>
          </dl>
          <div v-if="amc.coverage_json?.includes" class="mt-3">
            <p class="text-[11px] font-semibold text-slate-500 mb-1">{{ $t('ws.includes') }}</p>
            <div class="flex flex-wrap gap-1.5"><span v-for="c in amc.coverage_json.includes" :key="c" class="text-[11px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{{ c }}</span></div>
          </div>
          <div v-if="amc.exclusions_json?.length" class="mt-2">
            <p class="text-[11px] font-semibold text-slate-500 mb-1">{{ $t('ws.exclusions') }}</p>
            <div class="flex flex-wrap gap-1.5"><span v-for="e in amc.exclusions_json" :key="e" class="text-[11px] bg-slate-50 text-slate-500 px-2 py-0.5 rounded-full">{{ e }}</span></div>
          </div>
          <NuxtLink to="/contact" class="mt-3 block text-center text-xs font-semibold bg-blue-500 text-white py-2.5 rounded-xl">{{ $t('ws.requestRenewal') }}</NuxtLink>
        </div>
        <EmptyState v-if="loaded.amc && !(amc.items || []).length" text="No AMC plan on this project yet." />
      </template>

      <!-- WARRANTY (FI.5.3) -->
      <template v-else-if="activeTab === 'warranty'">
        <div v-for="w in warranty.items || []" :key="w.id" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-800 capitalize">{{ (w.warranty_model || '').replace(/_/g,' ') }} warranty</h3>
            <span class="text-[10px] font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-600">{{ w.start_date }} → {{ w.end_date }}</span>
          </div>
          <dl class="mt-3 space-y-2 text-sm">
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.laborIncluded') }}</dt><dd>{{ w.included_labor ? 'Yes' : 'No' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.remoteSupport') }}</dt><dd>{{ w.included_remote_support ? 'Yes' : 'No' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.onsitePerYear') }}</dt><dd>{{ w.included_on_site_visits_per_year ?? '—' }}</dd></div>
            <div class="flex justify-between"><dt class="text-slate-400">{{ $t('ws.spareParts') }}</dt><dd>{{ w.spare_parts_included ? $t('ws.included') : $t('ws.quotedSeparately') }}</dd></div>
          </dl>
          <div v-if="w.included_devices_json?.length" class="mt-3">
            <p class="text-[11px] font-semibold text-slate-500 mb-1">{{ $t('ws.coveredDevices') }}</p>
            <div class="flex flex-wrap gap-1.5"><span v-for="d in w.included_devices_json" :key="d" class="text-[11px] bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full">{{ d }}</span></div>
          </div>
          <p class="mt-3 rounded-xl bg-amber-50 p-3 text-[11px] leading-relaxed text-amber-700">
            Hardware follows the original supplier warranty unless covered by Managed Warranty or a Fast Replacement Plan. On-site visits are quoted separately.
          </p>
          <button @click="setTab('tickets')" class="mt-3 w-full text-center text-xs font-semibold bg-slate-100 text-slate-700 py-2.5 rounded-xl">{{ $t('ws.openTicket') }}</button>
        </div>
        <EmptyState v-if="loaded.warranty && !(warranty.items || []).length" text="No warranty record on this project yet." />
      </template>

      <!-- REPORTS (FI.5.6) -->
      <template v-else-if="activeTab === 'reports'">
        <StorageGuardReportPreview v-if="reports.sample_report" :report="reports.sample_report" />
        <div v-if="(reports.calibration_certificates || []).length" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.calibrationCerts') }}</h2>
          <div class="space-y-2">
            <div v-for="c in reports.calibration_certificates" :key="c.id" class="flex items-center justify-between rounded-xl bg-slate-50 p-3">
              <div><p class="text-xs font-semibold text-slate-700">Calibration {{ c.calibration_date }}</p><p class="text-[11px] text-slate-400">{{ c.calibration_method }} · {{ c.technician }}</p></div>
              <span class="text-[10px] font-semibold px-2 py-1 rounded-full" :class="c.result === 'pass' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'">{{ c.result }}</span>
            </div>
          </div>
        </div>
        <div v-if="(reports.files || []).length" class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <h2 class="text-sm font-bold text-slate-800 mb-3">{{ $t('ws.files') }}</h2>
          <div class="space-y-2">
            <div v-for="f in reports.files" :key="f.id" class="flex items-center justify-between rounded-xl bg-slate-50 p-3">
              <p class="text-xs text-slate-700 truncate">{{ f.original_name }}</p>
              <span class="text-[10px] text-slate-400">{{ f.file_type || f.mime_type }}</span>
            </div>
          </div>
        </div>
        <EmptyState v-if="loaded.reports && !reports.sample_report && !(reports.calibration_certificates||[]).length && !(reports.files||[]).length" text="No reports or certificates yet." />
      </template>

      <!-- TICKETS (FI.5.4) -->
      <template v-else-if="activeTab === 'tickets'">
        <div class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-bold text-slate-800">{{ $t('ws.tickets') }}</h2>
            <button @click="showTicketForm = !showTicketForm" class="text-xs font-semibold bg-blue-500 text-white px-3 py-1.5 rounded-full">{{ showTicketForm ? $t('ws.cancel') : $t('ws.newTicket') }}</button>
          </div>

          <form v-if="showTicketForm" class="space-y-3 mb-4" @submit.prevent="submitTicket">
            <div>
              <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Issue Type</label>
              <select v-model="ticketForm.issue_type" class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 bg-white">
                <option v-for="t in issueTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-[10px] font-semibold text-slate-400 mb-1 uppercase tracking-wider">Priority</label>
              <select v-model="ticketForm.priority" class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 bg-white">
                <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
              </select>
            </div>
            <input v-model="ticketForm.title" type="text" :placeholder="$t('ws.shortTitle')" required class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5" />
            <input v-model="ticketForm.affected_device" type="text" :placeholder="$t('ws.affectedDevice')" class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5" />
            <textarea v-model="ticketForm.description" rows="3" :placeholder="$t('ws.describeIssue')" class="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 resize-none"></textarea>
            <button type="submit" :disabled="ticketSaving" class="w-full text-sm font-semibold bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 rounded-xl disabled:opacity-50">{{ ticketSaving ? $t('ws.submitting') : $t('ws.submitTicket') }}</button>
            <p v-if="ticketError" class="text-xs text-red-500">{{ ticketError }}</p>
          </form>

          <div class="space-y-2">
            <div v-for="t in tickets.items || []" :key="t.id" class="rounded-xl border border-slate-100 p-3">
              <div class="flex items-center justify-between gap-2">
                <p class="text-xs font-semibold text-slate-700">{{ t.title }}</p>
                <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full', statusClass(t.status)]">{{ t.status?.replace(/_/g,' ') }}</span>
              </div>
              <p class="text-[11px] text-slate-400 mt-1">{{ (t.issue_type || '').replace(/_/g,' ') }}<template v-if="t.affected_device"> · {{ t.affected_device }}</template></p>
              <div v-if="t.coverage_type" class="mt-1.5 flex items-center gap-2">
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{{ t.coverage_type.replace(/_/g,' ') }}</span>
                <span v-if="t.is_paid_service" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-600">paid service</span>
              </div>
            </div>
          </div>
          <EmptyState v-if="loaded.tickets && !(tickets.items || []).length" text="No tickets yet. Open one above." />
        </div>
      </template>
    </div>

    <div v-else class="text-center py-20 text-slate-400"><p class="text-sm">{{ $t('ws.loadingProject') }}</p></div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const { apiFetch } = useApi()
const { t } = useI18n()
const project = ref<any>(null)
const projectId = route.params.id as string

const activeTab = ref('overview')
const loaded = reactive<Record<string, boolean>>({})
const monitoring = ref<any>({})
const amc = ref<any>({})
const warranty = ref<any>({})
const reports = ref<any>({})
const tickets = ref<any>({})
const workspace = ref<any>({})
const space = ref<any>({})

const issueTypes = [
  { value: 'device_failure', label: t('ws.it_device_failure') },
  { value: 'false_alarm', label: t('ws.it_false_alarm') },
  { value: 'network', label: t('ws.it_network') },
  { value: 'report', label: t('ws.it_report') },
  { value: 'expansion', label: t('ws.it_expansion') },
  { value: 'calibration', label: t('ws.it_calibration') },
  { value: 'on_site_service', label: t('ws.it_on_site_service') },
  { value: 'upgrade', label: t('ws.it_upgrade') },
]

const showTicketForm = ref(false)
const ticketSaving = ref(false)
const ticketError = ref('')
const ticketForm = reactive({ issue_type: 'device_failure', priority: 'medium', title: '', affected_device: '', description: '' })
const showMissionForm = ref(false)
const missionSaving = ref(false)
const missionError = ref('')
const missionGoal = ref('')

const tabs = computed(() => [
  { key: 'overview', label: t('ws.overview') },
  { key: 'space', label: t('ws.projectSpace'), badge: (space.value.missions || []).length || '' },
  { key: 'monitoring', label: t('ws.monitoring'), badge: workspace.value.monitoring_points || '' },
  { key: 'amc', label: t('ws.amc'), badge: workspace.value.amc || '' },
  { key: 'warranty', label: t('ws.warranty'), badge: workspace.value.warranties || '' },
  { key: 'reports', label: t('ws.reports'), badge: workspace.value.calibration_records || '' },
  { key: 'tickets', label: t('ws.tickets'), badge: workspace.value.tickets || '' },
])

const statusSteps = [
  { key: 'planning' }, { key: 'site_survey' }, { key: 'quotation_confirmed' }, { key: 'procurement' },
  { key: 'delivery' }, { key: 'installation' }, { key: 'testing' }, { key: 'handover' },
  { key: 'maintenance' }, { key: 'closed' },
]
const currentStepIndex = computed(() => project.value ? statusSteps.findIndex(s => s.key === project.value.status) : -1)
const storageguard = computed(() => {
  const plan = project.value?.project_plan_json
  return plan && plan.solution_line === 'storageguard' ? plan : null
})

function statusClass(status: string) {
  if (['closed', 'handover', 'resolved'].includes(status)) return 'bg-emerald-50 text-emerald-600'
  if (['planning', 'site_survey', 'open'].includes(status)) return 'bg-blue-50 text-blue-600'
  return 'bg-amber-50 text-amber-600'
}
function money(min: number, max: number, currency = 'EUR') {
  const s = currency === 'EUR' ? '€' : `${currency} `
  const f = (n: number) => s + Number(n).toLocaleString()
  return min && max && min !== max ? `${f(min)} – ${f(max)}` : f(max || min || 0)
}
function pointsForSite(site: string) {
  return (monitoring.value.items || []).filter((p: any) => (p.site || 'Unassigned') === site)
}

async function setTab(key: string) {
  activeTab.value = key
  if (loaded[key] || key === 'overview') return
  const url: Record<string, string> = {
    monitoring: `/portal/projects/${projectId}/monitoring-points`,
    amc: `/portal/projects/${projectId}/amc-contracts`,
    warranty: `/portal/projects/${projectId}/warranties`,
    reports: `/portal/projects/${projectId}/reports`,
    tickets: `/portal/projects/${projectId}/tickets`,
    space: `/portal/projects/${projectId}/space`,
  }
  const target: Record<string, any> = { monitoring, amc, warranty, reports, tickets, space }
  try {
    target[key].value = await apiFetch<any>(url[key])
  } catch { target[key].value = {} }
  loaded[key] = true
}

async function submitTicket() {
  ticketError.value = ''
  if (!ticketForm.title.trim()) return
  ticketSaving.value = true
  try {
    await apiFetch('/tickets', { method: 'POST', body: { project_id: projectId, ...ticketForm } })
    showTicketForm.value = false
    Object.assign(ticketForm, { issue_type: 'device_failure', priority: 'medium', title: '', affected_device: '', description: '' })
    loaded.tickets = false
    await setTab('tickets')
  } catch (e: any) {
    ticketError.value = e?.data?.detail || 'Submit failed'
  } finally {
    ticketSaving.value = false
  }
}

async function submitMission() {
  missionError.value = ''
  if (missionGoal.value.trim().length < 10) return
  missionSaving.value = true
  try {
    await apiFetch(`/portal/projects/${projectId}/missions`, {
      method: 'POST',
      body: { goal: missionGoal.value.trim() },
    })
    missionGoal.value = ''
    showMissionForm.value = false
    loaded.space = false
    await setTab('space')
  } catch (e: any) {
    missionError.value = e?.data?.detail || 'Submit failed'
  } finally {
    missionSaving.value = false
  }
}

onMounted(async () => {
  try {
    project.value = await apiFetch<any>(`/projects/${projectId}`)
    workspace.value = await apiFetch<any>(`/portal/projects/${projectId}/workspace`)
  } catch {}
})
</script>
