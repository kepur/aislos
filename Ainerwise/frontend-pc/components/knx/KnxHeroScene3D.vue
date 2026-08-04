<template>
  <div ref="host" class="knx-scene" aria-hidden="true">
    <canvas ref="canvas" class="knx-scene-canvas" :class="{ 'is-live': live }" />
  </div>
</template>

<script setup lang="ts">
import * as THREE from 'three'

/**
 * Real-time 3D hero: a dusk city block with our own tower at the centre, the
 * bus traced in green along its edges, and a scan sweeping up the facade.
 *
 * Rendered rather than filmed on purpose — the building is ours (no third-party
 * project footage), it costs no video bytes, it re-colours with the theme, and
 * we can add scenes to it later. The caller keeps an SVG poster underneath and
 * cross-fades on `ready`, so a device without WebGL simply never fades.
 */
const emit = defineEmits<{ ready: [] }>()

const host = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
const live = ref(false)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let frameId = 0
let resizeObs: ResizeObserver | null = null
let viewObs: IntersectionObserver | null = null

/** Everything that holds GPU memory, collected for teardown. */
const trash: Array<{ dispose: () => void }> = []

let onScreen = true
let reducedMotion = false
const pointer = { x: 0, y: 0 }
const aim = { x: 0, y: 0 }

const TOWER = { w: 4.2, d: 3.4, h: 13.5 }
const GREEN = 0x22c55e
const WARM = 0xffd8a0
const COLD = 0x14513f

/** Soft radial sprite, generated so the scene needs no image assets. */
function radialTexture(core: string, edge: string) {
  const size = 128
  const cv = document.createElement('canvas')
  cv.width = cv.height = size
  const ctx = cv.getContext('2d')!
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
  g.addColorStop(0, core)
  g.addColorStop(1, edge)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, size, size)
  const tex = new THREE.CanvasTexture(cv)
  trash.push(tex)
  return tex
}

type Block = { x: number; z: number; w: number; d: number; h: number }

/** The centre tower plus neighbours that give the shot depth. */
const blocks: Block[] = [
  { x: 0, z: 0, w: TOWER.w, d: TOWER.d, h: TOWER.h },
  { x: -8.0, z: -5.0, w: 3.0, d: 3.0, h: 7.4 },
  { x: 8.4, z: -3.6, w: 3.2, d: 2.8, h: 9.0 },
  { x: -6.6, z: 6.2, w: 2.6, d: 2.6, h: 4.6 },
  { x: 7.4, z: 7.0, w: 2.8, d: 2.6, h: 5.4 },
  { x: -13.0, z: 1.0, w: 3.4, d: 3.0, h: 6.0 },
  { x: 13.5, z: 2.6, w: 3.0, d: 3.0, h: 7.8 },
]

