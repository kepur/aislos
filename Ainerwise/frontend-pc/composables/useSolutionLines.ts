/**
 * The eight AinerWise solution lines, as presentation metadata.
 *
 * Body copy (scene / risk / outcome / recurring) already lives in the `mtx.*`
 * i18n keys and the backend Solution records — this only adds what a detail
 * page needs on top: which building systems the line touches, what the AI
 * brain adds beyond a standard bus installation, and what is actually being
 * monitored.
 *
 * The AI column is the deliberate point of difference. A KNX installation
 * gives you control; these lines are sold on what the platform *notices* and
 * keeps noticing after handover.
 */
export interface SolutionLine {
  key: string
  /** Backend Solution slug — /solutions/{slug} already resolves. */
  slug: string
  name: string
  icon: string
  tagKey: string
  /** Building systems this line integrates with. */
  systems: Array<{ icon: string; label: string }>
  /** Capabilities that exist because of the AI brain, not the bus. */
  aiCapabilities: string[]
  /** What is measured, continuously. */
  monitoring: string[]
}

export const SOLUTION_LINES: SolutionLine[] = [
  {
    key: 'buildingbrain',
    slug: 'buildingbrain',
    name: 'BuildingBrain',
    icon: 'ai-brain',
    tagKey: 'tag_flagship',
    systems: [
      { icon: 'lighting', label: 'Lighting' },
      { icon: 'hvac', label: 'HVAC' },
      { icon: 'shading', label: 'Shading' },
      { icon: 'security', label: 'Security' },
      { icon: 'energy', label: 'Energy' },
      { icon: 'network', label: 'Network' },
      { icon: 'av', label: 'Audio / Video' },
      { icon: 'automation', label: 'Scenes' },
    ],
    aiCapabilities: [
      'Cross-system anomaly detection — a comfort complaint traced to a stuck valve, not guessed at',
      'Occupancy-aware setpoints that adapt per room instead of a fixed schedule',
      'Plain-language reports for owners who do not read trend graphs',
      'Upgrade recommendations ranked by payback, reviewed by an engineer before you see them',
    ],
    monitoring: ['Comfort per zone', 'Energy per system', 'Equipment run hours', 'Fault and alarm history'],
  },
  {
    key: 'storageguard',
    slug: 'storageguard',
    name: 'StorageGuard',
    icon: 'sensor',
    tagKey: 'tag_now',
    systems: [
      { icon: 'sensor', label: 'Temp / Humidity' },
      { icon: 'hvac', label: 'Refrigeration' },
      { icon: 'security', label: 'Door & Access' },
      { icon: 'network', label: 'Gateway' },
    ],
    aiCapabilities: [
      'Excursion prediction from drift, before the threshold is actually breached',
      'Audit-ready compliance reports generated from the raw record, not retyped',
      'Sensor-health checks that flag a probe going bad instead of trusting it',
    ],
    monitoring: ['Temperature per zone', 'Humidity', 'Door-open duration', 'Calibration due dates'],
  },
  {
    key: 'kitchenguard',
    slug: 'kitchenguard',
    name: 'KitchenGuard',
    icon: 'security',
    tagKey: 'tag_roadmap',
    systems: [
      { icon: 'sensor', label: 'Gas & CO' },
      { icon: 'hvac', label: 'Extraction' },
      { icon: 'security', label: 'Shut-off' },
      { icon: 'automation', label: 'Alarm routing' },
    ],
    aiCapabilities: [
      'Correlates gas readings with extraction state, so a real leak is separated from normal cooking',
      'Escalation that reaches a person, with a record of who acknowledged it',
    ],
    monitoring: ['Gas and CO levels', 'Water leak points', 'Extraction status', 'Shut-off valve state'],
  },
  {
    key: 'aquaguard',
    slug: 'aquaguard',
    name: 'AquaGuard',
    icon: 'sensor',
    tagKey: 'tag_partner',
    systems: [
      { icon: 'sensor', label: 'pH / COD / Turbidity' },
      { icon: 'energy', label: 'Dosing & Pumps' },
      { icon: 'network', label: 'Data logger' },
    ],
    aiCapabilities: [
      'Flags a reading trending toward a regulatory limit while there is still time to act',
      'Builds the regulator-facing report from the same record used internally',
    ],
    monitoring: ['pH', 'COD', 'Turbidity', 'Discharge volume', 'Probe calibration status'],
  },
  {
    key: 'energyguard',
    slug: 'energyguard',
    name: 'EnergyGuard',
    icon: 'solar',
    tagKey: 'tag_roadmap',
    systems: [
      { icon: 'solar', label: 'Solar PV' },
      { icon: 'energy', label: 'Storage' },
      { icon: 'ev', label: 'EV Charging' },
      { icon: 'network', label: 'Meters' },
    ],
    aiCapabilities: [
      'Tariff-aware charge and discharge planning instead of a fixed rule',
      'Battery-health trend that shows degradation before capacity visibly drops',
      'Yield checked against what the array should be producing, so underperformance is caught',
    ],
    monitoring: ['Generation vs consumption', 'Battery state of health', 'Peak demand', 'EV session usage'],
  },
  {
    key: 'factorypulse',
    slug: 'factorypulse',
    name: 'FactoryPulse',
    icon: 'automation',
    tagKey: 'tag_roadmap',
    systems: [
      { icon: 'sensor', label: 'Vibration & Current' },
      { icon: 'energy', label: 'Machine Energy' },
      { icon: 'network', label: 'Edge Gateway' },
    ],
    aiCapabilities: [
      'Non-invasive OEE — no PLC integration and no warranty risk on the machine',
      'Failure signatures learned per machine, so an alert means something specific',
    ],
    monitoring: ['Run / idle / stopped', 'Energy per machine', 'Vibration signature', 'Downtime causes'],
  },
  {
    key: 'assetpulse',
    slug: 'assetpulse',
    name: 'AssetPulse',
    icon: 'network',
    tagKey: 'tag_roadmap',
    systems: [
      { icon: 'sensor', label: 'BLE / UWB Tags' },
      { icon: 'network', label: 'Anchors' },
      { icon: 'security', label: 'Geofence' },
    ],
    aiCapabilities: [
      'Learns normal movement per asset class, so an unusual route raises a flag',
      'Stocktake from live position data rather than a manual count',
    ],
    monitoring: ['Asset location', 'Zone dwell time', 'Geofence breaches', 'Tag battery level'],
  },
  {
    key: 'agribrain',
    slug: 'agribrain',
    name: 'AgriBrain',
    icon: 'sensor',
    tagKey: 'tag_future',
    systems: [
      { icon: 'sensor', label: 'Soil & Climate' },
      { icon: 'hvac', label: 'Ventilation' },
      { icon: 'energy', label: 'Irrigation' },
      { icon: 'solar', label: 'Off-grid Power' },
    ],
    aiCapabilities: [
      'Irrigation planned against soil moisture and forecast rather than a timer',
      'Early stress detection from combined climate and soil trends',
    ],
    monitoring: ['Soil moisture', 'Air temp / humidity', 'Light levels', 'Water and nutrient usage'],
  },
]

export function useSolutionLines() {
  const bySlug = (slug: string) => SOLUTION_LINES.find((l) => l.slug === slug) || null
  return { lines: SOLUTION_LINES, bySlug }
}
