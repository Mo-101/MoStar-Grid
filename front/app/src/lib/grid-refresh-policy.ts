/**
 * The canonical Grid is a ten-minute snapshot. Faster polling is granted
 * only to explicitly time-sensitive components; it never refreshes the
 * whole Grid implicitly.
 */
export const GRID_REFRESH = Object.freeze({
  CANONICAL_MS: 10 * 60 * 1_000,
  CANONICAL_STALE_MS: 10 * 60 * 1_000,
  SIGNAL_FEED_MS: 15 * 1_000,
  SIGNAL_STALE_MS: 5 * 1_000,
  WEATHER_MS: 2 * 60 * 1_000,
  WEATHER_STALE_MS: 60 * 1_000,
  SERVICE_HEALTH_MS: 5 * 60 * 1_000,
  SERVICE_HEALTH_STALE_MS: 2 * 60 * 1_000,
} as const);
