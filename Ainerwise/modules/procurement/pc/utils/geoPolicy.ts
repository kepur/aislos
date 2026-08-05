export type SupportedRegionOption = {
  code: string
  label?: string
  name?: string
}

export type LocationGuess = {
  countryCode: string
  countryName: string
  city?: string
  latitude?: number
  longitude?: number
  confidence: 'high' | 'medium' | 'low'
  source: 'coordinates' | 'timezone'
}

type GeoRule = {
  code: string
  countryName: string
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
  cities: Array<{ name: string; lat: number; lng: number }>
}

const GEO_RULES: GeoRule[] = [
  {
    code: 'RS',
    countryName: 'Serbia',
    minLat: 42.0,
    maxLat: 46.3,
    minLng: 18.8,
    maxLng: 23.1,
    cities: [
      { name: 'Belgrade', lat: 44.8125, lng: 20.4612 },
      { name: 'Novi Sad', lat: 45.2671, lng: 19.8335 },
      { name: 'Nis', lat: 43.3209, lng: 21.8958 },
    ],
  },
  {
    code: 'PL',
    countryName: 'Poland',
    minLat: 49.0,
    maxLat: 54.9,
    minLng: 14.1,
    maxLng: 24.2,
    cities: [
      { name: 'Warsaw', lat: 52.2297, lng: 21.0122 },
      { name: 'Krakow', lat: 50.0647, lng: 19.945 },
      { name: 'Wroclaw', lat: 51.1079, lng: 17.0385 },
      { name: 'Gdansk', lat: 54.352, lng: 18.6466 },
    ],
  },
  {
    code: 'PH',
    countryName: 'Philippines',
    minLat: 4.5,
    maxLat: 21.5,
    minLng: 116.0,
    maxLng: 127.0,
    cities: [
      { name: 'Cebu City', lat: 10.3157, lng: 123.8854 },
      { name: 'Manila', lat: 14.5995, lng: 120.9842 },
      { name: 'Davao City', lat: 7.1907, lng: 125.4553 },
    ],
  },
  {
    code: 'BA',
    countryName: 'Bosnia and Herzegovina',
    minLat: 42.5,
    maxLat: 45.4,
    minLng: 15.7,
    maxLng: 19.7,
    cities: [
      { name: 'Sarajevo', lat: 43.8563, lng: 18.4131 },
      { name: 'Banja Luka', lat: 44.7722, lng: 17.191 },
      { name: 'Mostar', lat: 43.3438, lng: 17.8078 },
    ],
  },
  {
    code: 'RO',
    countryName: 'Romania',
    minLat: 43.5,
    maxLat: 48.3,
    minLng: 20.2,
    maxLng: 29.8,
    cities: [
      { name: 'Bucharest', lat: 44.4268, lng: 26.1025 },
      { name: 'Cluj-Napoca', lat: 46.7712, lng: 23.6236 },
      { name: 'Timisoara', lat: 45.7489, lng: 21.2087 },
    ],
  },
]

const TIMEZONE_COUNTRY_MAP: Record<string, string> = {
  'Europe/Belgrade': 'RS',
  'Europe/Warsaw': 'PL',
  'Asia/Manila': 'PH',
  'Europe/Sarajevo': 'BA',
  'Europe/Bucharest': 'RO',
}

export function allowedCountryCodes(regions: SupportedRegionOption[]) {
  return new Set(
    regions
      .map((region) => String(region.code || '').trim().toUpperCase().slice(0, 2))
      .filter(Boolean),
  )
}

export function countryLabel(code: string, regions: SupportedRegionOption[]) {
  const normalized = String(code || '').toUpperCase().slice(0, 2)
  const configured = regions.find((region) => String(region.code || '').toUpperCase().slice(0, 2) === normalized)
  return configured?.label || configured?.name || GEO_RULES.find((rule) => rule.code === normalized)?.countryName || normalized
}

export function inferLocationFromCoords(
  latitude: number,
  longitude: number,
  supportedRegions: SupportedRegionOption[] = [],
): LocationGuess | null {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  const allowed = allowedCountryCodes(supportedRegions)
  const rule = GEO_RULES.find((candidate) => (
    latitude >= candidate.minLat &&
    latitude <= candidate.maxLat &&
    longitude >= candidate.minLng &&
    longitude <= candidate.maxLng &&
    (!allowed.size || allowed.has(candidate.code))
  ))
  if (!rule) return null

  return {
    countryCode: rule.code,
    countryName: countryLabel(rule.code, supportedRegions),
    city: nearestCity(rule, latitude, longitude),
    latitude,
    longitude,
    confidence: 'medium',
    source: 'coordinates',
  }
}

export function inferLocationFromTimezone(
  timeZone?: string | null,
  supportedRegions: SupportedRegionOption[] = [],
): LocationGuess | null {
  const countryCode = TIMEZONE_COUNTRY_MAP[String(timeZone || '')]
  if (!countryCode) return null
  const allowed = allowedCountryCodes(supportedRegions)
  if (allowed.size && !allowed.has(countryCode)) return null
  const rule = GEO_RULES.find((candidate) => candidate.code === countryCode)
  return {
    countryCode,
    countryName: countryLabel(countryCode, supportedRegions),
    city: rule?.cities[0]?.name,
    confidence: 'low',
    source: 'timezone',
  }
}

function nearestCity(rule: GeoRule, latitude: number, longitude: number) {
  let nearest = rule.cities[0]
  let nearestDistance = Number.POSITIVE_INFINITY
  for (const city of rule.cities) {
    const distance = Math.hypot(city.lat - latitude, city.lng - longitude)
    if (distance < nearestDistance) {
      nearest = city
      nearestDistance = distance
    }
  }
  return nearest?.name
}
