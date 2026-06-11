<template>
  <div ref="container" class="fixed inset-0 z-[-1] overflow-hidden pointer-events-none bg-slate-950">
    <canvas ref="canvas" class="block w-full h-full"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'

const container = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationId: number
let particles: THREE.Points
let linesMesh: THREE.LineSegments

// Settings
const particleCount = 200
const maxDistance = 150

onMounted(() => {
  if (!canvas.value || !container.value) return

  // Scene
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x020617, 0.002) // slate-950 color fog

  // Camera
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 1000)
  camera.position.z = 400

  // Renderer
  renderer = new THREE.WebGLRenderer({
    canvas: canvas.value,
    alpha: true,
    antialias: true
  })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(window.innerWidth, window.innerHeight)

  // Particles
  const particlesGeometry = new THREE.BufferGeometry()
  const particlesPosition = new Float32Array(particleCount * 3)
  const particleVelocities: number[] = []

  for (let i = 0; i < particleCount; i++) {
    particlesPosition[i * 3] = (Math.random() - 0.5) * 800
    particlesPosition[i * 3 + 1] = (Math.random() - 0.5) * 800
    particlesPosition[i * 3 + 2] = (Math.random() - 0.5) * 800

    particleVelocities.push(
      (Math.random() - 0.5) * 0.5,
      (Math.random() - 0.5) * 0.5,
      (Math.random() - 0.5) * 0.5
    )
  }

  particlesGeometry.setAttribute('position', new THREE.BufferAttribute(particlesPosition, 3))

  // Custom shader material for glowing dots
  const particlesMaterial = new THREE.PointsMaterial({
    color: 0x0ea5e9, // sky-500
    size: 4,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
  })

  particles = new THREE.Points(particlesGeometry, particlesMaterial)
  scene.add(particles)

  // Lines
  const linesGeometry = new THREE.BufferGeometry()
  const linesMaterial = new THREE.LineBasicMaterial({
    color: 0x0ea5e9, // sky-500
    transparent: true,
    opacity: 0.15,
    blending: THREE.AdditiveBlending
  })
  linesMesh = new THREE.LineSegments(linesGeometry, linesMaterial)
  scene.add(linesMesh)

  // Animation Loop
  let frame = 0
  const animate = () => {
    animationId = requestAnimationFrame(animate)
    frame += 0.005

    // Slow scene rotation
    scene.rotation.y = frame * 0.5
    scene.rotation.x = frame * 0.2

    // Move particles
    const positions = particles.geometry.attributes.position.array as Float32Array
    
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] += particleVelocities[i * 3]
      positions[i * 3 + 1] += particleVelocities[i * 3 + 1]
      positions[i * 3 + 2] += particleVelocities[i * 3 + 2]

      // Bounce off invisible boundaries
      if (Math.abs(positions[i * 3]) > 400) particleVelocities[i * 3] *= -1
      if (Math.abs(positions[i * 3 + 1]) > 400) particleVelocities[i * 3 + 1] *= -1
      if (Math.abs(positions[i * 3 + 2]) > 400) particleVelocities[i * 3 + 2] *= -1
    }
    particles.geometry.attributes.position.needsUpdate = true

    // Update lines based on distance
    const linePositions: number[] = []
    const lineOpacities: number[] = []

    let vertexpos = 0
    let colorpos = 0
    let numConnected = 0

    for (let i = 0; i < particleCount; i++) {
      for (let j = i + 1; j < particleCount; j++) {
        const dx = positions[i * 3] - positions[j * 3]
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1]
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2]
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)

        if (dist < maxDistance) {
          const alpha = 1.0 - dist / maxDistance

          linePositions.push(
            positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2],
            positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]
          )

          numConnected++
        }
      }
    }

    linesMesh.geometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3))
    
    renderer.render(scene, camera)
  }

  animate()

  // Resize handler
  const handleResize = () => {
    if (!container.value) return
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(window.innerWidth, window.innerHeight)
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', () => {})
  if (renderer) {
    renderer.dispose()
  }
  if (particles.geometry) particles.geometry.dispose()
  if (linesMesh.geometry) linesMesh.geometry.dispose()
})
</script>
