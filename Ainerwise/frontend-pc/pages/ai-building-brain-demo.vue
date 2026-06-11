<template>
  <div class="bg-slate-950 text-white">
    <section class="relative overflow-hidden">
      <ClientOnly>
        <BuildingBrain3D :level="selectedLevel" :scenario-key="activeScenario.key" />
        <template #fallback>
          <div class="min-h-[640px] bg-slate-950"></div>
        </template>
      </ClientOnly>

      <div class="absolute inset-0 z-10 pointer-events-none">
        <div class="container-main h-full px-4 sm:px-6 lg:px-8 py-12 lg:py-16 flex flex-col justify-between">
          <div class="max-w-2xl pointer-events-auto">
            <p class="text-sm font-semibold uppercase tracking-wider text-emerald-300">
              AI Smart Building Brain
            </p>
            <h1 class="mt-4 text-4xl sm:text-5xl font-bold leading-tight text-white">
              Walk Into the AinerWise AI Building Brain
            </h1>
            <p class="mt-5 text-lg text-slate-300">
              A 3D interactive page for future-ready buildings and factories. Switch scenarios
              and L3-L5 intelligence to see AI, PV energy, EV charging, robots, smart access,
              industrial equipment, and serviceable automation become one connected system.
            </p>
            <div class="mt-7 flex flex-col sm:flex-row gap-3">
              <NuxtLink to="/submit-requirement" class="btn-primary px-6 py-3 font-semibold text-center">
                Start Chat Assessment
              </NuxtLink>
              <NuxtLink to="/demo-login" class="glass-panel text-cyan-100 px-6 py-3 font-semibold hover:bg-white/10 transition text-center">
                Open Buyer Preview
              </NuxtLink>
            </div>
          </div>

          <div class="pointer-events-auto space-y-4">
            <div>
              <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">Choose target intelligence</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="level in levelOptions"
                  :key="level.key"
                  type="button"
                  class="pc-chip"
                  :class="selectedLevel === level.key ? 'pc-chip-active' : 'pc-chip-inactive'"
                  @click="selectedLevel = level.key"
                >
                  {{ level.key }} · {{ level.label }}
                </button>
              </div>
            </div>

            <div>
              <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-300">Switch building scenario</p>
              <div class="flex flex-wrap gap-2 pb-2 xl:max-w-[calc(100%-470px)]">
                <button
                  v-for="scenario in scenarios"
                  :key="scenario.key"
                  type="button"
                  class="pc-chip shrink-0"
                  :class="activeScenario.key === scenario.key ? 'border-emerald-400 bg-emerald-400 text-slate-950' : 'pc-chip-inactive'"
                  @click="activeKey = scenario.key"
                >
                  {{ scenario.name }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="pc-section-muted">
      <div class="container-main section-padding">
        <div class="grid grid-cols-1 lg:grid-cols-[0.9fr_1.1fr] gap-8">
          <div>
            <p class="pc-kicker">{{ activeScenario.type }}</p>
            <h2 class="mt-2 text-3xl font-bold text-white">{{ activeScenario.name }}</h2>
            <p class="mt-4 text-slate-300">{{ activeScenario.positioning }}</p>

            <div class="mt-6 grid grid-cols-2 gap-3">
              <div class="pc-feature-card">
                <p class="pc-kicker-muted">Recommended level</p>
                <p class="mt-1 font-bold text-primary-300">{{ selectedLevel }} · {{ selectedLevelMeta.name }}</p>
              </div>
              <div class="pc-feature-card">
                <p class="pc-kicker-muted">Delivery boundary</p>
                <p class="mt-1 font-bold text-amber-300">{{ selectedLevelMeta.boundary }}</p>
              </div>
            </div>

            <div class="pc-feature-card mt-4">
              <p class="pc-kicker-muted">Selected intelligence behavior</p>
              <p class="mt-2 text-sm text-slate-300">{{ selectedLevelMeta.description }}</p>
            </div>

            <div class="mt-6 pc-notice-amber">
              AI estimate only. Final quote requires manual review, customer meeting,
              site survey, supplier confirmation, and signed contract.
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div v-for="block in capabilityBlocks" :key="block.title" class="pc-feature-card">
              <p class="pc-kicker-muted">{{ block.kicker }}</p>
              <h3 class="mt-2 font-bold text-white">{{ block.title }}</h3>
              <ul class="mt-3 space-y-2 text-sm text-slate-300">
                <li v-for="item in activeScenario[block.key]" :key="item" class="flex gap-2">
                  <span class="mt-2 h-1.5 w-1.5 shrink-0 bg-primary-400 rounded-full"></span>
                  <span>{{ item }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div class="mt-12">
          <div class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-6">
            <div>
              <p class="pc-kicker">Four Proposal Directions</p>
              <h2 class="mt-2 text-2xl font-bold text-white">From practical retrofit to future autonomous system</h2>
            </div>
            <NuxtLink to="/submit-requirement" class="text-sm font-semibold text-primary-300 hover:text-primary-200">
              Generate your own estimate &rarr;
            </NuxtLink>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <div v-for="tier in proposalTiers" :key="tier.name" class="pc-feature-card">
              <p class="pc-kicker-muted">{{ tier.level }}</p>
              <h3 class="mt-2 font-bold text-white">{{ tier.name }}</h3>
              <p class="mt-2 text-sm text-slate-300">{{ tier.text }}</p>
              <div class="mt-4 text-sm">
                <p class="font-semibold text-white">{{ tier.estimate }}</p>
                <p class="mt-1 text-xs text-slate-400">{{ tier.note }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-12">
          <p class="pc-kicker">Feature Boundaries</p>
          <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div v-for="tag in featureTags" :key="tag.name" class="pc-feature-card">
              <p class="font-bold text-white">{{ tag.name }}</p>
              <p class="mt-2 text-sm text-slate-300">{{ tag.text }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ alias: ['/ai-building-brain'] })

const activeKey = ref('villa')
const selectedLevel = ref<'L3' | 'L4' | 'L5'>('L5')

const levelOptions = [
  {
    key: 'L3',
    label: 'Energy Optimized',
    name: 'Energy Optimized Building',
    boundary: 'Available Now / Project Dependent',
    description: 'Best for solar, meters, HVAC schedules, scene control, dashboards, alerts, and monthly reports.',
  },
  {
    key: 'L4',
    label: 'AI Assisted',
    name: 'AI Assisted Building',
    boundary: 'Advanced Custom',
    description: 'Adds AI anomaly detection, admin review summaries, CCTV/energy insights, and AI-generated next-step recommendations.',
  },
  {
    key: 'L5',
    label: 'Local AI Brain',
    name: 'Local AI Building Brain',
    boundary: 'Advanced Custom / Future-Ready',
    description: 'Adds local AI box, identity-aware permissions, privacy-first offline workflows, and cross-system orchestration.',
  },
] as const

const selectedLevelMeta = computed(() => levelOptions.find((item) => item.key === selectedLevel.value) || levelOptions[0])

const scenarios = [
  {
    key: 'villa',
    name: 'Smart Villa / Future Home',
    type: 'Residential AI Brain',
    level: 'L2-L5',
    boundary: 'Available Now to Advanced Custom',
    positioning: 'A local AI-ready family building system that connects identity, rooms, energy, security, kitchen, bathroom, bedroom, EV, garden, and service.',
    sense: ['Family member identity', 'Presence and room occupancy', 'Water leak, smoke, gas, humidity', 'Solar, battery, and EV charging status'],
    control: ['Lighting scenes and curtains', 'HVAC comfort modes', 'Door, visitor, and garage permissions', 'Smart bedroom, kitchen, and bathroom equipment'],
    optimize: ['Sleep and comfort curves', 'PV-first EV charging', 'Low-tariff appliance scheduling', 'Unoccupied room energy saving'],
    maintain: ['Remote gateway health', 'Firmware and backup checks', 'Spare parts planning', 'Annual lifecycle review'],
  },
  {
    key: 'school',
    name: 'School Campus',
    type: 'AI Campus Brain',
    level: 'L2-L4',
    boundary: 'Project Dependent',
    positioning: 'A campus operating layer for classroom comfort, safety, network visibility, energy reporting, and maintenance workflows.',
    sense: ['Teacher, student, and visitor zones', 'CO2, temperature, humidity, and noise', 'Camera and network device health', 'After-school occupancy'],
    control: ['Classroom lighting and HVAC schedules', 'Lab and machine room access', 'Visitor area permissions', 'Campus alert workflows'],
    optimize: ['Class schedule energy saving', 'Roof solar visibility', 'High-consumption building ranking', 'Daily facility summary'],
    maintain: ['Offline camera alerts', 'AP and switch status', 'Repair ticket creation', 'Monthly energy reports'],
  },
  {
    key: 'apartment',
    name: 'Apartment Building',
    type: 'AI Property Brain',
    level: 'L2-L4',
    boundary: 'Available Now / Project Dependent',
    positioning: 'A property management layer for common area energy, access, CCTV, parking, tenant experience, repair workflow, and lifecycle service.',
    sense: ['Common area occupancy', 'Parking license plates', 'Public lighting and meter data', 'Visitor and parcel access events'],
    control: ['Common area lighting', 'Visitor QR access', 'Parking gate permissions', 'Tenant service notifications'],
    optimize: ['Shared area energy allocation', 'PV for public loads', 'Maintenance priority', 'Monthly property reports'],
    maintain: ['Door access logs', 'Camera status', 'Meter gateway health', 'Preventive maintenance reminders'],
  },
  {
    key: 'office',
    name: 'Enterprise Office Building',
    type: 'AI Facility Brain',
    level: 'L2-L5',
    boundary: 'Advanced Custom for AI identity',
    positioning: 'A facility system for visitor management, meeting rooms, employee comfort, IT visibility, access control, and energy optimization.',
    sense: ['Employee and visitor presence', 'Meeting room usage', 'IT room temperature and UPS status', 'Network AP and switch health'],
    control: ['Meeting room scenes', 'Visitor temporary access', 'Floor-level HVAC schedules', 'Screen, lighting, and curtain modes'],
    optimize: ['Empty-area energy saving', 'Workspace utilization', 'Daily facility summary', 'High-consumption floor alerts'],
    maintain: ['CCTV and access uptime', 'Network incident tracking', 'Firmware update planning', 'SLA-based service workflow'],
  },
  {
    key: 'factory',
    name: 'Factory / Industrial Plant',
    type: 'AI Industrial Energy Brain',
    level: 'L3-L5',
    boundary: 'Project Dependent / Advanced Custom',
    positioning: 'An industrial operating layer for production lines, machinery, PLC/SCADA, OT networks, compressed air, chillers, motors, robots, PV/battery, safety visibility, and lifecycle maintenance.',
    sense: ['Machine status, runtime, alarms, and downtime', 'Line-level energy, power quality, and peak demand', 'Compressed air, chiller, motor, VFD, pump, and boiler loads', 'PLC/SCADA/Modbus/MQTT/OPC-UA integration signals'],
    control: ['Energy schedules for compressors and chillers', 'Non-safety setpoint recommendations', 'Robot/AGV-ready dispatch hooks', 'Maintenance work order triggers'],
    optimize: ['Peak demand and load shedding', 'Machine-level energy waste', 'Production schedule energy planning', 'Anomaly detection and predictive maintenance'],
    maintain: ['OT gateway and network health', 'PLC/SCADA integration notes', 'Critical spare parts and SLA planning', 'Safety boundary and downtime review'],
  },
  {
    key: 'hotel',
    name: 'Hotel / Serviced Apartment',
    type: 'Guest Experience + Energy',
    level: 'L2-L4',
    boundary: 'Available Now / Project Dependent',
    positioning: 'A guest-room control and remote maintenance system that reduces energy waste while improving check-in, comfort, and room status visibility.',
    sense: ['Guest check-in status', 'Room occupancy', 'Housekeeping access', 'Public area CCTV and door events'],
    control: ['Welcome and away scenes', 'Room HVAC and lighting', 'Curtains and panels', 'Staff permissions'],
    optimize: ['Vacant room energy saving', 'Room comfort presets', 'Monthly energy report', 'Preventive maintenance plan'],
    maintain: ['Room device health', 'Remote troubleshooting', 'Spare panel planning', 'Service package tracking'],
  },
  {
    key: 'energy',
    name: 'Solar + Energy Site',
    type: 'AI Energy Brain',
    level: 'L3-L5',
    boundary: 'Project Dependent',
    positioning: 'A visibility and optimization layer for PV, battery storage, EV charging, key building loads, tariffs, alerts, and energy reporting.',
    sense: ['PV generation', 'Battery SOC', 'Inverter and meter state', 'EV charger sessions'],
    control: ['Load priority rules', 'EV charging windows', 'Battery discharge strategy', 'Critical load alerts'],
    optimize: ['Peak tariff reduction', 'PV self-consumption', 'Fault and anomaly detection', 'Monthly AI energy advice'],
    maintain: ['Inverter health', 'Meter gateway status', 'Remote diagnostics', 'Lifecycle service plan'],
  },
]

const activeScenario = computed(() => scenarios.find((item) => item.key === activeKey.value) || scenarios[0])

const capabilityBlocks = [
  { key: 'sense', kicker: 'Sense', title: 'What the building can know' },
  { key: 'control', kicker: 'Control', title: 'What the system can operate' },
  { key: 'optimize', kicker: 'Optimize', title: 'Where AI can help' },
  { key: 'maintain', kicker: 'Maintain', title: 'How service stays alive' },
] as const

const proposalTiers = [
  { name: 'Budget Plan', level: 'L1-L2', estimate: 'Basic estimated range', note: 'Good for first retrofit and limited scope.', text: 'Connected control, essential sensors, CCTV/access basics, and 1-3 year support.' },
  { name: 'Standard Plan', level: 'L2-L3', estimate: 'Most practical for real projects', note: 'Recommended default for early AinerWise delivery.', text: 'Sensor automation, energy monitoring, remote maintenance, and service-ready hardware.' },
  { name: 'Premium AI Plan', level: 'L4-L5', estimate: 'Manual review required', note: 'Needs site, supplier, and engineering validation.', text: 'AI analytics, identity-aware access, local AI box, CCTV AI, and advanced energy logic.' },
  { name: 'Future Autonomous Plan', level: 'L5-L6', estimate: 'Custom engineering required', note: 'No fixed price shown.', text: 'Robot-ready building, predictive maintenance, autonomous energy decisions, and future facility brain.' },
]

const featureTags = [
  { name: 'Available Now', text: 'Can usually be delivered with current hardware and normal project checks.' },
  { name: 'Project Dependent', text: 'Depends on site, wiring, protocols, product availability, and installer capability.' },
  { name: 'Advanced Custom', text: 'Requires manual engineering review and a paid design phase.' },
  { name: 'Future-Ready', text: 'Architecture can reserve this upgrade path without promising delivery today.' },
  { name: 'Concept Demo', text: 'Used to explain the vision, not as a quotation commitment.' },
]
</script>
