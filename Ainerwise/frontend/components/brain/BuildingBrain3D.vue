<template>
  <div ref="host" class="brain3d">
    <canvas ref="canvas" class="brain3d-canvas" aria-label="AinerWise 3D AI building brain scene"></canvas>
    <div class="brain3d-readout">
      <p>{{ levelConfig.kicker }}</p>
      <h3>{{ levelConfig.name }}</h3>
      <span>{{ scenarioLabel }}</span>
      <div class="mt-3 grid grid-cols-2 gap-2 text-[11px] uppercase tracking-wide text-slate-300">
        <span v-for="chip in activeScene.chips" :key="chip" class="border border-cyan-300/20 bg-cyan-300/10 px-2 py-1">{{ chip }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as THREE from 'three'

const props = defineProps<{
  level: 'L3' | 'L4' | 'L5'
  scenarioKey: string
}>()

const host = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let root: THREE.Group | null = null
let animationId = 0
let resizeObserver: ResizeObserver | null = null
let animated: Array<{ object: THREE.Object3D; mode: 'spin' | 'pulse' | 'float' | 'walk' | 'drive' | 'scan'; speed: number; offset: number }> = []

const levelConfigs = {
  L3: {
    kicker: 'L3 Energy Optimized',
    name: 'Energy Optimized Building',
    color: 0x34d399,
    secondary: 0xfbbf24,
    atmosphere: 0x0f766e,
    nodeCount: 9,
    beamCount: 14,
    orbitSpeed: 0.0018,
    cityScale: 0.92,
  },
  L4: {
    kicker: 'L4 AI Assisted',
    name: 'AI Assisted Building',
    color: 0x38bdf8,
    secondary: 0xa78bfa,
    atmosphere: 0x0ea5e9,
    nodeCount: 13,
    beamCount: 22,
    orbitSpeed: 0.0026,
    cityScale: 1.02,
  },
  L5: {
    kicker: 'L5 Local AI Brain',
    name: 'Local AI Building Brain',
    color: 0x60a5fa,
    secondary: 0xf472b6,
    atmosphere: 0x4f46e5,
    nodeCount: 17,
    beamCount: 32,
    orbitSpeed: 0.0034,
    cityScale: 1.12,
  },
}

const sceneConfigs: Record<string, { label: string; chips: string[]; buildings: number; solar: boolean; ev: boolean; robots: boolean; doors: boolean; garden: boolean; campus: boolean }> = {
  villa: { label: 'Smart Villa / Future Home', chips: ['AI Family', 'Smart Windows', 'EV', 'Robots'], buildings: 5, solar: true, ev: true, robots: true, doors: true, garden: true, campus: false },
  school: { label: 'School Campus', chips: ['Campus AI', 'CCTV', 'CO2', 'Energy'], buildings: 8, solar: true, ev: false, robots: true, doors: true, garden: false, campus: true },
  apartment: { label: 'Apartment Building', chips: ['Property AI', 'Access', 'Parking', 'Meters'], buildings: 9, solar: true, ev: true, robots: false, doors: true, garden: false, campus: false },
  office: { label: 'Enterprise Office', chips: ['Facility AI', 'Meetings', 'Network', 'Identity'], buildings: 7, solar: true, ev: true, robots: true, doors: true, garden: false, campus: false },
  hotel: { label: 'Hotel / Serviced Apartment', chips: ['Guest AI', 'Room Scene', 'HVAC', 'Service'], buildings: 6, solar: true, ev: false, robots: true, doors: true, garden: false, campus: false },
  energy: { label: 'Solar + Energy Site', chips: ['PV', 'Battery', 'EV', 'Tariff AI'], buildings: 4, solar: true, ev: true, robots: false, doors: false, garden: false, campus: false },
}

const levelConfig = computed(() => levelConfigs[props.level])
const activeScene = computed(() => sceneConfigs[props.scenarioKey] || sceneConfigs.energy)
const scenarioLabel = computed(() => activeScene.value.label)

function mat(color: number, emissive = 0, intensity = 0.25, transparent = false, opacity = 1) {
  return new THREE.MeshStandardMaterial({
    color,
    emissive: emissive || color,
    emissiveIntensity: intensity,
    roughness: 0.42,
    metalness: 0.34,
    transparent,
    opacity,
  })
}

function addLine(group: THREE.Group, from: THREE.Vector3, to: THREE.Vector3, color: number, opacity = 0.46) {
  const geometry = new THREE.BufferGeometry().setFromPoints([from, to])
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity })
  group.add(new THREE.Line(geometry, material))
}

