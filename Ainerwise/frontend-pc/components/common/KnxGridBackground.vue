<template>
  <div class="knx-bg fixed inset-0 z-[-1] overflow-hidden pointer-events-none" aria-hidden="true">
    <canvas ref="canvas" class="block h-full w-full"></canvas>
  </div>
</template>

<script setup lang="ts">
/**
 * Background for the knx theme.
 *
 * The knx look is the industry one — white surfaces, one confident green, a lot
 * of order. So this is not a particle cloud: it is a floor plan seen in
 * perspective, with signal pulses travelling out across it the way a bus
 * telegram propagates through a building. Quiet enough to sit under body text,
 * and it says "building automation" rather than "generic tech background".
 */
import * as THREE from 'three'

const canvas = ref<HTMLCanvasElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let frame = 0

const ACCENT = new THREE.Color('#00b451')

onMounted(() => {
  if (!canvas.value) return
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 400)
  // Low and tilted, so the plane recedes like a site drawing on a desk.
  camera.position.set(0, 46, 92)
  camera.lookAt(0, 0, -30)

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)

  // --- Floor grid -----------------------------------------------------------
  const SIZE = 260
  const DIV = 46
  const geometry = new THREE.PlaneGeometry(SIZE, SIZE, DIV, DIV)
  geometry.rotateX(-Math.PI / 2)
  const base = Float32Array.from(geometry.attributes.position.array)

  const grid = new THREE.LineSegments(
    new THREE.WireframeGeometry(geometry),
    new THREE.LineBasicMaterial({ color: ACCENT, transparent: true, opacity: 0.13 }),
  )
  grid.position.z = -40
  scene.add(grid)

  // --- Pulse origins --------------------------------------------------------
  // Each pulse is a ring expanding from a point on the plane; vertices near the
  // ring lift, which reads as a wave running through the structure.
  type Pulse = { x: number; z: number; t: number; speed: number }
  const pulses: Pulse[] = []
  function spawnPulse() {
    pulses.push({
      x: (Math.random() - 0.5) * SIZE * 0.7,
      z: (Math.random() - 0.5) * SIZE * 0.7,
      t: 0,
      speed: 26 + Math.random() * 14,
    })
    if (pulses.length > 4) pulses.shift()
  }
  spawnPulse()
  const pulseTimer = window.setInterval(spawnPulse, 2600)

  // --- Node markers ---------------------------------------------------------
  // A handful of brighter points sitting on grid intersections, like devices.
  const nodeCount = 26
  const nodePositions = new Float32Array(nodeCount * 3)
  for (let i = 0; i < nodeCount; i += 1) {
    const step = SIZE / DIV
    nodePositions[i * 3] = (Math.round((Math.random() - 0.5) * DIV * 0.8)) * step
    nodePositions[i * 3 + 1] = 0
    nodePositions[i * 3 + 2] = (Math.round((Math.random() - 0.5) * DIV * 0.8)) * step
  }
  const nodeGeo = new THREE.BufferGeometry()
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePositions, 3))
  const nodes = new THREE.Points(
    nodeGeo,
    new THREE.PointsMaterial({ color: ACCENT, size: 1.5, transparent: true, opacity: 0.5 }),
  )
  nodes.position.z = -40
  scene.add(nodes)

  const wireGeo = grid.geometry as THREE.BufferGeometry
  const wireBase = Float32Array.from(wireGeo.attributes.position.array)

  function displace(elapsed: number) {
    const pos = wireGeo.attributes.position
    const arr = pos.array as Float32Array
    for (let i = 0; i < arr.length; i += 3) {
      const x = wireBase[i]
      const z = wireBase[i + 2]
      let y = 0
      for (const p of pulses) {
        const d = Math.hypot(x - p.x, z - p.z)
        const ring = p.t - d
        // A narrow band around the ring front, fading as the pulse travels.
        if (ring > -6 && ring < 6) {
          const fall = Math.max(0, 1 - p.t / 190)
          y += Math.cos((ring / 6) * Math.PI * 0.5) * 3.4 * fall
        }
      }
      // A slow ambient swell keeps it alive between pulses.
      y += Math.sin(x * 0.045 + elapsed * 0.5) * Math.cos(z * 0.045 - elapsed * 0.4) * 0.5
      arr[i + 1] = y
    }
    pos.needsUpdate = true
  }

  const clock = new THREE.Clock()
  function render() {
    frame = requestAnimationFrame(render)
    const elapsed = clock.getElapsedTime()
    const delta = clock.getDelta()
    for (const p of pulses) p.t += p.speed * delta
    displace(elapsed)
    // A barely-there drift so the scene never sits perfectly still.
    grid.rotation.y = Math.sin(elapsed * 0.05) * 0.03
    nodes.rotation.y = grid.rotation.y
    renderer!.render(scene, camera)
  }

  if (reduceMotion) {
    displace(0)
    renderer.render(scene, camera)
  } else {
    render()
  }

  function onResize() {
    if (!renderer) return
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
  }
  window.addEventListener('resize', onResize)

  onBeforeUnmount(() => {
    cancelAnimationFrame(frame)
    window.clearInterval(pulseTimer)
    window.removeEventListener('resize', onResize)
    geometry.dispose()
    wireGeo.dispose()
    nodeGeo.dispose()
    renderer?.dispose()
    renderer = null
  })
})
</script>

<style scoped>
.knx-bg {
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, #f2fbf6 0%, transparent 60%),
    linear-gradient(180deg, #ffffff 0%, #f7faf8 55%, #f2f6f3 100%);
}
</style>
