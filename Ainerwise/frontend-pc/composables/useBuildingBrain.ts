/**
 * AI Building Brain content, shared by the immersive 3D demo and the three
 * sub-pages that were split out of it.
 *
 * Extracted verbatim from the original single page so nothing was lost in the
 * split — the demo keeps using the same objects, and the sub-pages present
 * them at a granularity that reads well without the 3D scene.
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

export const BRAIN_SCENARIOS: BrainScenario[] = [
  {
    key: 'villa',
    name: 'Smart Villa / Future Home',
    type: 'Residential AI Brain',
    level: 'L2-L5',
    boundary: 'Available Now to Advanced Custom',
    icon: 'automation',
    positioning: 'A local AI-ready family building system that connects identity, rooms, energy, security, kitchen, bathroom, bedroom, EV, garden, and service.',
    sense: ['Family member identity', 'Presence and room occupancy', 'Water leak, smoke, gas, humidity', 'Solar, battery, and EV charging status'],
    control: ['Lighting scenes and curtains', 'HVAC comfort modes', 'Door, visitor, and garage permissions', 'Smart bedroom, kitchen, and bathroom equipment'],
    optimize: ['Sleep and comfort curves', 'PV-first EV charging', 'Low-tariff appliance scheduling', 'Unoccupied room energy saving'],
    maintain: ['Remote gateway health', 'Firmware and backup checks', 'Spare parts planning', 'Annual lifecycle review'],
  },
  {
    key: 'school',
    name: 'School Campus',
    type: 'AI Campus Brain',
    level: 'L2-L4',
    boundary: 'Project Dependent',
    icon: 'network',
    positioning: 'A campus operating layer for classroom comfort, safety, network visibility, energy reporting, and maintenance workflows.',
    sense: ['Teacher, student, and visitor zones', 'CO2, temperature, humidity, and noise', 'Camera and network device health', 'After-school occupancy'],
    control: ['Classroom lighting and HVAC schedules', 'Lab and machine room access', 'Visitor area permissions', 'Campus alert workflows'],
    optimize: ['Class schedule energy saving', 'Roof solar visibility', 'High-consumption building ranking', 'Daily facility summary'],
    maintain: ['Offline camera alerts', 'AP and switch status', 'Repair ticket creation', 'Monthly energy reports'],
  },
  {
    key: 'apartment',
    name: 'Apartment Building',
    type: 'AI Property Brain',
    level: 'L2-L4',
    boundary: 'Available Now / Project Dependent',
    icon: 'security',
    positioning: 'A property management layer for common area energy, access, CCTV, parking, tenant experience, repair workflow, and lifecycle service.',
    sense: ['Common area occupancy', 'Parking license plates', 'Public lighting and meter data', 'Visitor and parcel access events'],
    control: ['Common area lighting', 'Visitor QR access', 'Parking gate permissions', 'Tenant service notifications'],
    optimize: ['Shared area energy allocation', 'PV for public loads', 'Maintenance priority', 'Monthly property reports'],
    maintain: ['Door access logs', 'Camera status', 'Meter gateway health', 'Preventive maintenance reminders'],
  },
  {
    key: 'office',
    name: 'Enterprise Office Building',
    type: 'AI Facility Brain',
    level: 'L2-L5',
    boundary: 'Advanced Custom for AI identity',
    icon: 'lighting',
    positioning: 'A facility system for visitor management, meeting rooms, employee comfort, IT visibility, access control, and energy optimization.',
    sense: ['Employee and visitor presence', 'Meeting room usage', 'IT room temperature and UPS status', 'Network AP and switch health'],
    control: ['Meeting room scenes', 'Visitor temporary access', 'Floor-level HVAC schedules', 'Screen, lighting, and curtain modes'],
    optimize: ['Empty-area energy saving', 'Workspace utilization', 'Daily facility summary', 'High-consumption floor alerts'],
    maintain: ['CCTV and access uptime', 'Network incident tracking', 'Firmware update planning', 'SLA-based service workflow'],
  },
  {
    key: 'factory',
    name: 'Factory / Industrial Plant',
    type: 'AI Industrial Energy Brain',
    level: 'L3-L5',
    boundary: 'Project Dependent / Advanced Custom',
    icon: 'automation',
    positioning: 'An industrial operating layer for production lines, machinery, PLC/SCADA, OT networks, compressed air, chillers, motors, robots, PV/battery, safety visibility, and lifecycle maintenance.',
    sense: ['Machine status, runtime, alarms, and downtime', 'Line-level energy, power quality, and peak demand', 'Compressed air, chiller, motor, VFD, pump, and boiler loads', 'PLC/SCADA/Modbus/MQTT/OPC-UA integration signals'],
    control: ['Energy schedules for compressors and chillers', 'Non-safety setpoint recommendations', 'Robot/AGV-ready dispatch hooks', 'Maintenance work order triggers'],
    optimize: ['Peak demand and load shedding', 'Machine-level energy waste', 'Production schedule energy planning', 'Anomaly detection and predictive maintenance'],
    maintain: ['OT gateway and network health', 'PLC/SCADA integration notes', 'Critical spare parts and SLA planning', 'Safety boundary and downtime review'],
  },
  {
    key: 'hotel',
    name: 'Hotel / Serviced Apartment',
    type: 'Guest Experience + Energy',
    level: 'L2-L4',
    boundary: 'Available Now / Project Dependent',
    icon: 'shading',
    positioning: 'A guest-room control and remote maintenance system that reduces energy waste while improving check-in, comfort, and room status visibility.',
    sense: ['Guest check-in status', 'Room occupancy', 'Housekeeping access', 'Public area CCTV and door events'],
    control: ['Welcome and away scenes', 'Room HVAC and lighting', 'Curtains and panels', 'Staff permissions'],
    optimize: ['Vacant room energy saving', 'Room comfort presets', 'Monthly energy report', 'Preventive maintenance plan'],
    maintain: ['Room device health', 'Remote troubleshooting', 'Spare panel planning', 'Service package tracking'],
  },
  {
    key: 'energy',
    name: 'Solar + Energy Site',
    type: 'AI Energy Brain',
    level: 'L3-L5',
    boundary: 'Project Dependent',
    icon: 'solar',
    positioning: 'A visibility and optimization layer for PV, battery storage, EV charging, key building loads, tariffs, alerts, and energy reporting.',
    sense: ['PV generation', 'Battery SOC', 'Inverter and meter state', 'EV charger sessions'],
    control: ['Load priority rules', 'EV charging windows', 'Battery discharge strategy', 'Critical load alerts'],
    optimize: ['Peak tariff reduction', 'PV self-consumption', 'Fault and anomaly detection', 'Monthly AI energy advice'],
    maintain: ['Inverter health', 'Meter gateway status', 'Remote diagnostics', 'Lifecycle service plan'],
  },
]

export const CAPABILITY_BLOCKS = [
  { key: 'sense', kicker: 'Sense', title: 'What the building can know', icon: 'sensor' },
  { key: 'control', kicker: 'Control', title: 'What the system can operate', icon: 'automation' },
  { key: 'optimize', kicker: 'Optimize', title: 'Where AI can help', icon: 'ai-brain' },
  { key: 'maintain', kicker: 'Maintain', title: 'How service stays alive', icon: 'lifecycle' },
] as const

export const PROPOSAL_TIERS = [
  { name: 'Budget Plan', level: 'L1-L2', estimate: 'Basic estimated range', note: 'Good for first retrofit and limited scope.', text: 'Connected control, essential sensors, CCTV/access basics, and 1-3 year support.' },
  { name: 'Standard Plan', level: 'L2-L3', estimate: 'Most practical for real projects', note: 'Recommended default for early AinerWise delivery.', text: 'Sensor automation, energy monitoring, remote maintenance, and service-ready hardware.' },
  { name: 'Premium AI Plan', level: 'L4-L5', estimate: 'Manual review required', note: 'Needs site, supplier, and engineering validation.', text: 'AI analytics, identity-aware access, local AI box, CCTV AI, and advanced energy logic.' },
  { name: 'Future Autonomous Plan', level: 'L5-L6', estimate: 'Custom engineering required', note: 'No fixed price shown.', text: 'Robot-ready building, predictive maintenance, autonomous energy decisions, and future facility brain.' },
]

export const FEATURE_TAGS = [
  { name: 'Available Now', text: 'Can usually be delivered with current hardware and normal project checks.' },
  { name: 'Project Dependent', text: 'Depends on site, wiring, protocols, product availability, and installer capability.' },
  { name: 'Advanced Custom', text: 'Requires manual engineering review and a paid design phase.' },
  { name: 'Future-Ready', text: 'Architecture can reserve this upgrade path without promising delivery today.' },
  { name: 'Concept Demo', text: 'Used to explain the vision, not as a quotation commitment.' },
]

/**
 * Intelligence levels. A KNX installation lands around L1-L2; everything above
 * needs the AI layer, which is exactly the line this page has to draw.
 */
