/**
 * gridSnapshot.ts — composes a spoken briefing from live grid data.
 *
 * WHAT WAS WRONG
 *   statusWord() took a percentage. At 80% it said "fully operational" —
 *   and 80% was the average of five booleans, one of which was the DCX
 *   Trinity being offline. The Grid would have announced its own health in
 *   Piper's voice while its reasoning stack was dark.
 *
 * WHAT CHANGED
 *   The verdict now comes from the worst critical dependency. The percentage
 *   is reported as evidence, never as the ruling. The briefing states how old
 *   its own data is, because a confident reading of stale numbers is worse
 *   than silence.
 */

import { SEVERITY_VERDICT, timeAgo, freshnessOf, type Severity } from "./gridTruth";

export interface SnapshotMetrics {
  nodes: number | null;
  relationships: number | null;
  /** Sealed count over total — evidence, not verdict. */
  sealedChecks: number;
  totalChecks: number;
  /** The ruling. Worst of the critical dependencies. */
  verdict: Severity;
  degradedLabels: string[];
  advisorCount: number | null;
  queuePending: number | null;
  queueCommittedToday: number | null;
  latestFeed: { agent: string; text: string; at: string } | null;
  /** When the underlying grid-status payload was produced. */
  asOf: string | null;
}

function joinWithAnd(items: string[]): string {
  if (items.length <= 1) return items[0] ?? "";
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`;
}

function verdictSentence(v: Severity): string {
  switch (v) {
    case "SEALED":
      return "All critical systems sealed.";
    case "DEGRADED":
      return "Operating degraded.";
    case "DOWN":
      return "Critical dependency down.";
    default:
      return "Status unverified.";
  }
}

/** Speak numbers as numbers, not as digit strings Piper will mangle. */
function spoken(n: number): string {
  return n.toLocaleString("en-US");
}

export function buildSnapshotSegments(
  metrics: SnapshotMetrics,
  previous: SnapshotMetrics | null = null,
): string[] {
  const segments: string[] = [];
  const fresh = freshnessOf(metrics.asOf);

  /* --- 1. The ruling, first, before any comforting numbers. --- */
  segments.push(`Grid pulse check. ${verdictSentence(metrics.verdict)}`);

  /* --- 2. Provenance. The briefing declares its own age. --- */
  if (fresh === "STALE") {
    segments.push(
      `Warning: this reading is ${timeAgo(metrics.asOf)}. Treat the following as historical, not current.`,
    );
  } else if (fresh === "UNKNOWN") {
    segments.push(
      "Warning: the grid status payload carries no timestamp. Freshness cannot be confirmed.",
    );
  }

  /* --- 3. Graph. --- */
  if (metrics.nodes != null && metrics.relationships != null) {
    let line = `The mind graph holds ${spoken(metrics.nodes)} nodes and ${spoken(
      metrics.relationships,
    )} relationships.`;
    const delta = previous?.nodes != null ? metrics.nodes - previous.nodes : 0;
    if (delta > 0) {
      line += ` ${spoken(delta)} new node${delta === 1 ? "" : "s"} since the last check.`;
    } else if (delta < 0) {
      line += ` ${spoken(Math.abs(delta))} node${delta === -1 ? "" : "s"} fewer than the last check.`;
    }
    segments.push(line);
  } else {
    segments.push(
      "The mind graph has not reported in. Node and relationship counts are unavailable.",
    );
  }

  /* --- 4. Council. --- */
  if (metrics.advisorCount != null && metrics.advisorCount > 0) {
    segments.push(
      `${metrics.advisorCount} council advisor${metrics.advisorCount === 1 ? "" : "s"} registered.`,
    );
  } else {
    segments.push("The council channel is unreachable.");
  }

  /* --- 5. Vitals. Evidence after the ruling, never instead of it. --- */
  if (metrics.degradedLabels.length > 0) {
    segments.push(
      `${metrics.sealedChecks} of ${metrics.totalChecks} systems sealed. ${joinWithAnd(
        metrics.degradedLabels,
      )} ${metrics.degradedLabels.length > 1 ? "are" : "is"} not sealed.`,
    );
  } else {
    segments.push(`All ${metrics.totalChecks} systems sealed.`);
  }

  /* --- 6. Queue. --- */
  if (metrics.queuePending != null) {
    segments.push(
      `${metrics.queuePending} item${metrics.queuePending === 1 ? "" : "s"} pending review. ${
        metrics.queueCommittedToday ?? 0
      } sealed today.`,
    );
  }

  /* --- 7. Signal, with its own age attached. --- */
  if (metrics.latestFeed) {
    segments.push(
      `Most recent signal, ${timeAgo(metrics.latestFeed.at)}, from ${metrics.latestFeed.agent}. ${
        metrics.latestFeed.text
      }`,
    );
  } else {
    segments.push("No signals recorded.");
  }

  return segments;
}

/**
 * Reading-time estimate for the SILENT fallback only.
 *
 * This is not a duration and must never be published as one. When Piper is
 * alive, real per-segment durations come from /narrate, measured off the WAV
 * headers. This exists so the ceremony can still be paced with no voice at
 * all.
 */
export function estimateSegmentDurations(segments: string[]): number[] {
  const MS_PER_CHAR = 55; // ≈ 215 wpm
  const PAUSE_MS = 350; // breath between segments
  return segments.map((text) => Math.max(1_200, text.length * MS_PER_CHAR) + PAUSE_MS);
}

/** Convenience: turn estimates into the same segment shape /narrate returns. */
export function silentSegmentPlan(segments: string[]) {
  const durations = estimateSegmentDurations(segments);
  let cursor = 0;
  return segments.map((text, i) => {
    const start = cursor;
    cursor += durations[i];
    return { text, start_ms: start, end_ms: cursor };
  });
}
