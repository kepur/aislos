<template>
  <div class="light-bg fixed inset-0 z-[-1] overflow-hidden pointer-events-none" aria-hidden="true">
    <canvas ref="canvas" class="block h-full w-full"></canvas>
  </div>
</template>

<script setup lang="ts">
/**
 * Background for the light theme.
 *
 * Where knx gets a floor plan and dark gets a particle network, this one is
 * lighter on its feet: a slow drift of wireframe polyhedra at several depths,
 * parallaxing against a soft blue wash. No hard edges, nothing that competes
 * with body copy — the movement is slow enough that you notice it only when
 * you stop reading.
 */
import * as THREE from 'three'

const canvas = ref<HTMLCanvasElement | null>(null)
let renderer: THREE.WebGLRenderer | null = null
let frame = 0

onMounted(() => {
  if (!canvas.value) return
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 500)
  camera.position.z = 120

  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)

  // Three depth bands. Nearer shapes are larger, fainter and drift faster, so
  // the field reads as having volume rather than being a flat pattern.
  const BANDS = [
    { count: 5, z: [-140, -90], scale: [16, 26], opacity: 0.16, speed: 0.055 },
    { count: 6, z: [-80, -30], scale: [9, 16], opacity: 0.24, speed: 0.085 },
    { count: 5, z: [-20, 30], scale: [5, 10], opacity: 0.34, speed: 0.12 },
  ]

  const SHAPES = [
    () => new THREE.IcosahedronGeometry(1, 0),
    () => new THREE.OctahedronGeometry(1, 0),
    () => new THREE.TetrahedronGeometry(1, 0),
  ]

  type Drifter = {
    mesh: THREE.LineSegments
    spin: THREE.Vector3
    bob: number
    bobSpeed: number
    baseY: number
  }
  const drifters: Drifter[] = []
  const geometries: THREE.BufferGeometry[] = []
  const materials: THREE.Material[] = []

  const rand = (min: number, max: number) => min + Math.random() * (max - min)

  for (const band of BANDS) {
    for (let i = 0; i < band.count; i += 1) {
      const geo = SHAPES[Math.floor(Math.random() * SHAPES.length)]()
      const wire = new THREE.WireframeGeometry(geo)
      const material = new THREE.LineBasicMaterial({
        color: new THREE.Color('#3b82f6'),
        transparent: true,
        opacity: band.opacity,
      })
      const mesh = new THREE.LineSegments(wire, material)
      const scale = rand(band.scale[0], band.scale[1])
      mesh.scale.setScalar(scale)
      mesh.position.set(rand(-110, 110), rand(-60, 60), rand(band.z[0], band.z[1]))
      mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0)
      scene.add(mesh)
      geometries.push(geo, wire)
      materials.push(material)
      drifters.push({
        mesh,
        spin: new THREE.Vector3(rand(-1, 1), rand(-1, 1), rand(-0.4, 0.4)).multiplyScalar(band.speed),
        bob: Math.random() * Math.PI * 2,
        bobSpeed: rand(0.12, 0.3),
        baseY: mesh.position.y,
      })
    }
  }

  // Pointer parallax, damped so it feels like the field has weight.
  const pointer = { x: 0, y: 0, tx: 0, ty: 0 }
  function onPointerMove(event: PointerEvent) {
    pointer.tx = (event.clientX / window.innerWidth - 0.5) * 12
    pointer.ty = (event.clientY / window.innerHeight - 0.5) * 8
  }
  window.addEventListener('pointermove', onPointerMove, { passive: true })

  const clock = new THREE.Clock()
  function render() {
    frame = requestAnimationFrame(render)
    const elapsed = clock.getElapsedTime()
    const delta = Math.min(clock.getDelta(), 0.05)

    pointer.x += (pointer.tx - pointer.x) * 0.04
    pointer.y += (pointer.ty - pointer.y) * 0.04
    camera.position.x = pointer.x
    camera.position.y = -pointer.y
    camera.lookAt(0, 0, -40)

    for (const d of drifters) {
      d.mesh.rotation.x += d.spin.x * delta
      d.mesh.rotation.y += d.spin.y * delta
      d.mesh.rotation.z += d.spin.z * delta
      d.mesh.position.y = d.baseY + Math.sin(elapsed * d.bobSpeed + d.bob) * 3.5
    }
    renderer!.render(scene, camera)
  }

  if (reduceMotion) {
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
    window.removeEventListener('resize', onResize)
    window.removeEventListener('pointermove', onPointerMove)
    for (const g of geometries) g.dispose()
    for (const m of materials) m.dispose()
    renderer?.dispose()
    renderer = null
  })
})
</script>

<style scoped>
.light-bg {
  background:
    radial-gradient(ellipse 70% 55% at 18% 8%, rgba(96, 165, 250, 0.14) 0%, transparent 58%),
    radial-gradient(ellipse 60% 50% at 88% 92%, rgba(56, 189, 248, 0.10) 0%, transparent 55%),
    radial-gradient(ellipse 45% 40% at 60% 40%, rgba(129, 140, 248, 0.07) 0%, transparent 60%),
    linear-gradient(180deg, #ffffff 0%, #fafcff 60%, #f4f8fd 100%);
}
</style>