function addGround(group: THREE.Group, color: number) {
  const plane = new THREE.Mesh(
    new THREE.PlaneGeometry(11, 7),
    new THREE.MeshBasicMaterial({ color: 0x020617, transparent: true, opacity: 0.55 }),
  )
  plane.rotation.x = -Math.PI / 2
  plane.position.y = -1.62
  group.add(plane)

  const grid = new THREE.GridHelper(11, 22, color, 0x164e63)
  grid.position.y = -1.58
  const material = grid.material as THREE.Material
  material.transparent = true
  material.opacity = 0.26
  group.add(grid)
}

function addPortal(group: THREE.Group, color: number, secondary: number) {
  const portal = new THREE.Group()
  portal.position.set(-3.65, -0.42, 1.15)
  portal.rotation.y = 0.5

  const outer = new THREE.Mesh(
    new THREE.TorusGeometry(0.88, 0.035, 12, 96),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.92 }),
  )
  const inner = new THREE.Mesh(
    new THREE.TorusGeometry(0.62, 0.018, 12, 96),
    new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.62 }),
  )
  const surface = new THREE.Mesh(
    new THREE.CircleGeometry(0.82, 72),
    new THREE.MeshBasicMaterial({ color, transparent: true, opacity: props.level === 'L5' ? 0.22 : 0.12 }),
  )
  portal.add(outer, inner, surface)
  animated.push({ object: outer, mode: 'spin', speed: 0.025, offset: 0 })
  animated.push({ object: inner, mode: 'spin', speed: -0.035, offset: 0 })

  const path = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-3.45, -1.46, 1.3),
    new THREE.Vector3(-2.55, -1.44, 0.72),
    new THREE.Vector3(-1.65, -1.42, 0.34),
    new THREE.Vector3(-0.55, -1.38, 0.1),
  ])
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(path, 60, 0.018, 8, false),
    new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.72 }),
  )
  group.add(portal, tube)

  const human = new THREE.Group()
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.09, 0.34, 6, 12), mat(0xe2e8f0, color, 0.3))
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.095, 16, 12), mat(0xf8fafc, secondary, 0.18))
  head.position.y = 0.32
  const glow = new THREE.Mesh(new THREE.RingGeometry(0.19, 0.22, 32), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.5, side: THREE.DoubleSide }))
  glow.rotation.x = Math.PI / 2
  glow.position.y = -0.22
  human.add(body, head, glow)
  human.position.set(-3.45, -1.1, 1.3)
  group.add(human)
  animated.push({ object: human, mode: 'walk', speed: props.level === 'L5' ? 0.00032 : 0.00022, offset: 0 })
}

function addAICore(group: THREE.Group, color: number, secondary: number) {
  const coreGroup = new THREE.Group()
  coreGroup.position.set(0.25, -0.2, 0)

  const core = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.58, 4),
    new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: props.level === 'L5' ? 1.85 : 1.25,
      roughness: 0.16,
      metalness: 0.5,
      transparent: true,
      opacity: 0.96,
    }),
  )
  core.name = 'AI'
  const brainWire = new THREE.Mesh(
    new THREE.IcosahedronGeometry(props.level === 'L5' ? 1.35 : 1.08, 2),
    new THREE.MeshBasicMaterial({ color: secondary, wireframe: true, transparent: true, opacity: props.level === 'L5' ? 0.42 : 0.28 }),
  )
  coreGroup.add(core, brainWire)
  animated.push({ object: core, mode: 'pulse', speed: 0.004, offset: 0 })
  animated.push({ object: brainWire, mode: 'spin', speed: 0.009, offset: 0 })

  const ringCount = props.level === 'L3' ? 3 : props.level === 'L4' ? 5 : 7
  for (let i = 0; i < ringCount; i += 1) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(1.1 + i * 0.22, 0.008, 8, 144),
      new THREE.MeshBasicMaterial({ color: i % 2 ? secondary : color, transparent: true, opacity: 0.38 - i * 0.025 }),
    )
    ring.rotation.set(Math.PI / 2.2 + i * 0.18, i * 0.22, i * 0.1)
    coreGroup.add(ring)
    animated.push({ object: ring, mode: 'spin', speed: 0.004 + i * 0.001, offset: i })
  }
  group.add(coreGroup)
}

