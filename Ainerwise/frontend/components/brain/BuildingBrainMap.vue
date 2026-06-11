<template>
  <div class="brain-shell" :class="{ compact }">
    <svg class="brain-lines" viewBox="0 0 720 520" aria-hidden="true">
      <line
        v-for="node in nodes"
        :key="`line-${node.key}`"
        x1="360"
        y1="260"
        :x2="node.x"
        :y2="node.y"
        :class="['brain-line', activeKey === node.key ? 'is-active' : '']"
      />
    </svg>

    <button
      class="brain-core"
      type="button"
      @mouseenter="activeKey = 'core'"
      @focus="activeKey = 'core'"
    >
      <span class="core-kicker">AinerWise</span>
      <strong>AI Brain</strong>
      <span>KNX + Energy + Security + Service</span>
    </button>

    <button
      v-for="node in nodes"
      :key="node.key"
      type="button"
      class="brain-node"
      :class="[`tone-${node.tone}`, activeKey === node.key ? 'is-active' : '']"
      :style="{ left: `${node.xPercent}%`, top: `${node.yPercent}%` }"
      @mouseenter="activeKey = node.key"
      @focus="activeKey = node.key"
    >
      <span class="node-dot"></span>
      <span>{{ node.label }}</span>
    </button>

    <div class="brain-panel">
      <p class="panel-eyebrow">{{ activeItem.status }}</p>
      <h3>{{ activeItem.title }}</h3>
      <p>{{ activeItem.description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ compact?: boolean }>()

const activeKey = ref('core')

const nodes = [
  { key: 'identity', label: 'Identity', title: 'Identity & access intelligence', status: 'Available Now / Project Dependent', description: 'Face, mobile, card, QR visitor, license plate, and future voiceprint access can be combined with admin-controlled permission rules.', x: 140, y: 84, xPercent: 16, yPercent: 13, tone: 'blue' },
  { key: 'rooms', label: 'Rooms', title: 'Room-level automation model', status: 'Available Now', description: 'Room, zone, occupancy, scene, comfort, and energy data become the base model for smart villa, hotel, office, apartment, and school workflows.', x: 312, y: 54, xPercent: 40, yPercent: 7, tone: 'emerald' },
  { key: 'cctv', label: 'CCTV', title: 'Security sensing layer', status: 'Available Now', description: 'IP cameras, NVR, ONVIF, access control, and selected AI analytics provide awareness without turning the platform into a camera shop.', x: 544, y: 84, xPercent: 73, yPercent: 13, tone: 'amber' },
  { key: 'hvac', label: 'HVAC', title: 'Comfort and energy control', status: 'Project Dependent', description: 'HVAC integration depends on Modbus, BACnet, dry contact, IR, gateway support, and local installer verification.', x: 626, y: 202, xPercent: 84, yPercent: 35, tone: 'slate' },
  { key: 'lighting', label: 'Lighting', title: 'Lighting and scene control', status: 'Available Now', description: 'KNX, DALI, smart switches, presence sensors, and scenes create the first visible layer of building intelligence.', x: 602, y: 348, xPercent: 79, yPercent: 64, tone: 'amber' },
  { key: 'energy', label: 'Solar', title: 'Solar and energy optimization', status: 'Project Dependent', description: 'PV, inverters, meters, batteries, EV chargers, and tariff logic can become a practical energy dashboard and alerting system.', x: 448, y: 456, xPercent: 59, yPercent: 84, tone: 'emerald' },
  { key: 'robots', label: 'Robots', title: 'Robot-ready building design', status: 'Future-Ready / Concept Demo', description: 'Cleaning, patrol, hotel delivery, garden, and AMR workflows need doors, elevators, permissions, maps, and safety design.', x: 250, y: 456, xPercent: 31, yPercent: 84, tone: 'blue' },
  { key: 'network', label: 'Network', title: 'Network and local AI edge', status: 'Available Now / Advanced Custom', description: 'Routers, PoE, Wi-Fi, NAS, VPN, edge AI boxes, and local servers make the building serviceable after handover.', x: 92, y: 332, xPercent: 8, yPercent: 62, tone: 'slate' },
  { key: 'maintenance', label: 'Service', title: 'Lifecycle service layer', status: 'Available Now', description: 'Remote support, firmware updates, spare parts, inspections, and AI reports turn one-time projects into long-term service.', x: 104, y: 190, xPercent: 10, yPercent: 34, tone: 'emerald' },
]

const coreItem = {
  title: 'AI Smart Building Brain',
  status: 'Lead-to-Solution Platform',
  description: 'AinerWise connects AI assessment, product capability matching, China supply chain, local implementation, and lifecycle support into one smart building operating model.',
}

const activeItem = computed(() => {
  return nodes.find((node) => node.key === activeKey.value) || coreItem
})
</script>

<style scoped>
.brain-shell {
  position: relative;
  width: 100%;
  min-height: 520px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background:
    radial-gradient(circle at 50% 42%, rgba(56, 189, 248, 0.16), transparent 26%),
    linear-gradient(135deg, #06111f 0%, #102033 42%, #10261f 100%);
  box-shadow: 0 24px 80px rgba(2, 6, 23, 0.28);
}

.brain-shell.compact {
  min-height: 460px;
}

.brain-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(to bottom, black, transparent 92%);
}

.brain-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.brain-line {
  stroke: rgba(125, 211, 252, 0.28);
  stroke-width: 1.2;
  stroke-dasharray: 6 12;
  transform-origin: center;
}

.brain-line.is-active {
  stroke: rgba(250, 204, 21, 0.8);
  stroke-width: 2;
}

.brain-core,
.brain-node {
  position: absolute;
  border: 0;
  color: white;
  cursor: pointer;
}

.brain-core {
  left: 50%;
  top: 50%;
  width: 190px;
  height: 190px;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 50%;
  background:
    linear-gradient(145deg, rgba(14, 165, 233, 0.94), rgba(16, 185, 129, 0.84)),
    #0f172a;
  box-shadow:
    0 0 0 10px rgba(14, 165, 233, 0.12),
    0 0 60px rgba(45, 212, 191, 0.42);
  text-align: center;
}

.brain-core strong {
  font-size: 28px;
  line-height: 1;
}

.brain-core span {
  max-width: 130px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.82);
}

