<template>
  <div class="space-y-2">
    <button type="button" class="text-sm font-semibold text-primary-600" @click="toggle">
      {{ active ? '关闭扫码相机' : '打开二维码扫描' }}
    </button>
    <div v-if="active" class="overflow-hidden rounded-xl bg-black">
      <video ref="video" autoplay playsinline muted class="aspect-square w-full object-cover" />
      <p class="p-2 text-center text-[10px] text-white/70">{{ message }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{ scanned: [value: string] }>()
const video = ref<HTMLVideoElement | null>(null)
const active = ref(false)
const message = ref('Point the camera at a QR code.')
let stream: MediaStream | null = null
let frame = 0

async function stop() {
  active.value = false
  cancelAnimationFrame(frame)
  stream?.getTracks().forEach(track => track.stop())
  stream = null
}

async function scan() {
  if (!active.value || !video.value) return
  const Detector = (window as any).BarcodeDetector
  if (!Detector) {
    message.value = 'Live QR detection is not supported by this browser. Enter the code manually.'
    return
  }
  try {
    const detector = new Detector({ formats: ['qr_code'] })
    const codes = await detector.detect(video.value)
    if (codes[0]?.rawValue) {
      emit('scanned', codes[0].rawValue)
      await stop()
      return
    }
  } catch {
    message.value = 'Scanning failed. Reposition the QR code or enter it manually.'
  }
  frame = requestAnimationFrame(scan)
}

async function toggle() {
  if (active.value) return stop()
  message.value = 'Point the camera at a QR code.'
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' } },
      audio: false,
    })
    active.value = true
    await nextTick()
    if (video.value) video.value.srcObject = stream
    frame = requestAnimationFrame(scan)
  } catch {
    message.value = 'Camera permission was denied. Enter the code manually.'
  }
}

onUnmounted(stop)
</script>