function addBuildings(group: THREE.Group, color: number, secondary: number) {
  type BuildingSpec = { x: number; z: number; w: number; h: number; d: number; tone?: number; roof?: 'flat' | 'gable' | 'antenna' | 'battery' }
  const scenarioTones: Record<string, { base: number; glass: number; accent: number; window: number }> = {
    villa: { base: 0x13251f, glass: 0x1f3a2f, accent: 0xfbbf24, window: 0x86efac },
    school: { base: 0x1e293b, glass: 0x334155, accent: 0x38bdf8, window: 0x7dd3fc },
    apartment: { base: 0x111827, glass: 0x1e3a8a, accent: 0xa78bfa, window: 0xc4b5fd },
    office: { base: 0x0f172a, glass: 0x164e63, accent: 0x22d3ee, window: 0x67e8f9 },
    hotel: { base: 0x1c1917, glass: 0x3f2f25, accent: 0xf59e0b, window: 0xfcd34d },
    energy: { base: 0x10231f, glass: 0x14532d, accent: 0x34d399, window: 0x6ee7b7 },
  }
  const tones = scenarioTones[props.scenarioKey] || scenarioTones.energy
  const bodyMaterial = mat(tones.base, color, 0.18)
  const glassMaterial = mat(tones.glass, color, props.level === 'L5' ? 0.42 : 0.28)
  const accentMaterial = new THREE.MeshBasicMaterial({ color: tones.accent, transparent: true, opacity: 0.74 })
  const windowMaterial = new THREE.MeshBasicMaterial({ color: tones.window, transparent: true, opacity: props.level === 'L3' ? 0.5 : 0.78 })
  const doorMaterial = new THREE.MeshBasicMaterial({ color: secondary, transparent: true, opacity: 0.9 })

  const layouts: Record<string, BuildingSpec[]> = {
    villa: [
      { x: -1.35, z: -0.7, w: 1.05, h: 0.62, d: 0.72, roof: 'gable' },
      { x: -0.45, z: -0.72, w: 0.8, h: 0.92, d: 0.72, roof: 'gable' },
      { x: 0.42, z: -0.75, w: 0.7, h: 0.7, d: 0.68, roof: 'gable' },
      { x: 1.15, z: -0.65, w: 0.62, h: 0.48, d: 0.62, roof: 'flat' },
    ],
    school: [
      { x: -2.05, z: -1.05, w: 1.15, h: 0.62, d: 0.58, roof: 'flat' },
      { x: -0.82, z: -1.05, w: 1.15, h: 0.62, d: 0.58, roof: 'flat' },
      { x: 0.42, z: -1.05, w: 1.15, h: 0.62, d: 0.58, roof: 'flat' },
      { x: 1.58, z: -1.05, w: 0.82, h: 0.84, d: 0.58, roof: 'antenna' },
      { x: -1.42, z: -1.82, w: 1.1, h: 0.5, d: 0.48, roof: 'flat' },
      { x: 0.02, z: -1.82, w: 1.1, h: 0.5, d: 0.48, roof: 'flat' },
    ],
    apartment: [
      { x: -1.9, z: -0.86, w: 0.58, h: 1.85, d: 0.58, roof: 'antenna' },
      { x: -1.14, z: -0.88, w: 0.58, h: 2.28, d: 0.58, roof: 'flat' },
      { x: -0.34, z: -0.9, w: 0.64, h: 1.62, d: 0.64, roof: 'flat' },
      { x: 0.54, z: -0.88, w: 0.58, h: 2.45, d: 0.58, roof: 'antenna' },
      { x: 1.34, z: -0.9, w: 0.62, h: 1.96, d: 0.62, roof: 'flat' },
    ],
    office: [
      { x: -1.72, z: -0.92, w: 0.7, h: 2.0, d: 0.62, roof: 'antenna' },
      { x: -0.78, z: -0.88, w: 0.76, h: 2.7, d: 0.66, roof: 'flat' },
      { x: 0.22, z: -0.9, w: 0.84, h: 2.28, d: 0.72, roof: 'antenna' },
      { x: 1.22, z: -0.92, w: 0.66, h: 1.75, d: 0.58, roof: 'flat' },
    ],
    hotel: [
      { x: -1.6, z: -1.0, w: 1.35, h: 0.92, d: 0.66, roof: 'flat' },
      { x: -0.18, z: -1.0, w: 1.35, h: 0.92, d: 0.66, roof: 'flat' },
      { x: 1.18, z: -1.0, w: 0.92, h: 1.52, d: 0.66, roof: 'antenna' },
      { x: -0.72, z: -1.78, w: 1.42, h: 0.56, d: 0.48, roof: 'flat' },
      { x: 0.84, z: -1.78, w: 1.42, h: 0.56, d: 0.48, roof: 'flat' },
    ],
    energy: [
      { x: -1.32, z: -0.86, w: 0.8, h: 0.74, d: 0.62, roof: 'flat' },
      { x: -0.32, z: -0.86, w: 0.72, h: 1.08, d: 0.58, roof: 'antenna' },
      { x: 0.72, z: -0.96, w: 0.86, h: 0.42, d: 0.58, roof: 'battery' },
      { x: 1.72, z: -0.96, w: 0.86, h: 0.42, d: 0.58, roof: 'battery' },
    ],
  }

  const specs = layouts[props.scenarioKey] || layouts.energy
  for (const [i, spec] of specs.entries()) {
    const material = props.scenarioKey === 'office' || i % 2 === 1 ? glassMaterial : bodyMaterial
    const block = new THREE.Mesh(new THREE.BoxGeometry(spec.w, spec.h, spec.d), material)
    block.position.set(spec.x, -1.58 + spec.h / 2, spec.z)
    group.add(block)

    if (spec.roof === 'gable') {
      const roof = new THREE.Mesh(new THREE.ConeGeometry(spec.w * 0.72, 0.34, 4), accentMaterial)
      roof.position.set(spec.x, -1.58 + spec.h + 0.17, spec.z)
      roof.rotation.y = Math.PI / 4
      roof.scale.z = spec.d / spec.w
      group.add(roof)
    } else {
      const roof = new THREE.Mesh(new THREE.BoxGeometry(spec.w * 0.82, 0.035, spec.d * 0.74), accentMaterial)
      roof.position.set(spec.x, -1.58 + spec.h + 0.045, spec.z)
      group.add(roof)
    }

    if (spec.roof === 'antenna' || (props.level === 'L5' && i === 0)) {
      const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.48, 8), new THREE.MeshBasicMaterial({ color: secondary }))
      mast.position.set(spec.x + spec.w * 0.28, -1.58 + spec.h + 0.28, spec.z)
      group.add(mast)
      const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 8), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.95 }))
      beacon.position.set(spec.x + spec.w * 0.28, -1.58 + spec.h + 0.53, spec.z)
      group.add(beacon)
      animated.push({ object: beacon, mode: 'pulse', speed: 0.004, offset: i })
    }

    if (spec.roof === 'battery') {
      const stripe = new THREE.Mesh(new THREE.PlaneGeometry(spec.w * 0.7, 0.08), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85 }))
      stripe.position.set(spec.x, -1.58 + spec.h * 0.55, spec.z + spec.d / 2 + 0.006)
      group.add(stripe)
    }

    const rows = Math.max(1, Math.floor(spec.h / (props.scenarioKey === 'apartment' || props.scenarioKey === 'office' ? 0.24 : 0.28)))
    const cols = Math.max(2, Math.floor(spec.w / 0.18))
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        if ((row + col + i) % 3 === 0 && props.level === 'L3') continue
        const win = new THREE.Mesh(new THREE.PlaneGeometry(0.06, props.scenarioKey === 'hotel' ? 0.07 : 0.085), windowMaterial)
        win.position.set(spec.x - spec.w / 2 + 0.14 + col * 0.16, -1.42 + row * 0.21, spec.z + spec.d / 2 + 0.006)
        group.add(win)
        animated.push({ object: win, mode: 'pulse', speed: 0.0025, offset: i + row + col })
      }
    }

    if (activeScene.value.doors && (i === 0 || i % 2 === 0)) {
      const door = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.28), doorMaterial)
      door.position.set(spec.x, -1.42, spec.z + spec.d / 2 + 0.008)
      group.add(door)
      animated.push({ object: door, mode: 'pulse', speed: 0.004, offset: i })
    }
  }

  if (activeScene.value.garden) {
    for (let i = 0; i < 10; i += 1) {
      const tree = new THREE.Group()
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.035, 0.22, 8), new THREE.MeshBasicMaterial({ color: 0x854d0e }))
      const crown = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.32, 12), new THREE.MeshBasicMaterial({ color: 0x22c55e, transparent: true, opacity: 0.85 }))
      crown.position.y = 0.23
      tree.add(trunk, crown)
      tree.position.set(-2.6 + i * 0.52, -1.48, 0.25 + (i % 2) * 0.42)
      group.add(tree)
    }
  }
}

