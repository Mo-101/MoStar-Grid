import { describe, expect, it } from "vitest";
import { deriveGridReadiness } from "./grid-status-schema";
import { mintSealReceipt } from "./seal-receipt-guard";

describe("Seal receipt authority guard", () => {
  it("HP-9 withholds a receipt when all six gates pass but HumanAuthorization is absent", () => {
    const readiness = deriveGridReadiness({
      MODEL_BINDING: "SEALED",
      CYPHER_GUARD: "SEALED",
      PROVENANCE_FILTER: "SEALED",
      ATTESTATION_GUARD: "SEALED",
      INVOCATION_SURFACE_GUARD: "SEALED",
      HOSTILE_PATH_TEST: "PASS",
    });
    expect(readiness.GRID_MIND_READY).toBe(true);
    expect(
      mintSealReceipt({
        readiness,
        worktreeCommit: "immutable-commit",
        humanAuthorization: undefined,
      }),
    ).toEqual({ disposition: "WITHHELD", reason: "NO_HUMAN_AUTHORIZATION" });
  });
});