function buildScene(el: HTMLElement, cv: HTMLCanvasElement) {
  const w = el.clientWidth || 1
  const h = el.clientHeight || 1

  renderer = new THREE.WebGLRenderer({ canvas: cv, alpha: true, antialias: true, powerPreference: 'high-performance' })
  // Capping DPR at 2 keeps a 5K display from rendering 4x the pixels for no
  // visible gain on a background scene.
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h, false)

  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x06251f, 0.03)

  camera = new THREE.PerspectiveCamera(52, w / h, 0.1, 200)

  // ---- Massing -----------------------------------------------------------
  const facade = new THREE.MeshLambertMaterial({ color: 0x21463d })
  trash.push(facade)

  for (const b of blocks) {
    const geo = new THREE.BoxGeometry(b.w, b.h, b.d)
    trash.push(geo)
    const mesh = new THREE.Mesh(geo, facade)
    mesh.position.set(b.x, b.h / 2, b.z)
    scene.add(mesh)

    // The green trace. Brighter on the hero tower, faint on the neighbours,
    // so the eye is told which building the story is about.
    const edges = new THREE.EdgesGeometry(geo)
    const lineMat = new THREE.LineBasicMaterial({
      color: GREEN,
      transparent: true,
      opacity: b.h === TOWER.h ? 1 : 0.5,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
    trash.push(edges, lineMat)
    const outline = new THREE.LineSegments(edges, lineMat)
    outline.position.copy(mesh.position)
    scene.add(outline)
  }

  // ---- Windows -----------------------------------------------------------
  // One InstancedMesh for every window in the block: ~900 lit panes at the
  // cost of a single draw call.
  const paneGeo = new THREE.PlaneGeometry(0.2, 0.11)
  const paneMat = new THREE.MeshBasicMaterial({ side: THREE.FrontSide })
  trash.push(paneGeo, paneMat)

  const slots: Array<{ p: THREE.Vector3; ry: number }> = []
  for (const b of blocks) {
    const rows = Math.max(4, Math.floor(b.h / 0.42))
    const faces: Array<{ span: number; ry: number; nx: number; nz: number }> = [
      { span: b.w, ry: 0, nx: 0, nz: b.d / 2 + 0.012 },
      { span: b.w, ry: Math.PI, nx: 0, nz: -(b.d / 2 + 0.012) },
      { span: b.d, ry: Math.PI / 2, nx: b.w / 2 + 0.012, nz: 0 },
      { span: b.d, ry: -Math.PI / 2, nx: -(b.w / 2 + 0.012), nz: 0 },
    ]
    for (const f of faces) {
      const cols = Math.max(3, Math.floor(f.span / 0.34))
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const along = (c + 0.5) / cols - 0.5
          const y = 0.4 + r * ((b.h - 0.75) / Math.max(1, rows - 1))
          const p = f.ry === 0 || f.ry === Math.PI
            ? new THREE.Vector3(b.x + along * f.span, y, b.z + f.nz)
            : new THREE.Vector3(b.x + f.nx, y, b.z + along * f.span)
          slots.push({ p, ry: f.ry })
        }
      }
    }
  }

  const panes = new THREE.InstancedMesh(paneGeo, paneMat, slots.length)
  const dummy = new THREE.Object3D()
  const warm = new THREE.Color(WARM)
  const cold = new THREE.Color(COLD)
  slots.forEach((s, i) => {
    dummy.position.copy(s.p)
    dummy.rotation.set(0, s.ry, 0)
    dummy.updateMatrix()
    panes.setMatrixAt(i, dummy.matrix)
    panes.setColorAt(i, Math.random() < 0.2 ? warm : cold)
  })
  panes.instanceMatrix.needsUpdate = true
  scene.add(panes)

  // ---- Ground ------------------------------------------------------------
  const groundGeo = new THREE.PlaneGeometry(90, 90)
  const groundMat = new THREE.MeshBasicMaterial({
    map: radialTexture('rgba(20,120,95,0.55)', 'rgba(4,30,26,0)'),
    transparent: true,
    depthWrite: false,
  })
  trash.push(groundGeo, groundMat)
  const ground = new THREE.Mesh(groundGeo, groundMat)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = 0.01
  scene.add(ground)

  // ---- Scan ring: the survey sweeping the facade -------------------------
  const ringGeo = new THREE.TorusGeometry(4.4, 0.02, 8, 96)
  const ringMat = new THREE.MeshBasicMaterial({
    color: GREEN, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false,
  })
  trash.push(ringGeo, ringMat)
  const ring = new THREE.Mesh(ringGeo, ringMat)
  ring.rotation.x = Math.PI / 2
  scene.add(ring)

  // ---- Bus pulses climbing the tower corners -----------------------------
  const pulseTex = radialTexture('rgba(190,255,220,1)', 'rgba(120,240,180,0)')
  const pulses: Array<{ sprite: THREE.Sprite; phase: number; speed: number }> = []
  const corners = [
    [TOWER.w / 2, TOWER.d / 2], [-TOWER.w / 2, TOWER.d / 2],
    [TOWER.w / 2, -TOWER.d / 2], [-TOWER.w / 2, -TOWER.d / 2],
  ]
  corners.forEach(([cx, cz], i) => {
    for (let k = 0; k < 2; k++) {
      const mat = new THREE.SpriteMaterial({ map: pulseTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })
      trash.push(mat)
      const sprite = new THREE.Sprite(mat)
      sprite.scale.setScalar(0.5)
      sprite.position.set(cx, 0, cz)
      scene.add(sprite)
      pulses.push({ sprite, phase: (i * 2 + k) / 8, speed: 0.16 + k * 0.03 })
    }
  })

  // ---- Atmosphere --------------------------------------------------------
  const dustGeo = new THREE.BufferGeometry()
  const dustCount = 160
  const dustPos = new Float32Array(dustCount * 3)
  for (let i = 0; i < dustCount; i++) {
    dustPos[i * 3] = (Math.random() - 0.5) * 42
    dustPos[i * 3 + 1] = Math.random() * 22
    dustPos[i * 3 + 2] = (Math.random() - 0.5) * 42
  }
  dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3))
  const dustMat = new THREE.PointsMaterial({
    color: 0x6ee7b7, size: 0.075, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false,
  })
  trash.push(dustGeo, dustMat)
  scene.add(new THREE.Points(dustGeo, dustMat))

  // ---- Light -------------------------------------------------------------
  scene.add(new THREE.AmbientLight(0x1f6f5c, 1.5))
  const key = new THREE.DirectionalLight(0x9df5cf, 1.15)
  key.position.set(6, 12, 8)
  scene.add(key)
  const rim = new THREE.DirectionalLight(0x2dd4bf, 0.7)
  rim.position.set(-8, 5, -6)
  scene.add(rim)

  // ---- Loop --------------------------------------------------------------
  const clock = new THREE.Clock()
  trash.push({ dispose: () => clock.stop() })
  let flickerAt = 0

  const place = (t: number) => {
    // A slow crane-style orbit — the move a drone shot would make.
    const angle = t * 0.038 + 0.6
    const radius = 12.5 + Math.sin(t * 0.24) * 0.6
    aim.x += (pointer.x - aim.x) * 0.045
    aim.y += (pointer.y - aim.y) * 0.045
    camera!.position.set(
      Math.sin(angle) * radius + aim.x * 1.4,
      3.4 + Math.sin(t * 0.18) * 0.4 - aim.y * 0.8,
      Math.cos(angle) * radius,
    )
    camera!.lookAt(0, 7.4, 0)

    const climb = (t * 0.18) % 1.3
    ring.position.y = climb * TOWER.h
    ringMat.opacity = 0.85 * Math.max(0, 1 - Math.abs(climb - 0.5) * 1.2)

    for (const p of pulses) {
      const u = (t * p.speed + p.phase) % 1
      p.sprite.position.y = u * TOWER.h
      ;(p.sprite.material as THREE.SpriteMaterial).opacity = Math.sin(u * Math.PI)
    }

    // Occupancy: a few windows switch state each beat, so the block reads as
    // lived-in rather than as a static render.
    if (t - flickerAt > 1.1 && panes.instanceColor) {
      flickerAt = t
      for (let n = 0; n < 6; n++) {
        const i = Math.floor(Math.random() * slots.length)
        panes.setColorAt(i, Math.random() < 0.45 ? warm : cold)
      }
      panes.instanceColor.needsUpdate = true
    }
  }

  const render = () => {
    frameId = requestAnimationFrame(render)
    if (!onScreen) return
    place(clock.getElapsedTime())
    renderer!.render(scene!, camera!)
  }

  if (reducedMotion) {
    place(6)
    renderer.render(scene, camera)
  } else {
    render()
  }
}

