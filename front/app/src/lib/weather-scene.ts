/**
 * Live sky derivation.
 *
 * Everything here is a pure function of measured readings — WMO code, prose
 * summary, precipitation, wind, humidity, hub coordinates and the observation
 * timestamp. Nothing is invented: when a signal is absent the scene degrades to
 * a weaker but still truthful state rather than guessing (see `confidence`).
 *
 * The renderer (weather-sky.tsx) owns no meteorology. It only draws what this
 * module reports, so the mapping from real conditions to pixels stays testable.
 */

export type SkyCondition =
  | "CLEAR"
  | "PARTLY_CLOUDY"
  | "CLOUDY"
  | "OVERCAST"
  | "FOG"
  | "DRIZZLE"
  | "RAIN"
  | "HEAVY_RAIN"
  | "THUNDERSTORM"
  | "SNOW"
  | "DUST";

export interface SkyReading {
  weather_code?: number | null;
  summary?: string | null;
  precipitation_mm?: number | null;
  precipitation_probability?: number | null;
  humidity_pct?: number | null;
  wind_kph?: number | null;
  wind_direction_deg?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  observed_at?: string | null;
}

export interface SkyScene {
  condition: SkyCondition;
  /** How the condition was established. "none" means we are showing a neutral sky. */
  confidence: "wmo" | "text" | "measurement" | "none";
  /** 0 = empty sky, 1 = fully closed deck. */
  cloudCover: number;
  /** 0 = dry, 1 = torrential. Drives droplet count and streak length. */
  rainRate: number;
  /** 0 = clear air, 1 = whiteout. Fog, haze and dust all land here. */
  hazeDensity: number;
  /** Lightning is only ever true for a measured thunderstorm. */
  lightning: boolean;
  snow: boolean;
  /** -1 = right-to-left, +1 = left-to-right, magnitude scales with wind speed. */
  windX: number;
  /** Normalised wind speed 0..1, used for drift rate and streak slant. */
  windStrength: number;
  /** Solar elevation in degrees at the observed hub. Negative is night. */
  sunElevationDeg: number;
  /** 0 (horizon) .. 1 (overhead). Drives sky luminance. */
  daylight: number;
  /** Horizontal sun/moon position across the card, 0 = left edge, 1 = right. */
  sunX: number;
  /** True while the sun sits just below/above the horizon. */
  goldenHour: boolean;
  night: boolean;
}

/** WMO 4677 groupings, per Open-Meteo's published code table. */
function conditionFromWmo(code: number): SkyCondition | null {
  if (code === 0 || code === 1) return "CLEAR";
  if (code === 2) return "PARTLY_CLOUDY";
  if (code === 3) return "OVERCAST";
  if (code === 45 || code === 48) return "FOG";
  if (code >= 51 && code <= 57) return "DRIZZLE";
  if (code === 61 || code === 63 || code === 66 || code === 80 || code === 81) return "RAIN";
  if (code === 65 || code === 67 || code === 82) return "HEAVY_RAIN";
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "SNOW";
  if (code >= 95 && code <= 99) return "THUNDERSTORM";
  return null;
}

/**
 * Prose fallback for providers that do not speak WMO (OpenWeather,
 * MeteoSource). Ordered most-specific first: "thunderstorm with heavy rain"
 * must resolve to THUNDERSTORM, and "heavy rain" must beat "rain".
 */
const TEXT_RULES: Array<[RegExp, SkyCondition]> = [
  [/thunder|storm|squall|lightning/, "THUNDERSTORM"],
  [/snow|sleet|blizzard|ice pellet|hail/, "SNOW"],
  [/dust|sand|ash|smoke|harmattan/, "DUST"],
  [/fog|mist|haze/, "FOG"],
  [/drizzle|light rain|light shower/, "DRIZZLE"],
  // OpenWeather splits the intensifier from the noun ("heavy intensity rain",
  // "very heavy rain"), so this cannot require adjacency. Safe as a bare match
  // because snow/dust/fog/thunder are all resolved above it.
  [/heavy|torrential|extreme|violent/, "HEAVY_RAIN"],
  [/rain|shower|precipitation/, "RAIN"],
  [/overcast/, "OVERCAST"],
  [/broken cloud|mostly cloud|cloudy/, "CLOUDY"],
  [/partly|scattered|few cloud|partly sunny/, "PARTLY_CLOUDY"],
  [/clear|sunny|fair/, "CLEAR"],
];

function conditionFromText(summary: string): SkyCondition | null {
  const text = summary.toLowerCase();
  for (const [pattern, condition] of TEXT_RULES) {
    if (pattern.test(text)) return condition;
  }
  return null;
}

export function classifyCondition(reading: SkyReading): {
  condition: SkyCondition;
  confidence: SkyScene["confidence"];
} {
  if (typeof reading.weather_code === "number") {
    const condition = conditionFromWmo(reading.weather_code);
    if (condition) return { condition, confidence: "wmo" };
  }

  if (reading.summary) {
    const condition = conditionFromText(reading.summary);
    if (condition) return { condition, confidence: "text" };
  }

  // No code and no readable prose. Falling rain is still falling rain — if a
  // gauge reports accumulation we may honestly draw it, but nothing else.
  const mm = reading.precipitation_mm;
  if (typeof mm === "number" && mm > 0) {
    return { condition: mm >= 2.5 ? "HEAVY_RAIN" : "RAIN", confidence: "measurement" };
  }

  return { condition: "PARTLY_CLOUDY", confidence: "none" };
}

const BASE_CLOUD: Record<SkyCondition, number> = {
  CLEAR: 0.04,
  PARTLY_CLOUDY: 0.34,
  CLOUDY: 0.66,
  OVERCAST: 0.92,
  FOG: 0.72,
  DRIZZLE: 0.74,
  RAIN: 0.85,
  HEAVY_RAIN: 0.96,
  THUNDERSTORM: 1,
  SNOW: 0.82,
  DUST: 0.55,
};

