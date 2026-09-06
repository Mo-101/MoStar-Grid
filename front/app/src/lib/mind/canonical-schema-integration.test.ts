import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { deriveGridReadiness } from "./grid-status-schema";
import {
  assertLedgerIntegrity,
  deriveInvocationSurfaceGuard,
  type InvocationSurfaceLedger,
} from "./invocation-surface-ledger-schema";
import { deriveMoScriptRegistryHealth, type MoScriptRegistry } from "./moscripts-schema";

const repositoryRoot = resolve(process.cwd(), "../..");

describe("canonical schema integration", () => {
  it("derives INVOCATION_SURFACE_GUARD from the durable ledger", () => {
    const ledger = JSON.parse(
      readFileSync(
        resolve(repositoryRoot, "core/ops/status/INVOCATION_SURFACE_LEDGER.json"),
        "utf8",
      ),
    ) as InvocationSurfaceLedger;
    assertLedgerIntegrity(ledger);
    expect(deriveInvocationSurfaceGuard(ledger)).toBe("SEALED");
  });

  it("derives Grid readiness from the canonical six-gate schema", () => {
    expect(
      deriveGridReadiness({
        MODEL_BINDING: "CONSTITUTION_DRIFT",
        CYPHER_GUARD: "UNVERIFIED",
        PROVENANCE_FILTER: "UNVERIFIED",
        ATTESTATION_GUARD: "UNVERIFIED",
        INVOCATION_SURFACE_GUARD: "SEALED",
        HOSTILE_PATH_TEST: "UNVERIFIED",
      }),
    ).toMatchObject({ MIND_CONDUIT: "PARTIAL", GRID_MIND_READY: false });
  });

  it("derives MoScript registry health from the canonical mapping", () => {
    const registry = JSON.parse(
      readFileSync(
        resolve(repositoryRoot, "core/ops/status/MOSCRIPT_RUNTIME_IMPLEMENTATION_MAP.json"),
        "utf8",
      ),
    ) as MoScriptRegistry;
    expect(deriveMoScriptRegistryHealth(registry)).toBe("SEALED");
  });
});
