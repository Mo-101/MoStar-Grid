import { describe, expect, it } from "vitest";
import {
  buildOverviewSegments,
  buildSnapshotSegments,
  deriveContinentOptics,
  graphScaleSentence,
  isPartitionSound,
  type SnapshotMetrics,
} from "./gridSnapshot";
import type {
  AfricaSenses,
  AfricaWeatherLocation,
  GraphSemanticAccounting,
} from "@/services/gridApiClient";

function accounting(overrides: Partial<GraphSemanticAccounting> = {}): GraphSemanticAccounting {
  return {
    total_graph_nodes: 12_431,
    knowledge_nodes: 4_120,
    operational_nodes: 5_600,
    audit_nodes: 1_500,
    system_nodes: 900,
    test_nodes: 200,
    unknown_nodes: 111,
    classification_schema_version: "graph_semantic_classification.v1",
    measured_at: new Date().toISOString(),
    ...overrides,
  };
}

function metrics(overrides: Partial<SnapshotMetrics> = {}): SnapshotMetrics {
  return {
    totalNodes: 12_431,
    relationships: 40_220,
    sealedChecks: 8,
    totalChecks: 8,
    verdict: "SEALED",
    degradedLabels: [],
    advisorCount: 11,
    queuePending: 0,
    queueCommittedToday: 0,
    latestFeed: null,
    asOf: new Date().toISOString(),
    ...overrides,
  };
}

function hub(overrides: Partial<AfricaWeatherLocation> = {}): AfricaWeatherLocation {
  return {
    location_id: "nairobi",
    location: "Nairobi",
    country: "Kenya",
    region: "East",
    temperature_c: 20,
    feels_like_c: 20,
    humidity_pct: 61,
    wind_kph: 10.6,
    wind_direction_deg: 30,
    precipitation_mm: null,
    precipitation_probability: null,
    summary: "overcast clouds",
    agreement_score: 0.99,
    provider_count: 2,
    providers_used: ["openweather", "open_meteo"],
    epistemic_state: "CONSENSUS",
    temperature_spread_c: 0.1,
    freshness_seconds: 12,
    observed_at: new Date().toISOString(),
    ...overrides,
  } as AfricaWeatherLocation;
}

function senses(locations: AfricaWeatherLocation[], overrides: Partial<AfricaSenses> = {}) {
  return {
    generated_at: new Date().toISOString(),
    served_at: new Date().toISOString(),
    cache: "MISS",
    scope: "Africa",
    coverage: {
      jurisdictions: 54,
      weather_hubs_observed: locations.length,
      regions_observed: ["North", "West", "East", "Central", "Southern"],
    },
    weather: {
      state: "PARTIAL",
      providers: { meteosource: "MISSING", openweather: "HEALTHY", open_meteo: "HEALTHY" },
      locations,
    },
    health: { state: "PARTIAL", providers: {}, signals: {} },
    sovereignty: { state: "PARTIAL", reports: [] },
    canonical_report: {
      report_id: "africa-senses-x",
      canonical: true,
      generated_at: new Date().toISOString(),
      segments: ["canon one", "canon two"],
      text: "canon one canon two",
      source_digest: "abc123",
      source_refs: ["openweather", "open_meteo"],
    },
    ...overrides,
  } as AfricaSenses;
}

