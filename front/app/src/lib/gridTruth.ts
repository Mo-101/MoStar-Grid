/**
 * gridTruth.ts — the arbiter primitives.
 *
 * DOCTRINE
 *   A system is as healthy as its worst critical dependency. Averaging
 *   disagreement into a single soothing number is the Silent Wound, and it
 *   is how a green ring came to sit eleven pixels above "DCX TRINITY —
 *   OFFLINE".
 *
 *   Nothing may call itself LIVE without a timestamp to back the claim.
 */

export type Severity = "SEALED" | "UNKNOWN" | "DEGRADED" | "DOWN";

const RANK: Record<Severity, number> = {
  SEALED: 0,
  UNKNOWN: 1,
  DEGRADED: 2,
  DOWN: 3,
};

export const SEVERITY_COLOR: Record<Severity, string> = {
  SEALED: "var(--color-neon-green)",
  UNKNOWN: "oklch(0.62 0.02 260)",
  DEGRADED: "var(--color-neon-orange)",
  DOWN: "var(--color-neon-red)",
};

export const SEVERITY_VERDICT: Record<Severity, string> = {
  SEALED: "OPERATIONAL",
  UNKNOWN: "UNVERIFIED",
  DEGRADED: "DEGRADED",
  DOWN: "CRITICAL",
};

/** The whole is the worst of its parts. Never the mean. */
export function worst(list: Severity[]): Severity {
  if (!list.length) return "UNKNOWN";
  return list.reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "SEALED" as Severity);
}

/* ------------------------------------------------------------------ */
/* Freshness                                                           */
/* ------------------------------------------------------------------ */

export type Freshness = "LIVE" | "RECENT" | "STALE" | "UNKNOWN";

export const LIVE_WINDOW_MS = 60_000;
export const RECENT_WINDOW_MS = 15 * 60_000;

export function ageMs(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const t = new Date(iso).getTime();
  return Number.isFinite(t) ? Math.max(0, Date.now() - t) : null;
}

export function freshnessOf(iso: string | null | undefined): Freshness {
  const age = ageMs(iso);
  if (age == null) return "UNKNOWN";
  if (age < LIVE_WINDOW_MS) return "LIVE";
  if (age < RECENT_WINDOW_MS) return "RECENT";
  return "STALE";
}

export const FRESHNESS_COLOR: Record<Freshness, string> = {
  LIVE: "var(--color-neon-green)",
  RECENT: "var(--color-neon-cyan)",
  STALE: "var(--color-neon-orange)",
  UNKNOWN: "oklch(0.62 0.02 260)",
};

/**
 * timeAgo that does not stop at hours. "413h ago" was the old output for
 * seventeen days — technically true, practically a disguise.
 */
export function timeAgo(iso: string | null | undefined): string {
  const age = ageMs(iso);
  if (age == null) return "unknown";

  const s = Math.round(age / 1000);
  if (s < 5) return "just now";
  if (s < 60) return `${s}s ago`;

  const m = Math.round(s / 60);
  if (m < 60) return `${m}m ago`;

  const h = Math.round(m / 60);
  if (h < 24) return `${h}h ago`;

  const d = Math.round(h / 24);
  if (d < 30) return `${d}d ago`;

  const mo = Math.round(d / 30);
  return `${mo}mo ago`;
}

/** The badge a KPI is allowed to wear, given when its data actually arrived. */
export function liveBadge(iso: string | null | undefined): {
  text: string;
  color: string;
  freshness: Freshness;
} {
  const f = freshnessOf(iso);
  const color = FRESHNESS_COLOR[f];
  if (f === "UNKNOWN") return { text: "CONNECTING…", color, freshness: f };
  if (f === "LIVE") return { text: `LIVE · ${timeAgo(iso).toUpperCase()}`, color, freshness: f };
  return { text: `LAST SEEN ${timeAgo(iso).toUpperCase()}`, color, freshness: f };
}
