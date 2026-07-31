<template>
  <div class="space-y-2">
    <canvas
      ref="canvasRef"
      class="w-full h-36 border rounded-lg bg-white touch-none"
      @pointerdown="start"
      @pointermove="move"
      @pointerup="end"
      @pointerleave="end"
    />
    <div class="flex gap-2 text-sm">
      <button type="button" class="px-3 py-1 border rounded" @click="clear">清除</button>
      <button type="button" class="px-3 py-1 bg-primary-600 text-white rounded" @click="emitSignature">确认签字</button>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{ signed: [dataUrl: string] }>()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let drawing = false

function ctx() {
  const c = canvasRef.value
  if (!c) return null
  if (c.width !== c.clientWidth) {
    c.width = c.clientWidth
    c.height = c.clientHeight
  }
  return c.getContext('2d')
}

function start(e: PointerEvent) {
  drawing = true
  const g = ctx()
  if (!g) return
  g.strokeStyle = '#111'
  g.lineWidth = 2
  g.beginPath()
  g.moveTo(e.offsetX, e.offsetY)
}

function move(e: PointerEvent) {
  if (!drawing) return
  const g = ctx()
  if (!g) return
  g.lineTo(e.offsetX, e.offsetY)
  g.stroke()
}

function end() {
  drawing = false
}

function clear() {
  const c = canvasRef.value
  const g = ctx()
  if (!c || !g) return
  g.clearRect(0, 0, c.width, c.height)
}

function emitSignature() {
  const c = canvasRef.value
  if (!c) return
  emit('signed', c.toDataURL('image/png'))
}
</script>
