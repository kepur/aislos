<template>
  <div class="min-h-screen pt-10 pb-20">
    <section class="container-main px-4 sm:px-6 lg:px-8 py-8 lg:py-10">
      <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-8">
        <div>
          <p class="text-sm font-bold uppercase tracking-wider text-primary-400">{{ $t('lead.forgeKicker') }}</p>
          <h1 class="mt-2 text-4xl font-bold text-white">{{ $t('lead.forgeTitle') }}</h1>
          <p class="mt-3 max-w-4xl text-slate-300">{{ $t('lead.forgeSubtitle') }}</p>
        </div>
        <div class="border glass-panel border-primary-500/30 px-6 py-4 text-center">
          <p class="text-sm text-slate-400">{{ $t('lead.progress') }}</p>
          <p class="text-3xl font-bold text-primary-400">{{ progress }}%</p>
        </div>
      </div>

      <div v-if="!selectedCategory" class="grid grid-cols-1 lg:grid-cols-[0.8fr_1.2fr] gap-6">
        <div class="glass-panel p-6 border-primary-500/30">
          <p class="text-sm font-bold uppercase tracking-wider text-primary-300">Step 1</p>
          <h2 class="mt-2 text-2xl font-bold text-white">{{ $t('lead.step1Label') }}</h2>
          <p class="mt-3 text-slate-300">{{ $t('lead.step1Desc') }}</p>
          <div class="mt-6 bg-amber-400/10 border border-amber-500/30 p-4 text-sm text-amber-200">
            {{ $t('lead.estimateWarning') }}
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            v-for="category in projectCategories"
            :key="category.key"
            type="button"
            class="text-left glass-panel p-5 border-white/10 hover:border-primary-400 hover:shadow-md transition"
            @click="startCategory(category.key)"
          >
            <p class="text-xs font-bold uppercase tracking-wider text-primary-400">{{ category.level }}</p>
            <h3 class="mt-2 font-bold text-white">{{ category.label }}</h3>
            <p class="mt-2 text-sm text-slate-300">{{ category.description }}</p>
          </button>
        </div>
      </div>

      <div v-else class="space-y-6">
        <div class="glass-panel border-primary-500/30 border p-4">
          <div class="flex flex-col xl:flex-row xl:items-center gap-4">
            <div class="flex-1">
              <p class="text-xs font-bold uppercase tracking-wider text-primary-300">Selected project</p>
              <h2 class="mt-1 text-2xl font-bold text-white">{{ selectedCategory.label }}</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="level in levelOptions"
                :key="level.key"
                type="button"
                class="border px-4 py-2 text-sm font-semibold transition"
                :class="targetLevel === level.key ? 'pc-chip pc-chip-active' : 'pc-chip pc-chip-inactive'"
                @click="targetLevel = level.key"
              >
                {{ level.key }} · {{ level.label }}
              </button>
            </div>
            <button type="button" class="border px-4 py-2 text-sm font-semibold text-slate-300 hover:border-slate-500" @click="resetForge">
              Change category
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-[1.05fr_0.95fr] gap-6">
          <div class="glass-panel border-primary-500/30 overflow-hidden">
            <div class="border-b p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p class="text-sm font-bold uppercase tracking-wider text-primary-400">LangGraph Intake</p>
                <h2 class="mt-1 text-2xl font-bold text-white">Collect project information step by step</h2>
              </div>
              <button type="button" class="bg-primary-900/300/20 text-primary-400 px-4 py-2 text-sm font-semibold" @click="askNextQuestion">
                AI Analyze
              </button>
            </div>

            <div ref="chatScroll" class="h-[590px] overflow-y-auto p-5 lg:p-8 space-y-5 bg-transparent">
              <div
                v-for="message in messages"
                :key="message.id"
                class="flex"
                :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
              >
                <div
                  class="pc-chat-bubble"
                  :class="message.role === 'user' ? 'pc-chat-user' : 'pc-chat-assistant'"
                >
                  <p class="whitespace-pre-wrap">{{ message.text }}</p>
                  <p class="mt-2 text-xs" :class="message.role === 'user' ? 'text-primary-100' : 'text-slate-400'">
                    {{ message.tag }}
                  </p>
                </div>
              </div>
            </div>

            <div class="border-t border-white/10 bg-white/5 p-4">
              <div v-if="submitted" class="bg-emerald-400/10 border border-emerald-500/30 p-4 text-emerald-200">
                {{ phase1Requested ? 'Phase-1 Proposal request submitted.' : 'Requirement submitted.' }}
                Admin will review the AI estimate and follow up manually.
              </div>
              <form v-else class="flex flex-col sm:flex-row gap-3" @submit.prevent="sendMessage">
                <textarea
                  v-model="draft"
                  rows="2"
                  class="input-field resize-none"
                  :placeholder="currentQuestion?.placeholder || 'Answer the AI question...'"
                  @keydown.enter.exact.prevent="sendMessage"
                ></textarea>
                <button type="submit" class="btn-primary sm:w-40" :disabled="loading || (!readyToSubmit && !draft.trim())">
                  {{ loading ? 'Working...' : (readyToSubmit && !draft.trim()) ? 'Submit' : 'Send' }}
                </button>
              </form>
              <p v-if="error" class="mt-2 text-sm text-red-400">{{ error }}</p>
            </div>
          </div>

          <aside class="glass-panel p-6 border-primary-500/30 h-fit xl:sticky xl:top-24">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-sm font-bold uppercase tracking-wider text-primary-300">Project Preview</p>
                <h2 class="mt-1 text-2xl font-bold text-white">{{ progress }}% complete</h2>
              </div>
              <span class="border px-3 py-1 text-sm font-semibold text-primary-300">{{ targetLevel }} target</span>
            </div>

            <div class="mt-6 space-y-3">
              <div
                v-for="module in previewModules"
                :key="module.key"
                class="pc-status-card"
                :class="module.done ? 'pc-status-done' : module.active ? 'pc-status-active' : 'pc-status-pending'"
              >
                <div class="flex gap-3">
                  <span class="mt-2 h-3 w-3 shrink-0" :class="module.done ? 'bg-emerald-400' : module.active ? 'bg-amber-400' : 'bg-slate-600'"></span>
                  <div>
                    <p class="font-semibold text-white">{{ module.label }}</p>
                    <p class="mt-1 text-sm text-slate-300">{{ module.summary }}</p>
                  </div>
                </div>
                <span class="shrink-0 px-3 py-1 text-xs font-bold" :class="module.done ? 'pc-badge-done' : module.active ? 'pc-badge-active' : 'pc-badge-pending'">
                  {{ module.done ? 'Done' : module.active ? 'Active' : 'Pending' }}
                </span>
              </div>
            </div>

            <div class="mt-6 border p-4">
              <p class="text-sm font-semibold text-white">Selected intelligence behavior</p>
              <p class="mt-2 text-sm text-slate-300">{{ targetLevelMeta.description }}</p>
            </div>

            <div class="mt-6 bg-amber-400/10 border border-amber-500/30 p-4 text-sm text-amber-200">
              {{ estimateNotice }}
            </div>

            <div class="mt-6 border p-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-white">Lead Score</p>
                  <p class="mt-1 text-xs text-slate-400">Calculated from completeness, budget, contact, target level, and Phase-1 intent.</p>
                </div>
                <div class="text-right">
                  <p class="text-2xl font-bold text-primary-300">{{ leadScore }}</p>
                  <p class="text-xs font-semibold text-slate-400">{{ leadStage }}</p>
                </div>
              </div>
            </div>

            <div class="mt-6">
              <p class="text-sm font-semibold text-white">Preliminary Proposal Directions</p>
              <div class="mt-3 space-y-3">
                <div
                  v-for="plan in proposalPlans"
                  :key="plan.tier"
                  class="border p-4"
                  :class="plan.tier === 'premium_ai' ? 'border-primary-500/30 bg-primary-500/10' : 'border-white/10 bg-white/5'"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div>
                      <p class="font-semibold text-white">{{ plan.name }}</p>
                      <p class="mt-1 text-xs text-slate-400">{{ plan.level }} · {{ plan.complexity }}</p>
                    </div>
                    <span class="text-xs font-bold text-primary-300">{{ plan.risk }}</span>
                  </div>
                  <p class="mt-3 text-sm text-slate-300">{{ plan.summary }}</p>
                  <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div><dt class="text-slate-400">Device</dt><dd class="font-semibold text-white">{{ plan.device }}</dd></div>
                    <div><dt class="text-slate-400">Support</dt><dd class="font-semibold text-white">{{ plan.support }}</dd></div>
                  </dl>
                </div>
              </div>
            </div>

            <div v-if="readyToSubmit && !submitted" class="mt-6 border border-primary-500/30 bg-primary-900/30 p-4">
              <p class="font-semibold text-white">Ready for Phase-1 Proposal</p>
              <p class="mt-2 text-sm text-slate-300">
                Free AI estimate gives direction only. Phase-1 means human review, deeper BOM,
                architecture draft, supplier confirmation, and one meeting.
              </p>
              <button type="button" class="mt-4 btn-primary w-full" :disabled="loading" @click="requestPhase1Proposal">
                {{ loading ? 'Submitting...' : 'Request Phase-1 Proposal' }}
              </button>
            </div>
          </aside>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const { apiFetch } = useApi()
