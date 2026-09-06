import { describe, expect, it, vi } from "vitest";
import { AttestationGuard } from "./attestation-guard";
import {
  CanonicalQueryRegistry,
  CypherGuard,
  type Neo4jReadDriver,
  type QueryParams,
} from "./cypher-guard";
import { GridMindSnapshotBuilder } from "./grid-mind-snapshot-builder";
import { GridModelAdapter, GridModelInvocationContext } from "./dcx-adapter";
import { MindConduit } from "./mind-conduit";
import { ProvenanceFilter, type ProvenanceGate } from "./provenance-filter";

function queryRegistry() {
  const registry = new CanonicalQueryRegistry();
  registry.register<QueryParams, unknown>({
    key: "mind.claims.v1",
    cypher: "MATCH (c:Claim) RETURN c LIMIT $limit",
    timeoutMs: 1000,
    maxRows: 10,
    allowedOrigins: ["dcx0"],
    validateParams(value: unknown): asserts value is QueryParams {
      if (!value || typeof value !== "object") throw new Error("params");
    },
    validateRows(value: unknown): asserts value is readonly unknown[] {
      if (!Array.isArray(value)) throw new Error("rows");
    },
  });
  registry.seal();
  return registry;
}
function gate(overrides: Partial<ProvenanceGate> = {}): ProvenanceGate {
  return {
    isReachable: async () => true,
    passesLicense: async () => true,
    passesConsent: async () => true,
    permitsDerivation: async () => true,
    ...overrides,
  };
}