function addSolar(group: THREE.Group, color: number, secondary: number) {
  if (!activeScene.value.solar) return
  const panelMaterial = new THREE.MeshStandardMaterial({
    color: 0x0f172a,
    emissive: props.level === 'L3' ? 0xfacc15 : color,
    emissiveIntensity: props.level === 'L3' ? 0.42 : 0.28,
    roughness: 0.2,
    metalness: 0.6,
  })
  for (let i = 0; i < 9; i += 1) {
    const panel = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.018, 0.28), panelMaterial)
    panel.position.set(-3.0 + (i % 3) * 0.52, -1.42, -1.95 - Math.floor(i / 3) * 0.32)
    panel.rotation.x = -0.55
    panel.rotation.z = -0.12
    group.add(panel)
  }
  const sun = new THREE.Mesh(new THREE.SphereGeometry(0.22, 24, 16), new THREE.MeshBasicMaterial({ color: 0xfbbf24, transparent: true, opacity: 0.9 }))
  sun.position.set(-3.2, 1.58, -2.3)
  group.add(sun)
  animated.push({ object: sun, mode: 'float', speed: 0.002, offset: 1 })
  for (let i = 0; i < 5; i += 1) {
    addLine(group, new THREE.Vector3(-3.2, 1.36, -2.3), new THREE.Vector3(-3.0 + i * 0.34, -1.35, -1.8), secondary, 0.34)
  }
}