const assistant = useAssistant()
const aiComplete = ref(false)
onMounted(() => { assistant.checkStatus() })

function mergeExtracted(extracted: Record<string, any>) {
  if (!extracted) return
  for (const [k, v] of Object.entries(extracted)) {
    if (v === null || v === undefined || v === '') continue
    answers[k] = typeof v === 'string' ? v : JSON.stringify(v)
  }
  if (extracted.budget_and_service && !answers.budget) answers.budget = String(extracted.budget_and_service)
}

type CategoryKey = 'villa' | 'school' | 'apartment' | 'office' | 'factory' | 'hotel' | 'energy' | 'storage' | 'kitchen' | 'water' | 'asset' | 'agri' | 'retrofit' | 'custom'
type LevelKey = 'L3' | 'L4' | 'L5'

const estimateNotice = 'AI estimate only. Final quote requires manual review, customer meeting, site survey, supplier confirmation, and signed contract.'

const projectCategories = [
  { key: 'villa', label: 'Smart Villa / Future Home', level: 'L3-L5', description: 'Home AI brain, local privacy, family identity, comfort, energy, EV, smart room equipment.', systems: ['KNX', 'Home Assistant', 'CCTV', 'Energy Monitoring', 'EV Charging', 'Offline AI'] },
  { key: 'school', label: 'School / Campus', level: 'L3-L4', description: 'Classrooms, safety, CO2, access, CCTV, network, energy reports, maintenance workflow.', systems: ['CCTV', 'Access Control', 'HVAC', 'Energy Monitoring', 'Network'] },
  { key: 'apartment', label: 'Apartment Building', level: 'L3-L4', description: 'Property brain for common areas, parking, visitor access, meters, tenant support.', systems: ['Access Control', 'CCTV', 'Energy Monitoring', 'Maintenance'] },
  { key: 'office', label: 'Enterprise Office Building', level: 'L3-L5', description: 'Meeting rooms, visitor access, occupancy, IT network, facility AI daily summary.', systems: ['HVAC', 'Lighting', 'Access Control', 'Network', 'Offline AI'] },
  { key: 'factory', label: 'Factory / Industrial Plant', level: 'L3-L5', description: 'Industrial automation, machine energy, PLC/SCADA, OT network, robots, compressed air, chillers, motors, and maintenance.', systems: ['Industrial Automation', 'PLC/SCADA', 'Machine Energy Monitoring', 'Compressed Air', 'Robots', 'OT Network', 'Solar/Battery'] },
  { key: 'hotel', label: 'Hotel / Serviced Apartment', level: 'L3-L4', description: 'Guest room control, away energy saving, housekeeping access, remote maintenance.', systems: ['KNX', 'HVAC', 'Lighting', 'Access Control', 'Remote Maintenance'] },
  { key: 'energy', label: 'Solar + Energy Site', level: 'L3-L5', description: 'PV, battery, EV charging, tariffs, critical loads, alerts, monthly AI energy reports.', systems: ['Solar', 'Battery', 'EV Charging', 'Energy Monitoring'] },
  { key: 'storage', label: 'Cold Chain / Storage (StorageGuard)', level: 'L2-L4', description: 'Temperature & humidity compliance, door events, outage alerts, audit reports, calibration, and annual maintenance for cold rooms, pharma and food storage.', systems: ['StorageGuard', 'Temperature & Humidity Monitoring', 'Door Sensors', 'Outage Alerts', 'Compliance Reports', 'Calibration', 'Alarm Monitoring'] },
  { key: 'kitchen', label: 'Commercial Kitchen Safety (KitchenGuard)', level: 'L2-L3', description: 'Gas, CO, water-leak and temperature safety with automatic cut-off, alarm escalation, annual inspection certificates and AMC.', systems: ['KitchenGuard', 'Gas & CO Monitoring', 'Water Leak', 'Cut-off Valve', 'Alarm Monitoring', 'Annual Inspection'] },
  { key: 'water', label: 'Water / Effluent Compliance (AquaGuard)', level: 'L2-L4', description: 'pH, conductivity, turbidity and COD monitoring with environmental compliance reports, calibration and probe replacement (partner-led).', systems: ['AquaGuard', 'pH / EC / Turbidity / COD', 'Compliance Reports', 'Calibration', 'Probe Replacement', 'Alarm Monitoring'] },
  { key: 'asset', label: 'Asset & Tool Tracking (AssetPulse)', level: 'L2-L3', description: 'BLE/UWB/LoRa tag tracking with geofence alerts, inventory and multi-site reports as a tag subscription.', systems: ['AssetPulse', 'Asset Tags', 'Geofence Alerts', 'Inventory', 'Multi-site Reports'] },
  { key: 'agri', label: 'Greenhouse / Farm (AgriBrain — Future)', level: 'L3-L4', description: 'Future-ready soil, climate, water and fertilizer monitoring with seasonal service. Concept scope until partners and demand are validated.', systems: ['AgriBrain', 'Soil & Climate', 'Irrigation', 'Seasonal Service'] },
  { key: 'retrofit', label: 'Existing Building Retrofit', level: 'L3-L4', description: 'Upgrade older wiring, CCTV, network, access, and energy visibility without overpromising.', systems: ['CCTV', 'Network', 'Lighting', 'Energy Monitoring'] },
  { key: 'custom', label: 'Custom Future Building', level: 'L4-L5', description: 'Advanced AI, local AI box, identity, robot-ready paths, and manual engineering review.', systems: ['Offline AI', 'Network', 'CCTV', 'Energy Monitoring'] },
] as const