describe("deriveContinentOptics", () => {
  it("counts coverage, live sources and cross-source agreement", () => {
    const optics = deriveContinentOptics(
      senses([
        hub({ location: "Cairo", temperature_c: 34 }),
        hub({ location: "Cape Town", temperature_c: 14, epistemic_state: "DIVERGENT" }),
        hub({ location: "Lagos", provider_count: 0, temperature_c: null }),
      ]),
    );

    expect(optics).not.toBeNull();
    expect(optics!.hubsObserved).toBe(2);
    expect(optics!.hubsConfigured).toBe(3);
    expect(optics!.liveSources).toBe(2);
    expect(optics!.totalSources).toBe(3);
    expect(optics!.consensusHubs).toBe(1);
    expect(optics!.divergentHubs).toBe(1);
    expect(optics!.coldest).toEqual({ location: "Cape Town", temperatureC: 14 });
    expect(optics!.warmest).toEqual({ location: "Cairo", temperatureC: 34 });
  });

  it("only reports rain when it is actually likely", () => {
    const dry = deriveContinentOptics(senses([hub({ precipitation_probability: 20 })]));
    expect(dry!.wettest).toBeNull();

    const wet = deriveContinentOptics(
      senses([hub({ location: "Kinshasa", precipitation_probability: 80 })]),
    );
    expect(wet!.wettest).toEqual({ location: "Kinshasa", probability: 80 });
  });

  it("returns null rather than an empty summary when there is no payload", () => {
    expect(deriveContinentOptics(null)).toBeNull();
  });
});

describe("mind graph semantic accounting", () => {
  it("holds the conservation law T = K + O + A + S + X + U", () => {
    expect(isPartitionSound(accounting())).toBe(true);
    // A double-counted multi-label node inflates the classes past the total.
    expect(isPartitionSound(accounting({ knowledge_nodes: 4_121 }))).toBe(false);
    // A dropped node leaves the partition short.
    expect(isPartitionSound(accounting({ unknown_nodes: 110 }))).toBe(false);
  });

  it("never calls a raw graph-wide count knowledge", () => {
    const line = graphScaleSentence(metrics());
    expect(line).toBe(
      "The governed graph currently contains 12,431 total nodes; knowledge-node composition remains under verification.",
    );
    expect(line).not.toContain("knowledge nodes");
  });

  it("refuses to quote any class when the partition does not reconcile", () => {
    const line = graphScaleSentence(
      metrics({ semanticAccounting: accounting({ knowledge_nodes: 9_999 }) }),
    );
    expect(line).toContain("does not reconcile");
    // The unsound knowledge figure must never reach the listener.
    expect(line).not.toContain("9,999");
  });

  it("speaks knowledge scale only from a sound backend classification", () => {
    const line = graphScaleSentence(metrics({ semanticAccounting: accounting() }));
    expect(line).toContain("12,431 total nodes");
    expect(line).toContain("4,120 are classified as knowledge");
  });

  it("surfaces unclassified material rather than absorbing it into a cleaner class", () => {
    expect(graphScaleSentence(metrics({ semanticAccounting: accounting() }))).toContain(
      "111 nodes remain unclassified",
    );
    const clean = accounting({ unknown_nodes: 0, knowledge_nodes: 4_231 });
    expect(graphScaleSentence(metrics({ semanticAccounting: clean }))).not.toContain(
      "unclassified",
    );
  });

  it("reports honestly when the graph has not reported at all", () => {
    expect(graphScaleSentence(metrics({ totalNodes: null }))).toContain("has not reported in");
  });
});

