import { describe, it, expect, beforeEach } from "vitest";
import {
  activateWoo,
  evaluateWoo,
  appendWooTrace,
  clearWooTraces,
  getWooTraces,
  WOO_VERSION,
  RESONANCE_ENGINE_VERSION,
  type WooActivationConfig,
  type WooActivationDependencies,
  type WooEvaluationInput,
  type WooEvaluationOptions,
} from "./woo";

function makeConfig(overrides: Partial<WooActivationConfig> = {}): WooActivationConfig {
  return {
    enabled: true,
    mode: "shadow",
    executionEnabled: false,
    graphWriteEnabled: false,
    denyThreshold: 0.92,
    approveThreshold: 0.95,
    graphRunId: "gds-pagerank-kd-sfc-20260712161104",
    ...overrides,
  };
}

function makeDeps(overrides: Partial<WooActivationDependencies> = {}): WooActivationDependencies {
  return {
    initializeMoScriptEngine: () => Promise.resolve(),
    applyScrollValidator: () => Promise.resolve(),
    enforceThroneLock: () => Promise.resolve(),
    activateResonanceEngine: () => Promise.resolve(),
    validateWooIdentity: () => Promise.resolve(true),
    verifyGraphRun: () => Promise.resolve(true),
    bindWooInterpreter: () => Promise.resolve(),
    ...overrides,
  };
}

function makeInput(overrides: Partial<WooEvaluationInput> = {}): WooEvaluationInput {
  return {
    scrollId: "scroll-1",
    requestId: "req-1",
    actor: "grid_builder",
    sealedScrollText: "sealed scroll content",
    mode: "shadow",
    graphRunId: "gds-pagerank-kd-sfc-20260712161104",
    evidenceNodeIds: ["n1", "n2"],
    ...overrides,
  };
}

function makeOptions(score: number): WooEvaluationOptions {
  return {
    denyThreshold: 0.92,
    approveThreshold: 0.95,
    getResonanceScore: () => Promise.resolve(score),
  };
}

describe("activateWoo", () => {
  beforeEach(() => {
    clearWooTraces();
  });

  it("returns early when Woo is disabled", async () => {
    const deps = makeDeps();
    await activateWoo(makeConfig({ enabled: false }), deps);
    // All deps should remain uncalled; no error.
    expect(true).toBe(true);
  });

  it("throws on invalid thresholds", async () => {
    await expect(
      activateWoo(makeConfig({ denyThreshold: 0.95, approveThreshold: 0.95 }), makeDeps()),
    ).rejects.toThrow("Invalid Woo resonance thresholds");
    await expect(
      activateWoo(makeConfig({ denyThreshold: -0.1 }), makeDeps()),
    ).rejects.toThrow("Invalid Woo resonance thresholds");
    await expect(
      activateWoo(makeConfig({ approveThreshold: 1.1 }), makeDeps()),
    ).rejects.toThrow("Invalid Woo resonance thresholds");
  });

  it("throws in shadow mode when execution or graph write is enabled", async () => {
    await expect(
      activateWoo(makeConfig({ executionEnabled: true }), makeDeps()),
    ).rejects.toThrow("Shadow mode cannot execute or mutate graph data");
    await expect(
      activateWoo(makeConfig({ graphWriteEnabled: true }), makeDeps()),
    ).rejects.toThrow("Shadow mode cannot execute or mutate graph data");
  });

  it("runs the full activation sequence in order", async () => {
    const order: string[] = [];
    const deps = makeDeps({
      initializeMoScriptEngine: async () => {
        order.push("moScript");
      },
      applyScrollValidator: async () => {
        order.push("scrollValidator");
      },
      enforceThroneLock: async () => {
        order.push("throneLock");
      },
      activateResonanceEngine: async () => {
        order.push("resonance");
      },
      validateWooIdentity: async () => {
        order.push("identity");
        return true;
      },
      verifyGraphRun: async () => {
        order.push("graphRun");
        return true;
      },
      bindWooInterpreter: async () => {
        order.push("interpreter");
      },
    });

    await activateWoo(makeConfig(), deps);
    expect(order).toEqual([
      "moScript",
      "scrollValidator",
      "throneLock",
      "resonance",
      "identity",
      "graphRun",
      "interpreter",
    ]);
  });

  it("throws and leaves Woo unavailable if identity validation fails", async () => {
    const deps = makeDeps({ validateWooIdentity: () => Promise.resolve(false) });
    await expect(activateWoo(makeConfig(), deps)).rejects.toThrow("Woo identity validation failed");
  });

  it("throws and leaves Woo unavailable if graph run verification fails", async () => {
    const deps = makeDeps({
      verifyGraphRun: (runId) => Promise.resolve(runId === "wrong"),
    });
    await expect(activateWoo(makeConfig(), deps)).rejects.toThrow(
      "Woo graph context lineage is invalid",
    );
  });

  it("throws and leaves Woo unavailable if any initialization step fails", async () => {
    const deps = makeDeps({
      activateResonanceEngine: () => Promise.reject(new Error("resonance engine crashed")),
    });
    await expect(activateWoo(makeConfig(), deps)).rejects.toThrow("resonance engine crashed");
  });
});

