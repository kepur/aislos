<template>
  <svg
    :class="sizeClass"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'ai-brain'">
      <path d="M12 4.5a3 3 0 0 0-3 3v.2A2.8 2.8 0 0 0 6.5 10a2.8 2.8 0 0 0 .6 1.7A2.9 2.9 0 0 0 6 14a2.9 2.9 0 0 0 3 2.9V17a3 3 0 0 0 3 3" />
      <path d="M12 4.5a3 3 0 0 1 3 3v.2A2.8 2.8 0 0 1 17.5 10a2.8 2.8 0 0 1-.6 1.7A2.9 2.9 0 0 1 18 14a2.9 2.9 0 0 1-3 2.9V17a3 3 0 0 1-3 3" />
      <path d="M12 4.5v15" />
      <circle cx="8.6" cy="10.4" r="1" fill="currentColor" stroke="none" />
      <circle cx="15.4" cy="13.6" r="1" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'supply-chain'">
      <path d="M3.5 8.2 12 4l8.5 4.2v7.6L12 20l-8.5-4.2z" />
      <path d="m3.5 8.2 8.5 4.2 8.5-4.2" />
      <path d="M12 12.4V20" />
    </template>

    <template v-else-if="name === 'installer'">
      <path d="m14.3 6.4 3.3 3.3" />
      <path d="M17 3.6a3.4 3.4 0 0 0-4.3 4.3L4 16.6V20h3.4l8.7-8.7A3.4 3.4 0 0 0 20.4 7z" />
    </template>

    <template v-else-if="name === 'lifecycle'">
      <path d="M20 12a8 8 0 1 1-2.6-5.9" />
      <path d="M20 4v4.5h-4.5" />
      <path d="M12 8v4.4l2.8 1.6" />
    </template>

    <template v-else-if="name === 'lighting'">
      <path d="M9.2 17h5.6" />
      <path d="M10 20h4" />
      <path d="M12 3a6 6 0 0 0-3.5 10.9c.4.3.6.7.6 1.1h5.8c0-.4.2-.8.6-1.1A6 6 0 0 0 12 3Z" />
    </template>

    <template v-else-if="name === 'hvac'">
      <path d="M12 9.8A2.2 2.2 0 1 0 12 14.2 2.2 2.2 0 1 0 12 9.8" />
      <path d="M12 9.8V4m0 16v-5.8" />
      <path d="m10.1 10.9-5-2.9m13.8 8-5-2.9" />
      <path d="m10.1 13.1-5 2.9m13.8-8-5 2.9" />
    </template>

    <template v-else-if="name === 'shading'">
      <path d="M3.5 4h17" />
      <path d="M5.5 4v9.5h13V4" />
      <path d="M5.5 8.2h13M5.5 11h13" />
      <path d="M12 13.5V20" />
    </template>

    <template v-else-if="name === 'energy'">
      <path d="M13.2 3 5.6 13.4h5.3L10.2 21l7.6-10.4h-5.3z" />
    </template>

    <template v-else-if="name === 'security'">
      <rect x="5" y="10.5" width="14" height="9.5" rx="2" />
      <path d="M8.2 10.5V7.6a3.8 3.8 0 0 1 7.6 0v2.9" />
      <path d="M12 14.4v2" />
    </template>

    <template v-else-if="name === 'automation'">
      <path d="M4 18a8 8 0 0 1 16 0" />
      <path d="M8.6 18a3.4 3.4 0 0 1 6.8 0" />
      <circle cx="12" cy="18" r="1.1" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'network'">
      <rect x="3.5" y="14.5" width="5" height="5" rx="1" />
      <rect x="15.5" y="14.5" width="5" height="5" rx="1" />
      <rect x="9.5" y="4.5" width="5" height="5" rx="1" />
      <path d="M12 9.5v3M6 14.5v-2h12v2" />
    </template>

    <template v-else-if="name === 'av'">
      <rect x="3.5" y="5" width="17" height="11" rx="2" />
      <path d="M9 20h6" />
      <path d="M12 16v4" />
      <path d="M10.4 8.6v3.8l3.3-1.9z" fill="currentColor" stroke="none" />
    </template>

    <template v-else-if="name === 'camera'">
      <path d="M4 8.5h3l1.4-2h7.2l1.4 2h3v10H4z" />
      <circle cx="12" cy="13" r="3.2" />
    </template>

    <template v-else-if="name === 'solar'">
      <path d="M4 15.5h16L18 5H6z" />
      <path d="M12 5v10.5M7.2 10.2h9.6" />
      <path d="M9 19h6" />
    </template>

    <template v-else-if="name === 'ev'">
      <rect x="4" y="6" width="10" height="12" rx="2" />
      <path d="M8 10.5h2.2L8.4 13.6h2.2" />
      <path d="M14 10h2.6a2 2 0 0 1 2 2v3.2a1.6 1.6 0 0 0 3.2 0V9.4l-2-2" />
    </template>

    <template v-else-if="name === 'sensor'">
      <circle cx="12" cy="12" r="2.2" />
      <path d="M8.4 8.4a5 5 0 0 0 0 7.2M15.6 15.6a5 5 0 0 0 0-7.2" />
      <path d="M5.9 5.9a8.6 8.6 0 0 0 0 12.2M18.1 18.1a8.6 8.6 0 0 0 0-12.2" />
    </template>

    <!-- Fallback keeps layout stable if a name is ever misspelled. -->
    <template v-else>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4.5l3 1.7" />
    </template>
  </svg>
</template>

<script setup lang="ts">
/**
 * Inline SVG feature icons.
 *
 * Deliberately not emoji: emoji render differently on every OS, and the
 * numeric HTML entities previously used here were interpolated as text by
 * Vue, so visitors saw "&#129302;" instead of an icon.
 */
const props = withDefaults(
  defineProps<{ name: string; size?: 'sm' | 'md' | 'lg' }>(),
  { size: 'md' }
)

const sizeClass = computed(
  () => ({ sm: 'h-5 w-5', md: 'h-7 w-7', lg: 'h-9 w-9' })[props.size]
)
</script>
