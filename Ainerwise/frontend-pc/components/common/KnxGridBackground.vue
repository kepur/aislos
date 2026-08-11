<template>
  <div class="knx-bg fixed inset-0 z-[-1] overflow-hidden pointer-events-none" aria-hidden="true">
    <canvas ref="canvas" class="block h-full w-full"></canvas>
  </div>
</template>

<script setup lang="ts">
/**
 * Background for the knx theme.
 *
 * Same idea as the dark theme's identity — a full-viewport field of drifting
 * points with lines forming between neighbours — reinterpreted for a white
 * ground: emerald constellation, depth-faded, with a handful of brighter
 * "device" nodes that pulse, and travelling sparks running along the longest
 * connections like telegrams on a bus. The first version was a floor grid
 * parked in one corner; this fills the screen the way dark does.
 */
import * as THREE from 'three'

const canvas = ref<HTMLCanvasElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let frame = 0

onMounted(() => {
  if (!canvas.value) return
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 1200)
  camera.position.z = 380

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)

  const EMERALD = new THREE.Color('#0f9d6b')
  const TEAL = new THREE.Color('#0891b2')

  // --- Drifting field -------------------------------------------------------
  const COUNT = 170
  const SPREAD = { x: 720, y: 420, z: 320 }
  const positions = new Float32Array(COUNT * 3)
  const velocities: THREE.Vector3[] = []
  for (let i = 0; i < COUNT; i += 1) {
    positions[i * 3] = (Math.random() - 0.5) * SPREAD.x
    positions[i * 3 + 1] = (Math.random() - 0.5) * SPREAD.y
    positions[i * 3 + 2] = (Math.random() - 0.5) * SPREAD.z
    velocities.push(
      new THREE.Vector3(
        (Math.random() - 0.5) * 6,
        (Math.random() - 0.5) * 5,
        (Math.random() - 0.5) * 4,
      ),
    )
  }
  const pointsGeo = new THREE.BufferGeometry()
  pointsGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  const pointsMat = new THREE.PointsMaterial({
    color: EMERALD,
    size: 3.2,
    transparent: true,
    opacity: 0.42,
    sizeAttenuation: true,
    depthWrite: false,
  })
  scene.add(new THREE.Points(pointsGeo, pointsMat))

  // Brighter pulsing "device" nodes on a second layer.
  const NODES = 14
  const nodePos = new Float32Array(NODES * 3)
  const nodeIdx: number[] = []
  for (let i = 0; i < NODES; i += 1) {
    const pick = Math.floor(Math.random() * COUNT)
    nodeIdx.push(pick)
  }
  const nodeGeo = new THREE.BufferGeometry()
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePos, 3))
  const nodeMat = new THREE.PointsMaterial({
    color: TEAL,
    size: 7,
    transparent: true,
    opacity: 0.55,
    sizeAttenuation: true,
    depthWrite: false,
  })
  scene.add(new THREE.Points(nodeGeo, nodeMat))

  // --- Connections ----------------------------------------------------------
  const MAX_DIST = 120
  const MAX_LINKS = COUNT * 4
  const linePos = new Float32Array(MAX_LINKS * 6)
  const lineGeo = new THREE.BufferGeometry()
  lineGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3))
  const lineMat = new THREE.LineBasicMaterial({
    color: EMERALD,
    transparent: true,
    opacity: 0.14,
    depthWrite: false,
  })
  const lines = new THREE.LineSegments(lineGeo, lineMat)
  scene.add(lines)

  // Sparks travelling along a few current connections.
  const SPARKS = 10
  const sparkPos = new Float32Array(SPARKS * 3)
  const sparks = Array.from({ length: SPARKS }, () => ({
    a: Math.floor(Math.random() * COUNT),
    b: Math.floor(Math.random() * COUNT),
    t: Math.random(),
    speed: 0.25 + Math.random() * 0.5,
  }))
  const sparkGeo = new THREE.BufferGeometry()
  sparkGeo.setAttribute('position', new THREE.BufferAttribute(sparkPos, 3))
  const sparkMat = new THREE.PointsMaterial({
    color: TEAL,
    size: 4.5,
    transparent: true,
    opacity: 0.85,
    depthWrite: false,
  })
  scene.add(new THREE.Points(sparkGeo, sparkMat))

  // Damped pointer parallax, same feel as the light theme's field.
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 }
  function onPointerMove(event: PointerEvent) {
    pointer.tx = (event.clientX / window.innerWidth - 0.5) * 26
    pointer.ty = (event.clientY / window.innerHeight - 0.5) * 16
  }
  window.addEventListener('pointermove', onPointerMove, { passive: true })

  const clock = new THREE.Clock()
  function tick() {
    const delta = Math.min(clock.getDelta(), 0.05)
    const elapsed = clock.getElapsedTime()

    // Drift and soft wrap at the bounds.
    for (let i = 0; i < COUNT; i += 1) {
      positions[i * 3] += velocities[i].x * delta
      positions[i * 3 + 1] += velocities[i].y * delta
      positions[i * 3 + 2] += velocities[i].z * delta
      if (Math.abs(positions[i * 3]) > SPREAD.x / 2) velocities[i].x *= -1
      if (Math.abs(positions[i * 3 + 1]) > SPREAD.y / 2) velocities[i].y *= -1
      if (Math.abs(positions[i * 3 + 2]) > SPREAD.z / 2) velocities[i].z *= -1
    }
    pointsGeo.attributes.position.needsUpdate = true

    // Rebuild neighbour links.
    let link = 0
    for (let i = 0; i < COUNT && link < MAX_LINKS; i += 1) {
      for (let j = i + 1; j < COUNT && link < MAX_LINKS; j += 1) {
        const dx = positions[i * 3] - positions[j * 3]
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1]
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2]
        if (dx * dx + dy * dy + dz * dz < MAX_DIST * MAX_DIST) {
          linePos.set(positions.subarray(i * 3, i * 3 + 3), link * 6)
          linePos.set(positions.subarray(j * 3, j * 3 + 3), link * 6 + 3)
          link += 1
        }
      }
    }
    lineGeo.setDrawRange(0, link * 2)
    lineGeo.attributes.position.needsUpdate = true

    // Device nodes track their host particles and breathe.
    for (let i = 0; i < NODES; i += 1) {
      nodePos.set(positions.subarray(nodeIdx[i] * 3, nodeIdx[i] * 3 + 3), i * 3)
    }
    nodeGeo.attributes.position.needsUpdate = true
    nodeMat.opacity = 0.4 + Math.sin(elapsed * 1.6) * 0.18

    // Sparks interpolate between their two endpoints.
    for (let i = 0; i < SPARKS; i += 1) {
      const s = sparks[i]
      s.t += s.speed * delta
      if (s.t >= 1) {
        s.t = 0
        s.a = s.b
        s.b = Math.floor(Math.random() * COUNT)
      }
      for (let axis = 0; axis < 3; axis += 1) {
        sparkPos[i * 3 + axis] =
          positions[s.a * 3 + axis] + (positions[s.b * 3 + axis] - positions[s.a * 3 + axis]) * s.t
      }
    }
    sparkGeo.attributes.position.needsUpdate = true

    pointer.x += (pointer.tx - pointer.x) * 0.04
    pointer.y += (pointer.ty - pointer.y) * 0.04
    camera.position.x = pointer.x
    camera.position.y = -pointer.y
    camera.lookAt(0, 0, 0)
    scene.rotation.y = Math.sin(elapsed * 0.04) * 0.08

    renderer!.render(scene, camera)
  }

  function render() {
    frame = requestAnimationFrame(render)
    tick()
  }

  if (reduceMotion) {
    tick()
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
    window.removeEventListener('resize', onResize)
    window.removeEventListener('pointermove', onPointerMove)
    pointsGeo.dispose()
    pointsMat.dispose()
    nodeGeo.dispose()
    nodeMat.dispose()
    lineGeo.dispose()
    lineMat.dispose()
    sparkGeo.dispose()
    sparkMat.dispose()
    renderer?.dispose()
    renderer = null
  })
})
</script>

<style scoped>
.knx-bg {
  background:
    radial-gradient(ellipse 65% 50% at 15% 10%, rgba(15, 157, 107, 0.08), transparent 60%),
    radial-gradient(ellipse 55% 45% at 88% 85%, rgba(8, 145, 178, 0.06), transparent 55%),
    linear-gradient(180deg, #ffffff 0%, #f7fbf8 55%, #f2f8f4 100%);
}
</style>