function addEV(group: THREE.Group, color: number, secondary: number) {
  if (!activeScene.value.ev) return
  const ev = new THREE.Group()
  ev.position.set(2.65, -1.35, 1.1)
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.24, 0.34), mat(0x0f172a, color, 0.38))
  const cabin = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.18, 0.28), mat(0x1e293b, secondary, 0.32))
  cabin.position.set(-0.05, 0.2, 0)
  ev.add(body, cabin)
  for (const x of [-0.28, 0.28]) {
    for (const z of [-0.18, 0.18]) {
      const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.045, 16), new THREE.MeshBasicMaterial({ color: 0x020617 }))
      wheel.rotation.z = Math.PI / 2
      wheel.position.set(x, -0.13, z)
      ev.add(wheel)
    }
  }
  group.add(ev)
  animated.push({ object: ev, mode: 'drive', speed: 0.0014, offset: 0 })

  const charger = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.52, 0.12), mat(0x1e293b, secondary, 0.5))
  charger.position.set(3.2, -1.22, 0.75)
  group.add(charger)
  addLine(group, new THREE.Vector3(3.12, -1.08, 0.78), new THREE.Vector3(2.76, -1.32, 1.03), secondary, 0.8)
}

function addRobots(group: THREE.Group, color: number, secondary: number) {
  if (!activeScene.value.robots && props.level !== 'L5') return
  const robotCount = props.level === 'L5' ? 3 : 1
  for (let i = 0; i < robotCount; i += 1) {
    const robot = new THREE.Group()
    robot.position.set(1.3 + i * 0.58, -1.36, -1.55 + i * 0.28)
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.18, 0.14, 18), mat(0x0f172a, color, 0.38))
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.14, 18, 12), mat(0x1e293b, secondary, 0.58))
    head.position.y = 0.22
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.035, 10, 8), new THREE.MeshBasicMaterial({ color }))
    eye.position.set(0.08, 0.23, 0.11)
    const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.28, 8), new THREE.MeshBasicMaterial({ color: secondary }))
    antenna.position.y = 0.46
    robot.add(base, head, eye, antenna)
    group.add(robot)
    animated.push({ object: robot, mode: 'float', speed: 0.002 + i * 0.0003, offset: i })
  }
}

