/**
 * AI Building Brain content, shared by the immersive 3D demo and the three
 * sub-pages that were split out of it.
 *
 * Structural fields (key / level / icon) stay in code; user-visible copy comes
 * from i18n so /cn, /rs, /pl render localized scenario text.
 */

export interface BrainScenario {
  key: string
  name: string
  type: string
  level: string
  boundary: string
  positioning: string
  sense: string[]
  control: string[]
  optimize: string[]
  maintain: string[]
  /** Icon used on the KNX-style scenario grid. */
  icon: string
}

const SCENARIO_DEFS = [
  { key: 'villa', level: 'L2-L5', icon: 'automation' },
  { key: 'school', level: 'L2-L4', icon: 'network' },
  { key: 'apartment', level: 'L2-L4', icon: 'security' },
  { key: 'office', level: 'L2-L5', icon: 'lighting' },
  { key: 'factory', level: 'L3-L5', icon: 'automation' },
  { key: 'hotel', level: 'L2-L4', icon: 'shading' },
  { key: 'energy', level: 'L3-L5', icon: 'solar' },
] as const

const CAPABILITY_DEFS = [
  { key: 'sense', icon: 'sensor' },
  { key: 'control', icon: 'automation' },
  { key: 'optimize', icon: 'ai-brain' },
  { key: 'maintain', icon: 'lifecycle' },
] as const

const TIER_DEFS = [
  { key: 'budget', level: 'L1-L2' },
  { key: 'standard', level: 'L2-L3' },
  { key: 'premium', level: 'L4-L5' },
  { key: 'future', level: 'L5-L6' },
] as const

const TAG_KEYS = ['availableNow', 'projectDependent', 'advancedCustom', 'futureReady', 'conceptDemo'] as const

const LEVEL_DEFS = [
  { level: 'L1', knx: true },
  { level: 'L2', knx: true },
  { level: 'L3', knx: false },
  { level: 'L4', knx: false },
  { level: 'L5', knx: false },
  { level: 'L6', knx: false },
] as const

/** vue-i18n `tm()` returns message AST nodes for arrays — resolve with `rt()`. */
function asStringList(raw: unknown, rt: (message: unknown) => string): string[] {
  const values = Array.isArray(raw)
    ? raw
    : raw && typeof raw === 'object'
      ? Object.values(raw as Record<string, unknown>)
      : []
  return values
    .map((item) => {
      if (typeof item === 'string') return item
      if (item == null) return ''
      try {
        const resolved = rt(item)
        if (typeof resolved === 'string' && resolved && resolved !== '[object Object]') return resolved
      } catch {
        /* fall through */
      }
      if (typeof item === 'object') {
        const node = item as Record<string, any>
        const staticBody = node?.body?.static ?? node?.loc?.source
        if (typeof staticBody === 'string' && staticBody) return staticBody
      }
      return ''
    })
    .filter(Boolean)
}

/** @deprecated Prefer useBuildingBrain().scenarios — kept for typed imports. */
export const BRAIN_SCENARIOS: BrainScenario[] = []

export function useBuildingBrain() {
  const { t, tm, rt } = useI18n({ useScope: 'global' })

  const scenarios = computed<BrainScenario[]>(() =>
    SCENARIO_DEFS.map((def) => ({
      key: def.key,
      level: def.level,
      icon: def.icon,
      name: t(`brain.scenarios.${def.key}.name`),
      type: t(`brain.scenarios.${def.key}.type`),
      boundary: t(`brain.scenarios.${def.key}.boundary`),
      positioning: t(`brain.scenarios.${def.key}.positioning`),
      sense: asStringList(tm(`brain.scenarios.${def.key}.sense`), rt),
      control: asStringList(tm(`brain.scenarios.${def.key}.control`), rt),
      optimize: asStringList(tm(`brain.scenarios.${def.key}.optimize`), rt),
      maintain: asStringList(tm(`brain.scenarios.${def.key}.maintain`), rt),
    })),
  )

  const capabilityBlocks = computed(() =>
    CAPABILITY_DEFS.map((def) => ({
      key: def.key,
      icon: def.icon,
      kicker: t(`brain.capabilities.${def.key}.kicker`),
      title: t(`brain.capabilities.${def.key}.title`),
    })),
  )

  const proposalTiers = computed(() =>
    TIER_DEFS.map((def) => ({
      name: t(`brain.tiers.${def.key}.name`),
      level: def.level,
      estimate: t(`brain.tiers.${def.key}.estimate`),
      note: t(`brain.tiers.${def.key}.note`),
      text: t(`brain.tiers.${def.key}.text`),
    })),
  )

  const featureTags = computed(() =>
    TAG_KEYS.map((key) => ({
      name: t(`brain.tags.${key}.name`),
      text: t(`brain.tags.${key}.text`),
    })),
  )

  const levels = computed(() =>
    LEVEL_DEFS.map((def) => ({
      level: def.level,
      knx: def.knx,
      name: t(`brain.levelsDetail.${def.level}.name`),
      text: t(`brain.levelsDetail.${def.level}.text`),
    })),
  )

  function byKey(key: string) {
    return scenarios.value.find((item) => item.key === key) || scenarios.value[0]
  }

  return {
    scenarios,
    capabilityBlocks,
    proposalTiers,
    featureTags,
    levels,
    byKey,
  }
}