.core-kicker {
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.brain-node {
  transform: translate(-50%, -50%);
  min-width: 112px;
  min-height: 42px;
  padding: 10px 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(15, 23, 42, 0.78);
  backdrop-filter: blur(10px);
  font-size: 13px;
  font-weight: 700;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}

.brain-node:hover,
.brain-node.is-active {
  transform: translate(-50%, -50%) scale(1.05);
  border-color: rgba(255, 255, 255, 0.46);
  background: rgba(15, 23, 42, 0.94);
}

.node-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 18px currentColor;
}

.tone-emerald .node-dot { background: #34d399; }
.tone-amber .node-dot { background: #fbbf24; }
.tone-slate .node-dot { background: #cbd5e1; }

.brain-panel {
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: 22px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(2, 6, 23, 0.72);
  color: white;
  backdrop-filter: blur(12px);
}

.brain-panel h3 {
  margin: 4px 0 6px;
  font-size: 17px;
  font-weight: 800;
}

.brain-panel p {
  margin: 0;
  color: rgba(226, 232, 240, 0.82);
  font-size: 13px;
  line-height: 1.5;
}

.panel-eyebrow {
  color: #fde68a !important;
  font-size: 11px !important;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

@media (max-width: 640px) {
  .brain-shell,
  .brain-shell.compact {
    min-height: 560px;
  }

  .brain-core {
    width: 150px;
    height: 150px;
  }

  .brain-core strong {
    font-size: 22px;
  }

  .brain-node {
    min-width: 96px;
    padding: 8px 10px;
    font-size: 12px;
  }
}
</style>