const levelOptions = [
  { key: 'L3', label: 'Energy Optimized', description: 'Focus on energy monitoring, scenes, schedules, dashboards, alarms, and lifecycle reports.' },
  { key: 'L4', label: 'AI Assisted', description: 'Adds AI analysis, anomaly detection, admin-reviewed recommendations, and smart operational summaries.' },
  { key: 'L5', label: 'Local AI Brain', description: 'Adds local AI box, privacy-first identity, offline control logic, and advanced cross-system orchestration.' },
] as const

const questionBank: Record<CategoryKey, Array<{ key: string; module: string; prompt: string; placeholder: string }>> = {
  villa: [
    { key: 'location', module: 'location', prompt: 'Where is the villa located? Please include country and city.', placeholder: 'Example: Belgrade, Serbia' },
    { key: 'building', module: 'site', prompt: 'What is the approximate area, number of floors, and main room list?', placeholder: 'Example: 320 sqm, 2 floors, living room, kitchen, 4 bedrooms...' },
    { key: 'existing', module: 'existing', prompt: 'What systems already exist: network, CCTV, alarm, HVAC, solar, EV charger, smart switches, or KNX?', placeholder: 'Describe current wiring, internet, CCTV, solar, HVAC...' },
    { key: 'goals', module: 'goals', prompt: 'What should the home become: energy saving, AI family brain, security, comfort, offline privacy, or robot-ready?', placeholder: 'Example: offline AI privacy, energy saving, face access, EV charging...' },
    { key: 'identity', module: 'identity', prompt: 'Do you need identity features such as face recognition, visitor QR, car plate, fingerprint, or future voiceprint?', placeholder: 'List required access and identity features...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need solar, battery, EV charging, peak/off-peak tariff logic, or appliance energy optimization?', placeholder: 'Describe PV, battery, EV and energy goals...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and service period should we design around?', placeholder: 'Example: 15k-50k EUR, 5-year support' },
    { key: 'contact', module: 'contact', prompt: 'Finally, who should we contact? Please provide name, email, and optional Telegram/WhatsApp.', placeholder: 'Example: Wei, wei@example.com, Telegram @...' },
  ],
  school: [
    { key: 'location', module: 'location', prompt: 'Where is the campus located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How many buildings, classrooms, floors, labs, admin areas, and students are involved?', placeholder: 'Example: 2 buildings, 32 classrooms, 600 students...' },
    { key: 'existing', module: 'existing', prompt: 'What existing CCTV, access control, network, HVAC, solar, or BMS systems are already installed?', placeholder: 'Describe existing systems and pain points...' },
    { key: 'goals', module: 'goals', prompt: 'What are the top goals: safety, energy saving, classroom comfort, lab access, network visibility, or maintenance?', placeholder: 'List top priorities...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need solar monitoring, classroom CO2, HVAC scheduling, or monthly energy reports?', placeholder: 'Describe energy and environment needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we assume?', placeholder: 'Example: 50k-100k EUR, 5-year lifecycle support' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this campus assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  apartment: [
    { key: 'location', module: 'location', prompt: 'Where is the apartment building located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How many units, floors, common areas, parking areas, and meters are involved?', placeholder: 'Example: 40 units, 8 floors, garage, lobby...' },
    { key: 'existing', module: 'existing', prompt: 'What existing intercom, CCTV, access, meters, lighting, or network systems exist?', placeholder: 'Describe current systems...' },
    { key: 'goals', module: 'goals', prompt: 'What should improve: visitor access, common-area energy, tenant experience, parking, repair workflow, or security?', placeholder: 'List property goals...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need common-area energy reports, PV for public loads, or meter monitoring?', placeholder: 'Energy and metering needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and service period are realistic?', placeholder: 'Example: 15k-50k EUR, 3-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for property follow-up?', placeholder: 'Name, email, phone or Telegram' },
  ],
  office: [
    { key: 'location', module: 'location', prompt: 'Where is the office building located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How large is the office, how many floors, employees, meeting rooms, IT rooms, and visitor areas?', placeholder: 'Example: 4100 sqm, 4 floors, 12 meeting rooms...' },
    { key: 'existing', module: 'existing', prompt: 'What existing access control, CCTV, network, HVAC, booking, or BMS systems are in place?', placeholder: 'Describe current office systems...' },
    { key: 'goals', module: 'goals', prompt: 'What are the goals: meeting automation, visitor access, energy saving, workplace utilization, local AI, or facility summaries?', placeholder: 'List office AI/facility goals...' },
    { key: 'identity', module: 'identity', prompt: 'Do you need employee identity, visitor QR, face access, mobile credentials, or admin-only AI permissions?', placeholder: 'Describe identity and access needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and maintenance period should we assume?', placeholder: 'Example: 50k-100k EUR, 5-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who is the office project contact?', placeholder: 'Name, email, phone or Telegram' },
  ],
  factory: [
    { key: 'location', module: 'location', prompt: 'Where is the factory, plant, or warehouse located?', placeholder: 'Country, city, industrial park if relevant' },
    { key: 'building', module: 'site', prompt: 'What is the plant scale: production area, floors/zones, production lines, warehouse, utilities, and shifts?', placeholder: 'Example: 12,000 sqm, 3 lines, compressor room, chiller plant, 2 shifts...' },
    { key: 'existing', module: 'existing', prompt: 'What existing OT/IT systems exist: PLC, SCADA, BMS, meters, VFDs, compressors, chillers, robots, CCTV, access, solar, or MES?', placeholder: 'List PLC/SCADA brands, protocols, meters, machines, network, PV...' },
    { key: 'production', module: 'production', prompt: 'Which mechanical or production equipment should be monitored or linked?', placeholder: 'Example: CNC machines, conveyors, robotic arms, pumps, boilers, chillers, compressors, packaging line...' },
    { key: 'goals', module: 'goals', prompt: 'What should improve: machine uptime, energy by line, peak demand, power quality, predictive maintenance, safety visibility, or production reporting?', placeholder: 'List industrial automation and business goals...' },
    { key: 'energy', module: 'energy', prompt: 'What are the major energy loads and energy assets: PV, battery, EV fleet, compressors, chillers, motors, VFDs, pumps, ovens, or peak tariff?', placeholder: 'Describe load profile, tariff problem, and monitoring goals...' },
    { key: 'identity', module: 'identity', prompt: 'Do you need staff/visitor access, machine-area permissions, OT network isolation, CCTV AI, or safety boundary rules?', placeholder: 'Access, safety, OT/IT separation, restricted areas...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and service/SLA period should we design around?', placeholder: 'Example: 50k-300k EUR, 5-year lifecycle support, production downtime sensitive' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for factory engineering follow-up?', placeholder: 'Name, role, company email, phone or Telegram' },
  ],
  hotel: [
    { key: 'location', module: 'location', prompt: 'Where is the hotel or serviced apartment located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'How many rooms, floors, room types, common areas, and service areas are involved?', placeholder: 'Example: 48 rooms, 5 floors, lobby, corridors...' },
    { key: 'existing', module: 'existing', prompt: 'What existing door locks, thermostats, CCTV, PMS, network, or room controls exist?', placeholder: 'Describe current hotel systems...' },
    { key: 'goals', module: 'goals', prompt: 'What should improve: guest welcome mode, away energy saving, housekeeping permissions, room status, or maintenance?', placeholder: 'List guest and operation goals...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need HVAC energy saving, room occupancy sensing, solar dashboard, or monthly hotel reports?', placeholder: 'Energy and room-control needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we design around?', placeholder: 'Example: 50k-100k EUR, 5-year lifecycle support' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for hotel follow-up?', placeholder: 'Name, email, phone or Telegram' },
  ],
  energy: [
    { key: 'location', module: 'location', prompt: 'Where is the solar or energy site located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What building or site loads should be monitored: office, warehouse, hotel, EV, critical loads?', placeholder: 'Describe site and load profile...' },
    { key: 'existing', module: 'existing', prompt: 'What PV, inverter, battery, meter, EV charger, or EMS equipment already exists?', placeholder: 'Inverter brand, battery, meters, EV chargers...' },
    { key: 'goals', module: 'goals', prompt: 'What do you want to optimize: PV self-consumption, peak tariff, EV charging, battery, alerts, or reports?', placeholder: 'List energy optimization goals...' },
    { key: 'energy', module: 'energy', prompt: 'Do you need tariff rules, load priority, anomaly alarms, monthly reports, or remote maintenance?', placeholder: 'Describe energy logic and reporting needs...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we assume?', placeholder: 'Example: 15k-50k EUR, 3-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this energy assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  storage: [
    { key: 'location', module: 'location', prompt: 'Where is the storage facility located? Please include country and city.', placeholder: 'Example: Belgrade, Serbia' },
    { key: 'storage_type', module: 'storage_type', prompt: 'What type of storage is this and how many rooms or zones: walk-in cold room, freezer, pharmacy fridge, ambient warehouse, or laboratory?', placeholder: 'Example: 3 cold rooms + 1 freezer, food distribution' },
    { key: 'temperature_humidity', module: 'temperature_humidity', prompt: 'What temperature and humidity ranges must each room stay within?', placeholder: 'Example: 2-8°C chilled, -18°C frozen, <60% RH' },
    { key: 'compliance_use', module: 'compliance_use', prompt: 'Is this for food (HACCP) or pharmaceutical / medical (GDP) goods, and do you need audit-ready compliance reports?', placeholder: 'Example: pharmaceutical, monthly GDP audit reports required' },
    { key: 'outage', module: 'outage', prompt: 'What is the power-failure risk, and do you already have any temperature logging or monitoring today?', placeholder: 'Example: occasional outages, only manual paper logs now' },
    { key: 'alert_channels', module: 'alert_channels', prompt: 'How should outage and out-of-range alerts reach you: SMS, Telegram, email, phone call, or in-app?', placeholder: 'Example: Telegram + email, phone call for critical alarms' },
    { key: 'monitoring_points', module: 'monitoring_points', prompt: 'How many monitoring points do you need in total across all rooms, doors, and sensors?', placeholder: 'Example: about 24 points' },
    { key: 'calibration_cycle', module: 'calibration_cycle', prompt: 'How often must sensors be calibrated, and over how many years do you want the service to run?', placeholder: 'Example: annual calibration, 3-year service term' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and service period should we design around?', placeholder: 'Example: 6k-18k EUR, 3-year compliance support' },
    { key: 'contact', module: 'contact', prompt: 'Finally, who should AinerWise contact for this StorageGuard assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  kitchen: [
    { key: 'location', module: 'location', prompt: 'Where is the kitchen / venue located?', placeholder: 'Country and city' },
    { key: 'kitchen_count', module: 'kitchen_count', prompt: 'How many kitchens or cooking lines, and is there an automatic gas cut-off valve?', placeholder: 'Example: 2 kitchens, existing gas valve' },
    { key: 'gas_type', module: 'gas_type', prompt: 'What gas type is used (natural gas, LPG), and do you need CO and water-leak monitoring?', placeholder: 'Example: natural gas + CO + leak under sinks' },
    { key: 'alarm_contacts', module: 'alarm_contacts', prompt: 'Who should receive alarms (manager, property, maintenance) and via which channels?', placeholder: 'Example: manager SMS, property Telegram, call escalation' },
    { key: 'service_term', module: 'service_term', prompt: 'Do you need annual safety inspection certificates, and over how many years?', placeholder: 'Example: annual inspection, 3-year AMC' },
    { key: 'budget', module: 'budget', prompt: 'What budget range should we design around?', placeholder: 'Example: 6k-16k EUR' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this KitchenGuard assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  water: [
    { key: 'location', module: 'location', prompt: 'Where is the water / effluent site located?', placeholder: 'Country and city' },
    { key: 'water_system', module: 'water_system', prompt: 'What water system is this (effluent, pool, cooling, process) and how many discharge / sample points?', placeholder: 'Example: factory effluent, 2 outfalls' },
    { key: 'parameters', module: 'parameters', prompt: 'Which parameters must be monitored: pH, conductivity, turbidity, COD, temperature?', placeholder: 'Example: pH, COD, turbidity' },
    { key: 'reporting', module: 'reporting', prompt: 'Do you need government / environmental compliance reports, and how often?', placeholder: 'Example: monthly regulator report' },
    { key: 'service_term', module: 'service_term', prompt: 'How often must probes be calibrated / replaced, and over how many years of service?', placeholder: 'Example: quarterly calibration, 3-year service' },
    { key: 'budget', module: 'budget', prompt: 'What budget range should we assume?', placeholder: 'Example: 12k-30k EUR' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this AquaGuard assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  asset: [
    { key: 'location', module: 'location', prompt: 'Where are the assets / sites located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What assets and how many, indoor or outdoor, and across how many sites?', placeholder: 'Example: 300 tools, 2 warehouses' },
    { key: 'goals', module: 'goals', prompt: 'What do you need: geofence alerts, inventory counts, location accuracy, multi-site reports?', placeholder: 'Example: geofence + inventory' },
    { key: 'monitoring_points', module: 'monitoring_points', prompt: 'Roughly how many tags / assets to track?', placeholder: 'Example: about 300 tags' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and tag-subscription period should we assume?', placeholder: 'Example: 9k-22k EUR, 3-year' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this AssetPulse assessment?', placeholder: 'Name, email, phone or Telegram' },
  ],
  agri: [
    { key: 'location', module: 'location', prompt: 'Where is the greenhouse / farm located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What scale: area, number of zones / greenhouses, crops?', placeholder: 'Example: 2 greenhouses, 1 ha' },
    { key: 'goals', module: 'goals', prompt: 'What to monitor / optimize: soil moisture, climate, irrigation, fertilizer?', placeholder: 'Example: soil + irrigation' },
    { key: 'budget', module: 'budget', prompt: 'Is this concept, pilot, or implementation, and what budget?', placeholder: 'Example: pilot first' },
    { key: 'contact', module: 'contact', prompt: 'Who should AinerWise contact for this AgriBrain concept?', placeholder: 'Name, email, phone or Telegram' },
  ],
  retrofit: [
    { key: 'location', module: 'location', prompt: 'Where is the existing building located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What building type, area, floors, and rooms/zones are involved?', placeholder: 'Describe building structure...' },
    { key: 'existing', module: 'existing', prompt: 'What systems exist today and what is outdated or painful?', placeholder: 'Wiring, CCTV, access, HVAC, network, lighting...' },
    { key: 'goals', module: 'goals', prompt: 'What is the retrofit goal: basic control, security upgrade, energy dashboard, KNX, or Home Assistant?', placeholder: 'Describe desired retrofit outcome...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and support period should we assume?', placeholder: 'Example: 5k-15k EUR, 3-year support' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for retrofit follow-up?', placeholder: 'Name, email, phone or Telegram' },
  ],
  custom: [
    { key: 'location', module: 'location', prompt: 'Where will this future building or concept project be located?', placeholder: 'Country and city' },
    { key: 'building', module: 'site', prompt: 'What kind of building or site is this, and what scale should we assume?', placeholder: 'Describe building type, area, floors, rooms...' },
    { key: 'goals', module: 'goals', prompt: 'What future capability are you imagining: local AI brain, robots, digital human, autonomous energy, identity, or predictive maintenance?', placeholder: 'Describe the vision...' },
    { key: 'existing', module: 'existing', prompt: 'What systems already exist or must be integrated?', placeholder: 'KNX, HA, CCTV, HVAC, solar, robot platform...' },
    { key: 'budget', module: 'budget', prompt: 'What budget range and phase should this start with: concept, Phase-1 proposal, or implementation?', placeholder: 'Example: design-only first, 5-year support later' },
    { key: 'contact', module: 'contact', prompt: 'Who should we contact for custom engineering review?', placeholder: 'Name, email, phone or Telegram' },
  ],
}

const selectedKey = ref<CategoryKey | null>(null)
const targetLevel = ref<LevelKey>('L3')
const messages = ref<Array<{ id: number; role: 'ai' | 'user'; text: string; tag: string }>>([])
const answers = reactive<Record<string, string>>({})
const currentIndex = ref(0)
const draft = ref('')
const submitted = ref(false)
const phase1Requested = ref(false)
const loading = ref(false)
const error = ref('')
const chatScroll = ref<HTMLElement | null>(null)

const selectedCategory = computed(() => projectCategories.find((item) => item.key === selectedKey.value) || null)
const targetLevelMeta = computed(() => levelOptions.find((item) => item.key === targetLevel.value) || levelOptions[0])
const currentQuestions = computed(() => selectedKey.value ? questionBank[selectedKey.value] : [])
const currentQuestion = computed(() => currentQuestions.value[currentIndex.value] || null)
const answeredCount = computed(() => Object.keys(answers).filter((key) => answers[key]?.trim()).length)
const progress = computed(() => {
  if (!selectedCategory.value) return 0
  const total = currentQuestions.value.length + 1
  return Math.min(100, Math.round(((answeredCount.value + 1) / total) * 100))
})

const leadScore = computed(() => {
  let score = progress.value >= 85 ? 20 : progress.value >= 50 ? 10 : 0
  if (answers.budget) score += /50|100|premium|enterprise|over/i.test(answers.budget) ? 20 : 12
  if (/3|5|8|10|lifecycle/i.test(answers.budget || '')) score += 15
  if (extractEmail(answers.contact || '')) score += 10
  if (/telegram|whatsapp|@|\+/i.test(answers.contact || '')) score += 10
  if (targetLevel.value === 'L4' || targetLevel.value === 'L5') score += 10
  if (phase1Requested.value) score += 25
  return Math.min(score, 100)
})

const leadStage = computed(() => {
  if (leadScore.value >= 85) return 'Phase-1 Ready'
  if (leadScore.value >= 70) return 'Qualified Lead'
  if (leadScore.value >= 45) return 'Warm Lead'
  return 'Cold Lead'
})

const proposalPlans = computed(() => {
  const industrialProject = selectedKey.value === 'factory'
  const largeProject = ['school', 'office', 'hotel'].includes(selectedKey.value || '')
  const ranges = industrialProject
    ? { budget: '30k-100k EUR', standard: '100k-300k EUR', premium: '300k-800k+ EUR' }
    : largeProject
    ? { budget: '15k-50k EUR', standard: '50k-100k EUR', premium: '100k-250k EUR' }
    : { budget: '5k-15k EUR', standard: '15k-50k EUR', premium: '50k-120k EUR' }
  return [
    {
      tier: 'budget',
      name: 'Budget Plan',
      level: 'L1-L2',
      complexity: 'Starter retrofit',
      risk: 'Medium risk',
      device: ranges.budget,
      support: '1-3 years',
      summary: industrialProject ? 'Starter industrial visibility for selected meters, machine status, OT gateway, and essential alerts.' : 'Basic control, essential CCTV/access/network/energy monitoring, and limited automation.',
    },
    {
      tier: 'standard',
      name: 'Standard Plan',
      level: 'L2-L3',
      complexity: 'Practical delivery',
      risk: 'Managed risk',
      device: ranges.standard,
      support: '3-5 years',
      summary: industrialProject ? 'Line-level energy dashboard, PLC/SCADA integration, compressor/chiller scheduling, and remote maintenance.' : 'Sensor automation, energy dashboard, remote maintenance, and service-ready device choices.',
    },
    {
      tier: 'premium_ai',
      name: 'Premium AI Plan',
      level: targetLevel.value === 'L5' ? 'L4-L5' : 'L3-L4',
      complexity: 'Manual review required',
      risk: 'High review',
      device: ranges.premium,
      support: '5-10 years',
      summary: industrialProject ? 'AI anomaly detection, predictive maintenance, local OT data gateway, production energy intelligence, and SLA planning.' : 'AI analysis, identity/access intelligence, local AI options, and deeper lifecycle planning.',
    },
    {
      tier: 'future_autonomous',
      name: 'Future Autonomous Plan',
      level: 'L5-L6',
      complexity: 'Concept demo',
      risk: 'Custom only',
      device: 'Custom engineering',
      support: 'Custom SLA',
      summary: 'Robot-ready and autonomous facility concepts. No fixed price before engineering review.',
    },
  ]
})

const previewModules = computed(() => {
  const modules = selectedKey.value === 'storage'
    ? [
        { key: 'category', label: 'Project Category', summary: selectedCategory.value?.label || 'Choose project type' },
        { key: 'location', label: 'Site Location', summary: answers.location || 'Country and city required' },
        { key: 'storage_type', label: 'Storage Type & Rooms', summary: answers.storage_type || 'Cold room, freezer, pharmacy fridge, warehouse...' },
        { key: 'temperature_humidity', label: 'Temperature & Humidity', summary: answers.temperature_humidity || 'e.g. 2-8°C, -18°C, <60% RH' },
        { key: 'compliance_use', label: 'Compliance Use', summary: answers.compliance_use || 'Food (HACCP) or pharma (GDP), audit reports' },
        { key: 'outage', label: 'Outage Protection', summary: answers.outage || 'Power-failure risk and current logging' },
        { key: 'alert_channels', label: 'Alert Channels', summary: answers.alert_channels || 'SMS, Telegram, email, phone call' },
        { key: 'monitoring_points', label: 'Monitoring Points', summary: answers.monitoring_points || 'Total points across rooms and doors' },
        { key: 'calibration_cycle', label: 'Calibration & Service', summary: answers.calibration_cycle || 'Calibration cycle and service term' },
        { key: 'budget', label: 'Budget & Service Period', summary: answers.budget || 'Budget range and support years' },
        { key: 'contact', label: 'Contact', summary: answers.contact || 'Name and email/phone' },
      ]
    : [
        { key: 'category', label: 'Project Category', summary: selectedCategory.value?.label || 'Choose project type' },
        { key: 'location', label: 'Site Location', summary: answers.location || 'Country and city required' },
        { key: 'site', label: 'Building / Site Profile', summary: answers.building || 'Area, rooms, floors, or loads' },
        { key: 'existing', label: 'Existing Systems', summary: answers.existing || 'Network, CCTV, HVAC, solar, access, KNX...' },
        { key: 'production', label: 'Production / Machines', summary: answers.production || 'Factory lines, machines, robots, utilities, PLC/SCADA' },
        { key: 'goals', label: 'Smart Goals', summary: answers.goals || 'Energy, security, comfort, AI, maintenance...' },
        { key: 'identity', label: 'Identity & Access', summary: answers.identity || 'Only needed for projects with access/AI identity' },
        { key: 'energy', label: 'Energy & Solar', summary: answers.energy || 'PV, battery, EV, tariffs, reports' },
        { key: 'budget', label: 'Budget & Service Period', summary: answers.budget || 'Budget range and support years' },
        { key: 'contact', label: 'Contact', summary: answers.contact || 'Name and email/phone' },
      ]
  const activeModule = currentQuestion.value?.module
  return modules.map((module) => ({
    ...module,
    done: module.key === 'category' || Boolean(answers[module.key]),
    active: module.key === activeModule,
  }))
})

function scrollChat() {
  nextTick(() => {
    if (chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight
  })
}

function pushAi(text: string, tag = 'gap_question') {
  messages.value.push({ id: Date.now() + Math.random(), role: 'ai', text, tag })
  scrollChat()
}

function pushUser(text: string) {
  messages.value.push({ id: Date.now() + Math.random(), role: 'user', text, tag: 'intake_chat' })
  scrollChat()
}

async function startCategory(key: CategoryKey) {
  selectedKey.value = key
  const category = projectCategories.find((item) => item.key === key)
  targetLevel.value = category?.level.includes('L5') ? 'L5' : 'L3'
  messages.value = []
  Object.keys(answers).forEach((answerKey) => delete answers[answerKey])
  currentIndex.value = 0
  submitted.value = false
  phase1Requested.value = false
  aiComplete.value = false

  // AI agent opening question (when configured); otherwise scripted first prompt.
  if (assistant.enabled.value) {
    loading.value = true
    try {
      const res = await assistant.ask(key, [{ role: 'user', content: `I want an AI facility assessment for: ${category?.label}.` }], { target_intelligence_level: targetLevel.value })
      if (res?.configured && res.reply) {
        pushAi(res.reply, res.complete ? 'proposal_ready' : 'ai_analyze')
        if (res.complete) aiComplete.value = true
        return
      }
    } catch {
      // fall through to scripted
    } finally {
      loading.value = false
    }
  }
  pushAi(`Great. I will create a ${category?.label} assessment and ask only the next missing smart-building question.\n\n${currentQuestion.value?.prompt}`)
}

function askNextQuestion() {
  if (currentQuestion.value) {
    pushAi(currentQuestion.value.prompt, 'ai_analyze')
  } else {
    pushAi('I have enough information for a preliminary AI estimate. You can submit this assessment for admin review.', 'proposal_ready')
  }
}

const readyToSubmit = computed(() => aiComplete.value || !currentQuestion.value)

async function sendMessage() {
  error.value = ''
  if (!draft.value.trim()) {
    if (readyToSubmit.value && !submitted.value) await submitLead()
    return
  }
  const text = draft.value.trim()
  draft.value = ''
  pushUser(text)

  // AI agent path (when configured in Admin → Integrations).
  if (assistant.enabled.value && selectedCategory.value) {
    loading.value = true
    try {
      const history = messages.value.map((m) => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text }))
      const res = await assistant.ask(selectedCategory.value.key, history, { ...answers, target_intelligence_level: targetLevel.value })
      if (res?.configured) {
        mergeExtracted(res.extracted)
        if (res.reply) pushAi(res.reply, res.complete ? 'proposal_ready' : 'ai_analyze')
        if (res.complete) aiComplete.value = true
        return
      }
    } catch {
      // fall through to scripted flow
    } finally {
      loading.value = false
    }
  }

  // Scripted fallback flow.
  if (currentQuestion.value) {
    answers[currentQuestion.value.module] = text
    currentIndex.value += 1
    const next = currentQuestion.value
    if (next) {
      pushAi(`Captured. Next missing item:\n\n${next.prompt}`)
      return
    }
    pushAi(`Thanks. The intake is now complete enough for a preliminary estimate.\n\nTarget level: ${targetLevel.value} ${targetLevelMeta.value.label}\n\n${estimateNotice}`, 'proposal_ready')
    return
  }

  await submitLead()
}

async function requestPhase1Proposal() {
  phase1Requested.value = true
  pushUser('Request Phase-1 Proposal')
  pushAi('Understood. I will mark this as Phase-1 intent. Human review is required before any detailed BOM, architecture diagram, supplier confirmation, or final quotation.', 'phase1_requested')
  await submitLead(true)
}

function resetForge() {
  selectedKey.value = null
  messages.value = []
  Object.keys(answers).forEach((answerKey) => delete answers[answerKey])
  currentIndex.value = 0
  submitted.value = false
  phase1Requested.value = false
  aiComplete.value = false
  error.value = ''
}

function extractEmail(value: string) {
  return value.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] || ''
}

function budgetToRange(value: string) {
  const lower = value.toLowerCase()
  if (lower.includes('100')) return 'over_100k'
  if (lower.includes('50')) return '50k_100k'
  if (lower.includes('15')) return '15k_50k'
  if (lower.includes('5')) return '5k_15k'
  return value || 'to_be_confirmed'
}

async function submitLead(requestPhase1 = false) {
  if (!selectedCategory.value) return
  loading.value = true
  phase1Requested.value = requestPhase1 || phase1Requested.value
  try {
    const { getAttribution } = useMarketingAttribution()
    const transcript = messages.value.map((message) => `${message.role.toUpperCase()}: ${message.text}`).join('\n\n')
    await apiFetch('/leads', {
      method: 'POST',
      body: {
        ...getAttribution(),
        project_type: selectedCategory.value.label,
        country: answers.location || '',
        budget_range: budgetToRange(answers.budget || ''),
        systems_needed_json: selectedCategory.value.systems,
        description: [
          `AI Project Forge transcript for ${selectedCategory.value.label}.`,
          `Target intelligence level: ${targetLevel.value} ${targetLevelMeta.value.label}.`,
          `Lead score: ${leadScore.value} (${leadStage.value}).`,
          phase1Requested.value ? 'Customer requested paid Phase-1 Proposal.' : 'Customer has not requested Phase-1 Proposal yet.',
          estimateNotice,
          transcript,
        ].join('\n\n'),
        contact_name: answers.contact?.split(',')?.[0] || 'AI Assessment Lead',
        contact_email: extractEmail(answers.contact || '') || 'unknown@ainerwise.local',
        contact_phone: answers.contact || '',
        site_info_json: {
          // Include every answered module key so new solution lines (KitchenGuard,
          // AquaGuard, AssetPulse, AgriBrain) land their intake fields for AI analysis.
          ...answers,
          target_intelligence_level: targetLevel.value,
          category_key: selectedCategory.value.key,
          lead_score: leadScore.value,
          lead_stage: leadStage.value,
          phase1_requested: phase1Requested.value,
          proposal_tiers: proposalPlans.value,
          building: answers.building,
          existing_systems: answers.existing,
          production_machines: answers.production,
          smart_goals: answers.goals,
          identity_access: answers.identity,
          energy_solar: answers.energy,
          storage_type: answers.storage_type,
          temperature_humidity: answers.temperature_humidity,
          compliance_use: answers.compliance_use,
          outage_protection: answers.outage,
          alert_channels: answers.alert_channels,
          monitoring_points: answers.monitoring_points,
          calibration_cycle: answers.calibration_cycle,
          budget_and_service: answers.budget,
          estimate_notice: estimateNotice,
          transcript: messages.value,
        },
      },
    })
    submitted.value = true
    pushAi('Submitted. AinerWise admin will review the preliminary AI estimate before any quote or commitment.', 'submitted')
  } catch (e: any) {
    error.value = e?.data?.detail || 'Submission failed'
  } finally {
    loading.value = false
  }
}
</script>