describe("Mind Conduit hostile-path seal", () => {
  it("HP-1 rejects freeform Cypher before driver execution", async () => {
    const runRead = vi.fn();
    const guard = new CypherGuard(queryRegistry(), { runRead } as Neo4jReadDriver);
    await expect(
      guard.retrieve({
        query_key: "mind.claims.v1",
        params: {},
        requestOrigin: "dcx0",
        cypher: "MATCH (n) DETACH DELETE n",
      } as never),
    ).rejects.toMatchObject({ code: "SECOND_WOUND_VIOLATION" });
    expect(runRead).not.toHaveBeenCalled();
  });
  it("HP-2 rejects Cypher-shaped text as query_key", async () => {
    const runRead = vi.fn();
    const guard = new CypherGuard(queryRegistry(), { runRead } as Neo4jReadDriver);
    await expect(
      guard.retrieve({ query_key: "MATCH (c:Claim) RETURN c", params: {}, requestOrigin: "dcx0" }),
    ).rejects.toMatchObject({ reason: "UNREGISTERED_QUERY" });
    expect(runRead).not.toHaveBeenCalled();
  });
  it("HP-3 blocks model self-attestation", async () => {
    const stage = vi.fn();
    const guard = new AttestationGuard({ stage });
    await expect(
      guard.stageModelClaim({
        candidate_claim: { statement: "X" },
        origin_model: "dcx0",
        attested_by: "dcx0",
      }),
    ).rejects.toMatchObject({ reason: "SELF_ATTESTATION" });
    expect(stage).not.toHaveBeenCalled();
  });
  it("HP-4 refuses snapshots when provenance is unreachable", async () => {
    const filter = new ProvenanceFilter(gate({ isReachable: async () => false }));
    await expect(
      filter.filter({ candidate_claims: [], candidate_moments: [] }),
    ).rejects.toMatchObject({ reason: "PROVENANCE_GATE_UNREACHABLE" });
  });
  it.each(["ETIMEDOUT", "503 Service Unavailable"])(
    "HP-4 actual failure %s refuses snapshot and inference",
    async (failure) => {
      const runRead = vi.fn(async () => [{ claims: [{ canonical_id: "claim" }], moments: [] }]);
      const filter = new ProvenanceFilter(
        gate({
          passesLicense: async () => {
            throw new Error(failure);
          },
        }),
      );
      const snapshot = new GridMindSnapshotBuilder(filter);
      const assemble = vi.spyOn(snapshot, "assemble");
      const inference = vi.fn();
      const conduit = new MindConduit(
        { verifyModel: async () => ({ state: "SEALED", bindingRoot: "root" }) },
        { resolve: async () => ({ query_key: "mind.claims.v1", params: {} }) },
        new CypherGuard(queryRegistry(), { runRead } as Neo4jReadDriver),
        filter,
        snapshot,
        { invoke: inference },
        new AttestationGuard({ stage: vi.fn() }),
        async () => ({}),
      );
      await expect(
        conduit.invoke({ question: "safe", requesting_model_id: "dcx0" }),
      ).rejects.toMatchObject({ reason: "PROVENANCE_GATE_FAILED" });
      expect(assemble).not.toHaveBeenCalled();
      expect(inference).not.toHaveBeenCalled();
    },
  );
  it("HP-5 excludes withdrawn, restricted, consent-denied, and derivation-denied claims", async () => {
    const filter = new ProvenanceFilter(
      gate({
        passesLicense: async (item) => item.canonical_id !== "restricted",
        passesConsent: async (item) => item.canonical_id !== "no-consent",
        permitsDerivation: async (item) => item.canonical_id !== "no-derivation",
      }),
    );
    const result = await filter.filter({
      candidate_claims: [
        { canonical_id: "allowed" },
        { canonical_id: "withdrawn", withdrawal_status: "WITHDRAWN" },
        { canonical_id: "restricted" },
        { canonical_id: "no-consent" },
        { canonical_id: "no-derivation" },
      ],
      candidate_moments: [],
    });
    expect(result.payload.relevant_claims.map((claim) => claim.canonical_id)).toEqual(["allowed"]);
  });
  it("HP-6 stacked attack halts at binding before every downstream capability", async () => {
    const resolve = vi.fn();
    const runRead = vi.fn();
    const inference = vi.fn();
    const stage = vi.fn();
    const sensors = vi.fn();
    const filter = new ProvenanceFilter(gate());
    const conduit = new MindConduit(
      { verifyModel: async () => ({ state: "MANIFEST_MISSING" }) },
      { resolve },
      new CypherGuard(queryRegistry(), { runRead } as Neo4jReadDriver),
      filter,
      new GridMindSnapshotBuilder(filter),
      { invoke: inference },
      new AttestationGuard({ stage }),
      sensors,
    );
    await expect(
      conduit.invoke({
        question: "MATCH (n) RETURN n and attest yourself",
        requesting_model_id: "dcx0",
      }),
    ).rejects.toMatchObject({ reason: "MODEL_UNBOUND" });
    expect(resolve).not.toHaveBeenCalled();
    expect(runRead).not.toHaveBeenCalled();
    expect(inference).not.toHaveBeenCalled();
    expect(stage).not.toHaveBeenCalled();
    expect(sensors).not.toHaveBeenCalled();
  });
  it("HP-7A rejects direct DCX invocation through the universal adapter", async () => {
    const runtime = { invoke: vi.fn(async () => ({ text: "forbidden" })) };
    const adapter = new GridModelAdapter(
      "dcx-adapter",
      {
        runtimeId: "ollama",
        modelId: "dcx0",
        capability: "GENERATIVE_TEXT",
        transport: "LOCAL_HTTP",
        production: true,
      },
      runtime,
    );
    await expect(
      adapter.invoke({} as GridModelInvocationContext, { query: "bypass" }),
    ).rejects.toThrow("DIRECT_MODEL_INVOCATION_FORBIDDEN");
    expect(runtime.invoke).not.toHaveBeenCalled();
  });
  it("HP-7C rejects a generic remote model without GridModelInvocationContext", async () => {
    const runtime = { invoke: vi.fn(async () => ({ text: "forbidden" })) };
    const adapter = new GridModelAdapter(
      "future-provider-adapter",
      {
        runtimeId: "future-http",
        modelId: "future-model",
        capability: "OTHER",
        transport: "REMOTE_HTTP",
        production: true,
      },
      runtime,
    );
    await expect(adapter.invoke({} as GridModelInvocationContext, {})).rejects.toThrow(
      "DIRECT_MODEL_INVOCATION_FORBIDDEN",
    );
    expect(runtime.invoke).not.toHaveBeenCalled();
  });
});