function onPointerMove(e: PointerEvent) {
  if (!host.value) return
  const r = host.value.getBoundingClientRect()
  pointer.x = ((e.clientX - r.left) / r.width - 0.5) * 2
  pointer.y = ((e.clientY - r.top) / r.height - 0.5) * 2
}

onMounted(() => {
  if (!host.value || !canvas.value) return
  reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

  try {
    buildScene(host.value, canvas.value)
  } catch {
    // No WebGL, blocked context, or a driver that refuses us: stay invisible
    // and let the caller's poster carry the section.
    return
  }

  live.value = true
  emit('ready')

  resizeObs = new ResizeObserver(() => {
    if (!host.value || !renderer || !camera) return
    const w = host.value.clientWidth || 1
    const h = host.value.clientHeight || 1
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h, false)
  })
  resizeObs.observe(host.value)

  // Scrolled past the hero: stop burning GPU on frames nobody sees.
  viewObs = new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting }, { threshold: 0 })
  viewObs.observe(host.value)

  window.addEventListener('pointermove', onPointerMove, { passive: true })
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId)
  window.removeEventListener('pointermove', onPointerMove)
  resizeObs?.disconnect()
  viewObs?.disconnect()
  for (const item of trash) item.dispose()
  trash.length = 0
  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
})
</script>

<style scoped>
.knx-scene {
  position: absolute;
  inset: 0;
  /* Sits behind the canvas so the dusk sky exists before WebGL is ready and
     still shows through the scene's transparent background afterwards. */
  background: radial-gradient(ellipse at 50% 80%, #12564a 0%, #0a3229 45%, #05201c 100%);
}
.knx-scene-canvas {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 1.1s ease;
}
.knx-scene-canvas.is-live { opacity: 1; }
</style>