describe("buildOverviewSegments", () => {
  it("opens with the ruling, not with the node count", () => {
    const [headline] = buildOverviewSegments(metrics(), null);
    expect(headline.startsWith("Grid overview. All critical systems sealed.")).toBe(true);
    // Scale is evidence and must come after the verdict in the same breath.
    expect(headline).toContain("8 of 8 systems sealed");
    expect(headline.indexOf("sealed")).toBeLessThan(headline.indexOf("12,431"));
  });

  it("qualifies node scale in the headline instead of implying knowledge", () => {
    const [headline] = buildOverviewSegments(metrics(), null);
    expect(headline).toContain("knowledge-node composition remains under verification");
    expect(headline).not.toMatch(/12,431 knowledge/);
  });

  it("summarises continent optics before any per-hub detail", () => {
    const optics = deriveContinentOptics(
      senses([
        hub({ location: "Cairo", temperature_c: 34 }),
        hub({ location: "Cape Town", temperature_c: 14 }),
      ]),
    );
    const segments = buildOverviewSegments(metrics(), optics);
    const optic = segments.find((s) => s.startsWith("Continent optics."));

    expect(optic).toBeDefined();
    expect(optic).toContain("2 of 2 observation hubs reporting across 5 regions");
    expect(optic).toContain("2 of 3 weather sources live");
    expect(optic).toContain("Temperatures span 14 degrees at Cape Town to 34 at Cairo");
    expect(optic).toContain("2 in cross-source consensus");
  });

  it("names every exception explicitly in the attention segment", () => {
    const optics = deriveContinentOptics(
      senses([
        hub({ location: "Cairo" }),
        hub({ location: "Cape Town", epistemic_state: "DIVERGENT" }),
        hub({ location: "Lagos", provider_count: 0, temperature_c: null }),
      ]),
    );
    const segments = buildOverviewSegments(
      metrics({
        verdict: "DEGRADED",
        sealedChecks: 6,
        degradedLabels: ["DCX Trinity", "Woo Oracle"],
      }),
      optics,
    );
    const attention = segments.find((s) => s.startsWith("Requiring attention."));

    expect(attention).toBeDefined();
    expect(attention).toContain("DCX Trinity and Woo Oracle are not sealed");
    expect(attention).toContain("1 hub reports sources that disagree");
    expect(attention).toContain("1 hub has no current source");
    expect(attention).toContain("health reporting is partial");
    expect(attention).toContain("sovereignty reporting is partial");
  });

  it("states plainly when nothing is flagged rather than staying silent", () => {
    const segments = buildOverviewSegments(metrics(), null);
    expect(segments.at(-1)).toBe("Nothing is currently flagged for attention. Detail follows.");
  });

  it("omits the grid headline entirely for a continent-only briefing", () => {
    const optics = deriveContinentOptics(senses([hub()]));
    const segments = buildOverviewSegments(null, optics);
    expect(segments.some((s) => s.startsWith("Grid overview."))).toBe(false);
    expect(segments[0].startsWith("Continent optics.")).toBe(true);
  });

  it("does not invent a temperature span from a single measured hub", () => {
    const optics = deriveContinentOptics(senses([hub({ location: "Nairobi" })]));
    const optic = buildOverviewSegments(null, optics).find((s) =>
      s.startsWith("Continent optics."),
    );
    expect(optic).not.toContain("Temperatures span");
  });
});

describe("briefing composition", () => {
  it("never repeats what the overview already stated", () => {
    const detail = buildSnapshotSegments(metrics(), null, { precededByOverview: true });
    const spokenText = detail.join(" ");

    expect(spokenText).not.toContain("Grid pulse check.");
    // The overview already carried these; hearing them twice is the flaw.
    expect(spokenText).not.toContain("12,431 nodes");
    expect(spokenText).not.toContain("council advisors registered");
    expect(spokenText).not.toContain("systems sealed");
    // What the overview could not carry must survive.
    expect(spokenText).toContain("pending review");
  });

  it("still reports graph movement after an overview, because change is news", () => {
    const now = metrics({ totalNodes: 12_500 });
    const before = metrics({ totalNodes: 12_431 });
    const detail = buildSnapshotSegments(now, before, { precededByOverview: true });
    expect(detail.some((s) => s.includes("69 new nodes since the last check"))).toBe(true);
  });

  it("still speaks exceptions after an overview", () => {
    const detail = buildSnapshotSegments(metrics({ advisorCount: 0, totalNodes: null }), null, {
      precededByOverview: true,
    });
    expect(detail.some((s) => s.includes("council channel is unreachable"))).toBe(true);
    expect(detail.some((s) => s.includes("mind graph has not reported in"))).toBe(true);
  });

  it("still leads with the verdict when used without an overview", () => {
    const detail = buildSnapshotSegments(metrics());
    expect(detail[0]).toBe("Grid pulse check. All critical systems sealed.");
  });
});