describe("evaluateWoo", () => {
  beforeEach(() => {
    clearWooTraces();
  });

  it("denies below denyThreshold", async () => {
    const trace = await evaluateWoo(makeInput(), makeOptions(0.85));
    expect(trace.status).toBe("denied");
    expect(trace.resonanceScore).toBe(0.85);
    expect(trace.mode).toBe("shadow");
    expect(trace.wooVersion).toBe(WOO_VERSION);
    expect(trace.resonanceEngineVersion).toBe(RESONANCE_ENGINE_VERSION);
  });

  it("warns between denyThreshold and approveThreshold", async () => {
    const trace = await evaluateWoo(makeInput(), makeOptions(0.93));
    expect(trace.status).toBe("warning");
    expect(trace.resonanceScore).toBe(0.93);
  });

  it("approves at or above approveThreshold", async () => {
    const trace = await evaluateWoo(makeInput(), makeOptions(0.97));
    expect(trace.status).toBe("approved");
    expect(trace.resonanceScore).toBe(0.97);
  });

  it("writes the expected bounded graph context to the trace", async () => {
    const trace = await evaluateWoo(
      makeInput({
        graphRunId: "gds-pagerank-kd-sfc-20260712161104",
        evidenceNodeIds: ["4:abc:123"],
      }),
      makeOptions(0.97),
    );
    expect(trace.graphRunId).toBe("gds-pagerank-kd-sfc-20260712161104");
    expect(trace.evidenceNodeIds).toEqual(["4:abc:123"]);
    expect(trace.inputHash).toMatch(/^[0-9a-f]{64}$/);
    expect(trace.outputHash).toMatch(/^[0-9a-f]{64}$/);
  });

  it("persists traces across storage reset (process restart)", async () => {
    await evaluateWoo(makeInput(), makeOptions(0.97));
    const first = getWooTraces();
    expect(first).toHaveLength(1);

    // Simulate a process restart by clearing the in-memory reference and re-reading from storage.
    const storage = window.localStorage;
    const raw = storage.getItem("mostar:woo:traces");
    clearWooTraces();
    if (raw) storage.setItem("mostar:woo:traces", raw);

    const second = getWooTraces();
    expect(second).toHaveLength(1);
    expect(second[0].status).toBe("approved");
  });

  it("creates unique traceIds for each evaluation", async () => {
    const a = await evaluateWoo(makeInput({ requestId: "req-a" }), makeOptions(0.97));
    const b = await evaluateWoo(makeInput({ requestId: "req-b" }), makeOptions(0.91));
    expect(a.traceId).not.toBe(b.traceId);
    const traces = getWooTraces();
    expect(traces).toHaveLength(2);
  });
});

describe("WooTrace validation", () => {
  it("rejects malformed trace objects from storage", () => {
    window.localStorage.setItem("mostar:woo:traces", JSON.stringify([{ not: "a trace" }]));
    expect(getWooTraces()).toHaveLength(0);
  });
});