export const INTELLIGENCE_LEVELS = [
  { level: 'L1', name: 'Connected control', knx: true, text: 'Switches, scenes and schedules on a proper bus. Reliable, but the building does not know anything.' },
  { level: 'L2', name: 'Sensor automation', knx: true, text: 'Presence, light and temperature sensors drive automatic behaviour. Still rule-based.' },
  { level: 'L3', name: 'Monitored & optimised', knx: false, text: 'Energy and equipment data is collected continuously; the platform reports what is drifting and where waste is.' },
  { level: 'L4', name: 'Predictive', knx: false, text: 'Patterns learned per site: anomalies flagged before failure, setpoints adapted to real occupancy.' },
  { level: 'L5', name: 'AI-assisted operation', knx: false, text: 'The building proposes actions in plain language; a human approves anything that costs money or changes safety behaviour.' },
  { level: 'L6', name: 'Autonomous (future)', knx: false, text: 'Robot-ready workflows and self-scheduling maintenance. Architecture reserves the path; we do not promise delivery today.' },
]

export function useBuildingBrain() {
  return {
    scenarios: BRAIN_SCENARIOS,
    capabilityBlocks: CAPABILITY_BLOCKS,
    proposalTiers: PROPOSAL_TIERS,
    featureTags: FEATURE_TAGS,
    levels: INTELLIGENCE_LEVELS,
    byKey: (key: string) => BRAIN_SCENARIOS.find((s) => s.key === key) || BRAIN_SCENARIOS[0],
  }
}
