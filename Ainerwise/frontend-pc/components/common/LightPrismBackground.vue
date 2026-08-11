<template>
  <div class="light-bg fixed inset-0 z-[-1] overflow-hidden pointer-events-none" aria-hidden="true">
    <canvas ref="canvas" class="block h-full w-full"></canvas>
  </div>
</template>

<script setup lang="ts">
/**
 * Background for the light theme.
 *
 * Same starfield language as the dark and knx themes — a full-viewport field of
 * drifting points with lines forming between neighbours, plus a few brighter
 * pulsing nodes and travelling sparks — in blue, on a soft light-blue wash. The
 * earlier version drifted faint wireframe polyhedra that were effectively
 * invisible on white; this makes the "星光点点" field read across all three
 * themes. As with knx, we can't glow dots on a light ground (additive blending
 * washes to white), so these are saturated blue specks at high opacity.
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

  const BLUE = new THREE.Color('#2563eb')
  const INDIGO = new THREE.Color('#4f46e5')

  // --- Drifting field -------------------------------------------------------
  const COUNT = 210
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
    color: BLUE,
    size: 3.8,
    transparent: true,
    opacity: 0.9,
    sizeAttenuation: true,
    depthWrite: false,
  })
  scene.add(new THREE.Points(pointsGeo, pointsMat))

  // Brighter pulsing nodes on a second layer.
  const NODES = 14
  const nodePos = new Float32Array(NODES * 3)
  const nodeIdx: number[] = []
  for (let i = 0; i < NODES; i += 1) {
    nodeIdx.push(Math.floor(Math.random() * COUNT))
  }
  const nodeGeo = new THREE.BufferGeometry()
  nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePos, 3))
  const nodeMat = new THREE.PointsMaterial({
    color: INDIGO,
    size: 8,
    transparent: true,
    opacity: 0.85,
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
    color: BLUE,
    transparent: true,
    opacity: 0.34,
    depthWrite: false,
  })
  const lines = new THREE.LineSegments(lineGeo, lineMat)
  scene.add(lines)

  // Sparks travelling along current connections.
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
    color: INDIGO,
    size: 4.5,
    transparent: true,
    opacity: 0.9,
    depthWrite: false,
  })
  scene.add(new THREE.Points(sparkGeo, sparkMat))

  // Damped pointer parallax.
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

    // Nodes track their host particles and breathe.
    for (let i = 0; i < NODES; i += 1) {
      nodePos.set(positions.subarray(nodeIdx[i] * 3, nodeIdx[i] * 3 + 3), i * 3)
    }
    nodeGeo.attributes.position.needsUpdate = true
    nodeMat.opacity = 0.72 + Math.sin(elapsed * 1.6) * 0.18

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
.light-bg {
  background:
    radial-gradient(ellipse 70% 55% at 18% 8%, rgba(37, 99, 235, 0.12) 0%, transparent 58%),
    radial-gradient(ellipse 60% 50% at 88% 92%, rgba(79, 70, 229, 0.10) 0%, transparent 55%),
    radial-gradient(ellipse 45% 40% at 60% 40%, rgba(56, 189, 248, 0.08) 0%, transparent 60%),
    linear-gradient(180deg, #f5f8ff 0%, #edf3fe 60%, #e6eefc 100%);
}
</style>
