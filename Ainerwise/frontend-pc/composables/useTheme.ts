export type ThemeKey = 'knx' | 'light' | 'dark'

export const THEME_OPTIONS: Array<{ key: ThemeKey; labelKey: string; swatch: string }> = [
  // Default: the industry look buyers in this market already recognise —
  // white surfaces, one strong accent, generous whitespace.
  { key: 'knx', labelKey: 'theme.knx', swatch: '#00b451' },
  { key: 'light', labelKey: 'theme.light', swatch: '#2563eb' },
  // The original identity: sky-blue 3D particle background on near-black.
  { key: 'dark', labelKey: 'theme.dark', swatch: '#0ea5e9' },
]

/**
 * AISLOS theme mode — SSR-safe via cookie.
 *
 * Three coexisting themes rather than a toggle: `knx` is the default public
 * look, `light` is the earlier neutral light scheme, and `dark` keeps the
 * original 3D-background identity intact. Nothing was removed to add the new
 * one, so any page that looked right before still does.
 */
export function useTheme() {
  const theme = useCookie<ThemeKey>('aislos_theme', {
    default: () => 'knx',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 365,
  })

  const isDark = computed(() => theme.value === 'dark')
  const isKnx = computed(() => theme.value === 'knx')
  // Both non-dark themes share the light typography/surface baseline.
  const isLightSurface = computed(() => theme.value !== 'dark')

  function set(value: ThemeKey) {
    theme.value = value
  }

  /** Cycles knx -> light -> dark -> knx, for the single-button control. */
  function toggle() {
    const order: ThemeKey[] = ['knx', 'light', 'dark']
    theme.value = order[(order.indexOf(theme.value) + 1) % order.length]
  }

  return { theme, isDark, isKnx, isLightSurface, toggle, set }
}