function addCCTVAndSensors(group: THREE.Group, color: number, secondary: number) {
  if (props.level === 'L3' && !['school', 'office', 'hotel', 'apartment'].includes(props.scenarioKey)) return
  const positions = [
    new THREE.Vector3(-1.7, 0.4, 0.35),
    new THREE.Vector3(1.85, 0.52, -0.25),
    new THREE.Vector3(0.4, 0.9, -1.35),
  ]
  for (const [index, position] of positions.entries()) {
    const cameraBox = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.1, 0.12), mat(0x0f172a, secondary, 0.45))
    cameraBox.position.copy(position)
    group.add(cameraBox)
    const cone = new THREE.Mesh(
      new THREE.ConeGeometry(0.48, 1.05, 28, 1, true),
      new THREE.MeshBasicMaterial({ color: index % 2 ? secondary : color, transparent: true, opacity: props.level === 'L5' ? 0.16 : 0.09, side: THREE.DoubleSide }),
    )
    cone.position.set(position.x, position.y - 0.28, position.z + 0.38)
    cone.rotation.x = Math.PI / 2
    group.add(cone)
    animated.push({ object: cone, mode: 'scan', speed: 0.0018, offset: index })
  }
}

function addDataNetwork(group: THREE.Group, color: number, secondary: number) {
  const config = levelConfig.value
  const endpoints: THREE.Vector3[] = []
  for (let i = 0; i < config.nodeCount; i += 1) {
    const angle = (i / config.nodeCount) * Math.PI * 2
    const radius = 2.7 + (i % 3) * 0.36 + (props.level === 'L5' ? 0.28 : 0)
    const y = -0.14 + ((i % 5) - 2) * 0.32
    const pos = new THREE.Vector3(Math.cos(angle) * radius, y, Math.sin(angle) * radius)
    endpoints.push(pos)
    const node = new THREE.Mesh(new THREE.SphereGeometry(i % 4 === 0 ? 0.105 : 0.07, 18, 12), new THREE.MeshBasicMaterial({ color: i % 2 ? secondary : color, transparent: true, opacity: 0.9 }))
    node.position.copy(pos)
    group.add(node)
    animated.push({ object: node, mode: 'pulse', speed: 0.0032, offset: i })
    addLine(group, new THREE.Vector3(0.25, -0.2, 0), pos, i % 2 ? secondary : color, props.level === 'L5' ? 0.48 : 0.31)
  }

  for (let i = 0; i < Math.min(config.beamCount, endpoints.length * 2); i += 1) {
    const from = endpoints[i % endpoints.length]
    const to = endpoints[(i * 3 + 2) % endpoints.length]
    addLine(group, from, to, i % 2 ? color : secondary, props.level === 'L5' ? 0.16 : 0.08)
  }
}

