<template>
  <div class="solutions-scene absolute inset-0" aria-hidden="true">
    <canvas ref="canvas" class="block h-full w-full"></canvas>
    <div class="solutions-scene__veil"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * Hero scene for the solutions page, replacing a static SVG.
 *
 * The page sells integrated building systems, so the scene shows exactly that:
 * stacked floor planes — the building — with risers connecting them, and light
 * running up and down those risers as systems talk to each other. It reads as
 * a building rather than as generic "tech", and it moves slowly enough to sit
 * behind a headline.
 */
import * as THREE from 'three'

const canvas = ref<HTMLCanvasElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let frame = 0

const ACCENT = new THREE.Color('#34d399')
const COOL = new THREE.Color('#38bdf8')

onMounted(() => {
  if (!canvas.value) return
  const host = canvas.value.parentElement as HTMLElement
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const size = () => ({ w: host.clientWidth || window.innerWidth, h: host.clientHeight || 600 })
  const { w, h } = size()

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(46, w / h, 0.1, 600)
  camera.position.set(58, 34, 96)
  camera.lookAt(6, 6, 0)

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h, false)

  const building = new THREE.Group()
  scene.add(building)

  // --- Floors ---------------------------------------------------------------
  const FLOORS = 7
  const FLOOR_GAP = 9
  const PLAN = 52
  const disposables: Array<{ dispose: () => void }> = []

  for (let i = 0; i < FLOORS; i += 1) {
    const inset = i * 1.6
    const plate = new THREE.PlaneGeometry(PLAN - inset, PLAN - inset, 6, 6)
    plate.rotateX(-Math.PI / 2)
    const wire = new THREE.WireframeGeometry(plate)
    const mat = new THREE.LineBasicMaterial({
      color: ACCENT,
      transparent: true,
      // Upper floors fade out, which gives the stack depth without a fog pass.
      opacity: 0.20 - i * 0.02,
    })
    const mesh = new THREE.LineSegments(wire, mat)
    mesh.position.y = i * FLOOR_GAP
    building.add(mesh)
    disposables.push(plate, wire, mat)
  }

  // --- Risers ---------------------------------------------------------------
  // Vertical lines at the plan corners, the paths signals travel along.
  const RISER_X = [-1, 1]
  const RISER_Z = [-1, 1]
  const riserTops = (FLOORS - 1) * FLOOR_GAP
  const risers: Array<{ x: number; z: number }> = []
  for (const sx of RISER_X) {
    for (const sz of RISER_Z) {
      const x = sx * (PLAN / 2 - 6)
      const z = sz * (PLAN / 2 - 6)
      risers.push({ x, z })
      const geo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(x, 0, z),
        new THREE.Vector3(x, riserTops, z),
      ])
      const mat = new THREE.LineBasicMaterial({ color: COOL, transparent: true, opacity: 0.16 })
      building.add(new THREE.Line(geo, mat))
      disposables.push(geo, mat)
    }
  }

  // --- Travelling signals ---------------------------------------------------
  const SIGNALS = 14
  const sigPos = new Float32Array(SIGNALS * 3)
  const signals = Array.from({ length: SIGNALS }, () => {
    const riser = risers[Math.floor(Math.random() * risers.length)]
    return {
      riser,
      t: Math.random(),
      speed: 0.05 + Math.random() * 0.12,
      dir: Math.random() > 0.5 ? 1 : -1,
    }
  })
  const sigGeo = new THREE.BufferGeometry()
  sigGeo.setAttribute('position', new THREE.BufferAttribute(sigPos, 3))
  const sigMat = new THREE.PointsMaterial({
    color: ACCENT,
    size: 2.4,
    transparent: true,
    opacity: 0.9,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  })
  building.add(new THREE.Points(sigGeo, sigMat))
  disposables.push(sigGeo, sigMat)

  // --- Ground halo ----------------------------------------------------------
  const haloGeo = new THREE.RingGeometry(PLAN * 0.62, PLAN * 0.66, 64)
  haloGeo.rotateX(-Math.PI / 2)
  const haloMat = new THREE.MeshBasicMaterial({
    color: ACCENT,
    transparent: true,
    opacity: 0.12,
    side: THREE.DoubleSide,
  })
  const halo = new THREE.Mesh(haloGeo, haloMat)
  halo.position.y = -0.5
  building.add(halo)
  disposables.push(haloGeo, haloMat)

  const clock = new THREE.Clock()
  function render() {
    frame = requestAnimationFrame(render)
    const delta = Math.min(clock.getDelta(), 0.05)
    const elapsed = clock.getElapsedTime()

    for (let i = 0; i < signals.length; i += 1) {
      const s = signals[i]
      s.t += s.speed * delta * s.dir
      if (s.t > 1) { s.t = 0; s.dir = 1 }
      if (s.t < 0) { s.t = 1; s.dir = -1 }
      sigPos[i * 3] = s.riser.x
      sigPos[i * 3 + 1] = s.t * riserTops
      sigPos[i * 3 + 2] = s.riser.z
    }
    sigGeo.attributes.position.needsUpdate = true

    // One slow revolution; the building is the subject, not the motion.
    building.rotation.y = elapsed * 0.045
    halo.scale.setScalar(1 + Math.sin(elapsed * 0.6) * 0.03)
    renderer!.render(scene, camera)
  }

  if (reduceMotion) {
    renderer.render(scene, camera)
  } else {
    render()
  }

  function onResize() {
    if (!renderer) return
    const next = size()
    camera.aspect = next.w / next.h
    camera.updateProjectionMatrix()
    renderer.setSize(next.w, next.h, false)
  }
  window.addEventListener('resize', onResize)

  onBeforeUnmount(() => {
    cancelAnimationFrame(frame)
    window.removeEventListener('resize', onResize)
    for (const d of disposables) d.dispose()
    renderer?.dispose()
    renderer = null
  })
})
</script>

<style scoped>
.solutions-scene {
  background:
    radial-gradient(ellipse 60% 55% at 72% 28%, rgba(52, 211, 153, 0.16), transparent 58%),
    radial-gradient(ellipse 55% 50% at 20% 78%, rgba(56, 189, 248, 0.12), transparent 55%),
    linear-gradient(135deg, #020617 0%, #04130f 52%, #020617 100%);
}
/* Keeps the headline side readable without dimming the scene everywhere. */
.solutions-scene__veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(2, 6, 23, 0.88) 0%, rgba(2, 6, 23, 0.42) 48%, rgba(2, 6, 23, 0.72) 100%);
}
</style>
