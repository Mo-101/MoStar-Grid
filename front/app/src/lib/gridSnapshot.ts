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
import type { AfricaSenses, GraphSemanticAccounting } from "@/services/gridApiClient";

export interface SnapshotMetrics {
  /**
   * TOTAL graph population — a raw node count, not a knowledge measurement.
   * Named explicitly so no caller can mistake it for corpus size.
   */
  totalNodes: number | null;
  relationships: number | null;
  /**
   * Backend-owned semantic classification. Null until the accounting layer
   * ships; the briefing must stay silent about knowledge scale while it is.
   */
  semanticAccounting?: GraphSemanticAccounting | null;
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

/**
 * The conservation law, checked before any class count is spoken:
 *
 *     T = K + O + A + S + X + U
 *
 * A partition that does not close means at least one node was double-counted
 * or dropped, which makes every class in it unsafe to quote. Multi-label nodes
 * are exactly how such a partition silently fails, so this is verified at the
 * consumption boundary rather than trusted from the producer.
 */
export function isPartitionSound(accounting: GraphSemanticAccounting): boolean {
  const sum =
    accounting.knowledge_nodes +
    accounting.operational_nodes +
    accounting.audit_nodes +
    accounting.system_nodes +
    accounting.test_nodes +
    accounting.unknown_nodes;
  return sum === accounting.total_graph_nodes;
}

/**
 * How the Grid is permitted to describe its own memory scale.
 *
 * A raw graph-wide count is total population, never knowledge. Until a sound
 * classification exists, the briefing states the total and says plainly that
 * composition is unverified — it does not round the uncertainty away, and it
 * does not go silent either.
 */
export function graphScaleSentence(metrics: SnapshotMetrics): string {
  const total = metrics.totalNodes;
  if (total == null) {
    return "The mind graph has not reported in. Node counts are unavailable.";
  }

  const accounting = metrics.semanticAccounting;

  // No accounting layer, or a partition that does not close: total only.
  if (!accounting || !isPartitionSound(accounting)) {
    const caveat = accounting
      ? "its semantic partition does not reconcile, so knowledge composition is unverified"
      : "knowledge-node composition remains under verification";
    return `The governed graph currently contains ${spoken(total)} total nodes; ${caveat}.`;
  }

  let line =
    `The governed graph holds ${spoken(accounting.total_graph_nodes)} total nodes, ` +
    `of which ${spoken(accounting.knowledge_nodes)} ${
      accounting.knowledge_nodes === 1 ? "is classified" : "are classified"
    } as knowledge.`;

  // Unknown material is reported, never absorbed into a cleaner-sounding class.
  if (accounting.unknown_nodes > 0) {
    line += ` ${spoken(accounting.unknown_nodes)} node${
      accounting.unknown_nodes === 1 ? " remains" : "s remain"
    } unclassified.`;
  }

  return line;
}

/**
 * Continental précis, reduced from the live senses payload.
 *
 * This is a summary OF canon, never a replacement for it — the canonical
 * Africa segments still follow verbatim, carrying their own digest. Nothing
 * here is inferred: every field is counted or measured from the payload, and
 * anything unobserved stays null so the overview can omit it rather than
 * guess.
 */
export interface ContinentOptics {
  hubsObserved: number;
  hubsConfigured: number;
  regions: number;
  jurisdictions: number;
  liveSources: number;
  totalSources: number;
  consensusHubs: number;
  divergentHubs: number;
  warmest: { location: string; temperatureC: number } | null;
  coldest: { location: string; temperatureC: number } | null;
  wettest: { location: string; probability: number } | null;
  weatherState: string;
  healthState: string;
  sovereigntyState: string;
  canonSegments: number;
}

export function deriveContinentOptics(
  senses: AfricaSenses | null | undefined,
): ContinentOptics | null {
  if (!senses) return null;

  const locations = senses.weather.locations ?? [];
  const observed = locations.filter((item) => (item.provider_count ?? 0) > 0);
  const measured = observed.filter(
    (item): item is typeof item & { temperature_c: number } =>
      typeof item.temperature_c === "number",
  );

  const sorted = [...measured].sort((a, b) => a.temperature_c - b.temperature_c);
  const rainiest = observed
    .filter(
      (item): item is typeof item & { precipitation_probability: number } =>
        typeof item.precipitation_probability === "number",
    )
    .sort((a, b) => b.precipitation_probability - a.precipitation_probability)[0];

  const providers = Object.values(senses.weather.providers ?? {});

  return {
    hubsObserved: observed.length,
    hubsConfigured: locations.length,
    regions: senses.coverage?.regions_observed?.length ?? 0,
    jurisdictions: senses.coverage?.jurisdictions ?? 0,
    liveSources: providers.filter((state) => state === "HEALTHY").length,
    totalSources: providers.length,
    consensusHubs: observed.filter((item) => item.epistemic_state === "CONSENSUS").length,
    divergentHubs: observed.filter((item) => item.epistemic_state === "DIVERGENT").length,
    coldest: sorted[0]
      ? { location: sorted[0].location, temperatureC: sorted[0].temperature_c }
      : null,
    warmest: sorted.at(-1)
      ? { location: sorted.at(-1)!.location, temperatureC: sorted.at(-1)!.temperature_c }
      : null,
    // Only worth speaking when rain is actually likely somewhere.
    wettest:
      rainiest && rainiest.precipitation_probability >= 50
        ? { location: rainiest.location, probability: rainiest.precipitation_probability }
        : null,
    weatherState: senses.weather.state,
    healthState: senses.health.state,
    sovereigntyState: senses.sovereignty.state,
    canonSegments: senses.canonical_report?.segments?.length ?? 0,
  };
}

/**
 * The executive overview that opens every briefing.
 *
 * A briefing that opens with "the mind graph holds 12,431 nodes" buries the
 * one thing a listener needs in the first two seconds. This leads with the
 * ruling, follows with the scale of what is being ruled on, then states the
 * continental picture, and closes by naming exactly what needs attention —
 * so the detail segments that follow are heard as evidence, not as news.
 */
export function buildOverviewSegments(
  metrics: SnapshotMetrics | null,
  optics: ContinentOptics | null,
): string[] {
  const segments: string[] = [];

  /* --- 1. Grid: the ruling, then the scale behind it. --- */
  if (metrics) {
    const parts = [`Grid overview. ${verdictSentence(metrics.verdict)}`];
    const evidence: string[] = [`${metrics.sealedChecks} of ${metrics.totalChecks} systems sealed`];
    if (metrics.advisorCount != null && metrics.advisorCount > 0) {
      evidence.push(
        `${metrics.advisorCount} council advisor${metrics.advisorCount === 1 ? "" : "s"} online`,
      );
    }
    if (metrics.relationships != null) {
      evidence.push(`${spoken(metrics.relationships)} graph relationships`);
    }
    parts.push(`${joinWithAnd(evidence)}.`);
    // Node scale is never folded into the headline's evidence list, because a
    // bare count there reads as a knowledge claim. It gets its own sentence,
    // qualified by whatever the classification layer can actually prove.
    parts.push(graphScaleSentence(metrics));
    segments.push(parts.join(" "));
  }

  /* --- 2. Continent optics: coverage first, then what the readings say. --- */
  if (optics) {
    const optic = [
      `Continent optics. ${optics.hubsObserved} of ${optics.hubsConfigured} observation hub${
        optics.hubsConfigured === 1 ? "" : "s"
      } reporting across ${optics.regions} region${optics.regions === 1 ? "" : "s"}, ` +
        `${optics.liveSources} of ${optics.totalSources} weather source${
          optics.totalSources === 1 ? "" : "s"
        } live.`,
    ];

    if (optics.warmest && optics.coldest && optics.warmest.location !== optics.coldest.location) {
      optic.push(
        `Temperatures span ${Math.round(optics.coldest.temperatureC)} degrees at ${
          optics.coldest.location
        } to ${Math.round(optics.warmest.temperatureC)} at ${optics.warmest.location}.`,
      );
    }

    if (optics.consensusHubs || optics.divergentHubs) {
      const agreement = [`${optics.consensusHubs} in cross-source consensus`];
      if (optics.divergentHubs) agreement.push(`${optics.divergentHubs} divergent`);
      optic.push(`${joinWithAnd(agreement)}.`);
    }

    if (optics.wettest) {
      optic.push(
        `Rain most likely at ${optics.wettest.location}, ${Math.round(
          optics.wettest.probability,
        )} percent.`,
      );
    }

    segments.push(optic.join(" "));
  }

  /* --- 3. Exceptions, named explicitly. Silence here must mean "clear". --- */
  const attention: string[] = [];
  if (metrics?.degradedLabels.length) {
    attention.push(
      `${joinWithAnd(metrics.degradedLabels)} ${
        metrics.degradedLabels.length > 1 ? "are" : "is"
      } not sealed`,
    );
  }
  if (metrics && freshnessOf(metrics.asOf) === "STALE") {
    attention.push(`the grid reading is ${timeAgo(metrics.asOf)}`);
  }
  if (optics && optics.divergentHubs > 0) {
    const n = optics.divergentHubs;
    attention.push(`${n} hub${n === 1 ? " reports" : "s report"} sources that disagree`);
  }
  if (optics && optics.hubsObserved < optics.hubsConfigured) {
    const silent = optics.hubsConfigured - optics.hubsObserved;
    attention.push(`${silent} hub${silent === 1 ? " has" : "s have"} no current source`);
  }
  if (optics && optics.healthState !== "HEALTHY" && optics.healthState !== "LIVE") {
    attention.push(`health reporting is ${optics.healthState.toLowerCase()}`);
  }
  if (optics && optics.sovereigntyState !== "HEALTHY" && optics.sovereigntyState !== "LIVE") {
    attention.push(`sovereignty reporting is ${optics.sovereigntyState.toLowerCase()}`);
  }

  if (attention.length) {
    segments.push(`Requiring attention. ${joinWithAnd(attention)}.`);
  } else if (segments.length) {
    segments.push("Nothing is currently flagged for attention. Detail follows.");
  }

  return segments;
}

export function buildSnapshotSegments(
  metrics: SnapshotMetrics,
  previous: SnapshotMetrics | null = null,
  options: { precededByOverview?: boolean } = {},
): string[] {
  const segments: string[] = [];
  const fresh = freshnessOf(metrics.asOf);

  // When an overview has already opened the briefing, it has stated the
  // verdict, the sealed ratio, the degraded systems by name, the advisor count
  // and the graph size. Repeating all of that here is how a briefing stops
  // being listened to. The detail then carries only what the overview could
  // not: movement since the last check, and exceptions.
  const brief = options.precededByOverview === true;

  /* --- 1. The ruling, first, before any comforting numbers. --- */
  if (!brief) {
    segments.push(`Grid pulse check. ${verdictSentence(metrics.verdict)}`);
  }

  /* --- 2. Provenance. The briefing declares its own age. --- */
  // The overview's attention segment already flags a stale reading; an absent
  // timestamp is always worth restating, because it cannot be flagged as an age.
  if (fresh === "STALE" && !brief) {
    segments.push(
      `Warning: this reading is ${timeAgo(metrics.asOf)}. Treat the following as historical, not current.`,
    );
  } else if (fresh === "UNKNOWN") {
    segments.push(
      "Warning: the grid status payload carries no timestamp. Freshness cannot be confirmed.",
    );
  }

  /* --- 3. Graph. --- */
  if (metrics.totalNodes != null && metrics.relationships != null) {
    const delta = previous?.totalNodes != null ? metrics.totalNodes - previous.totalNodes : 0;
    // Movement is a delta in TOTAL population and is stated as such. It is not
    // evidence that the knowledge corpus grew — new nodes may be operational,
    // audit or test material until the classification layer proves otherwise.
    let line = brief ? "" : graphScaleSentence(metrics);
    if (delta > 0) {
      line += `${line ? " " : "The governed graph has taken "}${spoken(delta)} new node${
        delta === 1 ? "" : "s"
      } since the last check.`;
    } else if (delta < 0) {
      line += `${line ? " " : "The governed graph is "}${spoken(Math.abs(delta))} node${
        delta === -1 ? "" : "s"
      } fewer than the last check.`;
    }
    // In brief mode an unchanged graph is not news and is left unsaid.
    if (line) segments.push(line);
  } else {
    segments.push(
      "The mind graph has not reported in. Node and relationship counts are unavailable.",
    );
  }

  /* --- 4. Council. Only an unreachable channel is news after the overview. --- */
  if (metrics.advisorCount != null && metrics.advisorCount > 0) {
    if (!brief) {
      segments.push(
        `${metrics.advisorCount} council advisor${metrics.advisorCount === 1 ? "" : "s"} registered.`,
      );
    }
  } else {
    segments.push("The council channel is unreachable.");
  }

  /* --- 5. Vitals. Evidence after the ruling, never instead of it. --- */
  if (!brief) {
    if (metrics.degradedLabels.length > 0) {
      segments.push(
        `${metrics.sealedChecks} of ${metrics.totalChecks} systems sealed. ${joinWithAnd(
          metrics.degradedLabels,
        )} ${metrics.degradedLabels.length > 1 ? "are" : "is"} not sealed.`,
      );
    } else {
      segments.push(`All ${metrics.totalChecks} systems sealed.`);
    }
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