function addAtmosphere(group: THREE.Group, color: number) {
  const count = props.level === 'L3' ? 480 : props.level === 'L4' ? 760 : 1100
  const positions = new Float32Array(count * 3)
  for (let i = 0; i < count; i += 1) {
    const radius = 2.6 + Math.random() * 5.2
    const angle = Math.random() * Math.PI * 2
    positions[i * 3] = Math.cos(angle) * radius
    positions[i * 3 + 1] = -1.8 + Math.random() * 4.6
    positions[i * 3 + 2] = Math.sin(angle) * radius
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  const points = new THREE.Points(
    geometry,
    new THREE.PointsMaterial({ color, size: props.level === 'L5' ? 0.028 : 0.022, transparent: true, opacity: props.level === 'L5' ? 0.72 : 0.52 }),
  )
  group.add(points)
  animated.push({ object: points, mode: 'spin', speed: 0.0009, offset: 0 })
}

function buildScene() {
  if (!scene) return
  if (root) scene.remove(root)
  animated = []
  root = new THREE.Group()
  root.scale.setScalar(levelConfig.value.cityScale)
  scene.add(root)

  const color = levelConfig.value.color
  const secondary = levelConfig.value.secondary

  addGround(root, color)
  addPortal(root, color, secondary)
  addAICore(root, color, secondary)
  addBuildings(root, color, secondary)
  addSolar(root, color, secondary)
  addEV(root, color, secondary)
  addRobots(root, color, secondary)
  addCCTVAndSensors(root, color, secondary)
  addDataNetwork(root, color, secondary)
  addAtmosphere(root, levelConfig.value.atmosphere)
}

function resize() {
  if (!host.value || !renderer || !camera) return
  const width = host.value.clientWidth
  const height = host.value.clientHeight
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function animate() {
  if (!renderer || !scene || !camera || !root) return
  const now = Date.now()
  root.rotation.y += levelConfig.value.orbitSpeed * 0.24
  root.rotation.x = Math.sin(now * 0.00028) * 0.045

  for (const item of animated) {
    if (item.mode === 'spin') {
      item.object.rotation.y += item.speed
      item.object.rotation.z += item.speed * 0.5
    }
    if (item.mode === 'pulse') {
      const scale = 1 + Math.sin(now * item.speed + item.offset) * 0.12
      item.object.scale.setScalar(scale)
    }
    if (item.mode === 'float') {
      item.object.position.y += Math.sin(now * item.speed + item.offset) * 0.0018
      item.object.rotation.y += item.speed * 2
    }
    if (item.mode === 'walk') {
      const t = (Math.sin(now * item.speed) + 1) / 2
      item.object.position.x = -3.48 + t * 2.78
      item.object.position.z = 1.18 - t * 1.05
      item.object.rotation.y = 0.42 + Math.sin(now * 0.004) * 0.08
    }
    if (item.mode === 'drive') {
      item.object.position.x = 2.55 + Math.sin(now * item.speed + item.offset) * 0.36
    }
    if (item.mode === 'scan') {
      item.object.rotation.z = Math.sin(now * item.speed + item.offset) * 0.42
    }
  }

  renderer.render(scene, camera)
  animationId = requestAnimationFrame(animate)
}

onMounted(() => {
  if (!canvas.value || !host.value) return
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x020617)
  scene.fog = new THREE.Fog(0x020617, 6.5, 15)

  camera = new THREE.PerspectiveCamera(43, 1, 0.1, 100)
  camera.position.set(0.25, 0.65, 7.4)
  camera.lookAt(0.1, -0.35, 0)

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true, alpha: false })
  renderer.outputColorSpace = THREE.SRGBColorSpace

  const ambient = new THREE.AmbientLight(0xffffff, 0.74)
  scene.add(ambient)
  const key = new THREE.PointLight(0x7dd3fc, 4.2, 13)
  key.position.set(2.8, 3.6, 3.2)
  scene.add(key)
  const warm = new THREE.PointLight(0xfbbf24, 1.8, 9)
  warm.position.set(-3.8, 1.8, -2.2)
  scene.add(warm)
  const magenta = new THREE.PointLight(0xf0abfc, props.level === 'L5' ? 3.3 : 1.6, 10)
  magenta.position.set(-4, -0.5, 2.5)
  scene.add(magenta)

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(host.value)
  buildScene()
  resize()
  animate()
})

watch(() => [props.level, props.scenarioKey], buildScene)

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  resizeObserver?.disconnect()
  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
  root = null
  animated = []
})
</script>

<style scoped>
.brain3d {
  position: relative;
  min-height: 720px;
  width: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 68% 42%, rgba(20, 184, 166, 0.22), transparent 28%),
    radial-gradient(circle at 34% 54%, rgba(59, 130, 246, 0.18), transparent 26%),
    linear-gradient(135deg, #020617 0%, #061428 50%, #041f1a 100%);
}

.brain3d::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(to right, rgba(2, 6, 23, 0.92), rgba(2, 6, 23, 0.08) 38%, rgba(2, 6, 23, 0.78)),
    linear-gradient(to top, rgba(2, 6, 23, 0.9), transparent 36%),
    radial-gradient(circle at 56% 54%, transparent 0%, rgba(2, 6, 23, 0.16) 48%, rgba(2, 6, 23, 0.74) 100%);
}

.brain3d-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.brain3d-readout {
  position: absolute;
  right: 24px;
  top: 178px;
  z-index: 1;
  width: min(370px, calc(100% - 48px));
  border: 1px solid rgba(125, 211, 252, 0.26);
  background: rgba(2, 6, 23, 0.72);
  color: white;
  padding: 18px;
  backdrop-filter: blur(14px);
}

.brain3d-readout p,
.brain3d-readout span {
  margin: 0;
  color: rgba(226, 232, 240, 0.72);
  font-size: 12px;
}

.brain3d-readout p {
  color: #67e8f9;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.brain3d-readout h3 {
  margin: 6px 0;
  font-size: 20px;
  font-weight: 800;
}

@media (max-width: 768px) {
  .brain3d {
    min-height: 700px;
  }

  .brain3d::after {
    background:
      linear-gradient(to bottom, rgba(2, 6, 23, 0.82), rgba(2, 6, 23, 0.18) 46%, rgba(2, 6, 23, 0.94)),
      linear-gradient(to top, rgba(2, 6, 23, 0.92), transparent 42%);
  }

  .brain3d-readout {
    top: auto;
    right: 16px;
    bottom: 18px;
    width: min(340px, calc(100% - 32px));
  }
}
</style>