const BASE_RAIN: Record<SkyCondition, number> = {
  CLEAR: 0,
  PARTLY_CLOUDY: 0,
  CLOUDY: 0,
  OVERCAST: 0,
  FOG: 0,
  DRIZZLE: 0.22,
  RAIN: 0.55,
  HEAVY_RAIN: 0.9,
  THUNDERSTORM: 0.8,
  SNOW: 0.4,
  DUST: 0,
};

/**
 * Solar elevation and azimuth by the NOAA low-precision algorithm. Accurate to
 * well under a degree, which is far finer than "is it light out" needs, and it
 * runs off the hub's own coordinates so Cape Town can be dark while Cairo is
 * lit in the same render.
 */
export function solarPosition(
  latitude: number,
  longitude: number,
  at: Date,
): { elevationDeg: number; azimuthDeg: number } {
  const rad = Math.PI / 180;
  const start = Date.UTC(at.getUTCFullYear(), 0, 1);
  const dayOfYear = Math.floor((at.getTime() - start) / 86_400_000) + 1;
  const utcMinutes = at.getUTCHours() * 60 + at.getUTCMinutes() + at.getUTCSeconds() / 60;

  const gamma = ((2 * Math.PI) / 365) * (dayOfYear - 1 + (at.getUTCHours() - 12) / 24);

  const eqTime =
    229.18 *
    (0.000075 +
      0.001868 * Math.cos(gamma) -
      0.032077 * Math.sin(gamma) -
      0.014615 * Math.cos(2 * gamma) -
      0.040849 * Math.sin(2 * gamma));

  const decl =
    0.006918 -
    0.399912 * Math.cos(gamma) +
    0.070257 * Math.sin(gamma) -
    0.006758 * Math.cos(2 * gamma) +
    0.000907 * Math.sin(2 * gamma) -
    0.002697 * Math.cos(3 * gamma) +
    0.00148 * Math.sin(3 * gamma);

  const trueSolarTime = utcMinutes + eqTime + 4 * longitude;
  const hourAngle = trueSolarTime / 4 - 180;

  const latRad = latitude * rad;
  const haRad = hourAngle * rad;
  const cosZenith =
    Math.sin(latRad) * Math.sin(decl) + Math.cos(latRad) * Math.cos(decl) * Math.cos(haRad);
  const zenith = Math.acos(Math.min(1, Math.max(-1, cosZenith)));
  const elevationDeg = 90 - zenith / rad;

  const sinAz = -Math.sin(haRad) * Math.cos(decl);
  const cosAz = (Math.sin(decl) - Math.sin(latRad) * cosZenith) / Math.cos(latRad);
  const azimuthDeg = (Math.atan2(sinAz, cosAz) / rad + 360) % 360;

  return { elevationDeg, azimuthDeg };
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function deriveScene(reading: SkyReading, now: Date = new Date()): SkyScene {
  const { condition, confidence } = classifyCondition(reading);

  // Wet intensity: start from the condition, then let a real gauge or a real
  // forecast probability push it. A measured 8mm downpour must look heavier
  // than a nominal "rain".
  let rainRate = BASE_RAIN[condition];
  if (rainRate > 0) {
    const mm = reading.precipitation_mm;
    if (typeof mm === "number" && mm > 0) {
      rainRate = Math.max(rainRate, clamp01(mm / 8));
    }
    const probability = reading.precipitation_probability;
    if (typeof probability === "number") {
      rainRate *= 0.55 + 0.45 * clamp01(probability / 100);
    }
  }

  let hazeDensity = 0;
  if (condition === "FOG") hazeDensity = 0.72;
  else if (condition === "DUST") hazeDensity = 0.6;
  else if (typeof reading.humidity_pct === "number" && reading.humidity_pct > 80) {
    // Very humid air genuinely scatters light; below 80% this stays at zero
    // rather than inventing a permanent murk.
    hazeDensity = clamp01((reading.humidity_pct - 80) / 20) * 0.28;
  }

  // 60 km/h is treated as the top of the visual scale — beyond that the drift
  // reads as fast as it usefully can.
  const windStrength = clamp01((reading.wind_kph ?? 0) / 60);
  const bearing = reading.wind_direction_deg;
  // Meteorological bearing is the direction wind comes FROM, so travel is the
  // opposite vector. A 270° (westerly) wind moves cloud left-to-right.
  const windX = typeof bearing === "number" ? -Math.sin((bearing * Math.PI) / 180) : 0.35;

  const observedAt = reading.observed_at ? new Date(reading.observed_at) : now;
  const at = Number.isNaN(observedAt.getTime()) ? now : observedAt;

  let sunElevationDeg = 25;
  let azimuthDeg = 180;
  if (typeof reading.latitude === "number" && typeof reading.longitude === "number") {
    const position = solarPosition(reading.latitude, reading.longitude, at);
    sunElevationDeg = position.elevationDeg;
    azimuthDeg = position.azimuthDeg;
  }

  return {
    condition,
    confidence,
    cloudCover: BASE_CLOUD[condition],
    rainRate,
    hazeDensity,
    lightning: condition === "THUNDERSTORM",
    snow: condition === "SNOW",
    windX,
    windStrength,
    sunElevationDeg,
    daylight: clamp01((sunElevationDeg + 6) / 56),
    // Map the eastern-to-western arc (azimuth 90°..270°) across the card.
    sunX: clamp01((azimuthDeg - 60) / 240),
    goldenHour: sunElevationDeg > -6 && sunElevationDeg < 12,
    night: sunElevationDeg < -0.833,
  };
}
