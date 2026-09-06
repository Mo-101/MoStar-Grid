import { describe, expect, it, vi } from "vitest";
import { CanonicalQueryRegistry, CypherGuard } from "./cypher-guard";
import {
  CONSTITUTION_CHAIN_CYPHER,
  assertConstitutionComposition,
  registerConstitutionChainQuery,
  verifyConstitutionComposition,
} from "./constitution-composition";

const HASH = "a".repeat(64);
const row = {
  constitution_hash: HASH,
  provenance_hash: HASH,
  attestation_hash: HASH,
  attestation_subject_digest: HASH,
};

describe("constitution hash composition", () => {
  it("uses one parameterized mandatory chain with exact hash equality", () => {
    expect(CONSTITUTION_CHAIN_CYPHER).toContain("$constitution_hash");
    expect(CONSTITUTION_CHAIN_CYPHER).not.toContain("OPTIONAL MATCH");
    expect(CONSTITUTION_CHAIN_CYPHER).toContain("[:ORIGINATES_FROM]");
    expect(CONSTITUTION_CHAIN_CYPHER).toContain("[:ATTESTED_BY]");
    expect(CONSTITUTION_CHAIN_CYPHER).not.toContain("HAS_PROVENANCE");
    expect(CONSTITUTION_CHAIN_CYPHER).not.toContain("HAS_ATTESTATION");
    expect(CONSTITUTION_CHAIN_CYPHER).toContain("p.constitution_hash = c.constitution_hash");
    expect(CONSTITUTION_CHAIN_CYPHER).toContain("a.constitution_hash = c.constitution_hash");
  });

  it("verifies the exact canonical constitution, provenance, attestation and subject digest", async () => {
    const registry = new CanonicalQueryRegistry();
    registerConstitutionChainQuery(registry);
    registry.seal();
    const runRead = vi.fn(async () => [row]);
    const result = await verifyConstitutionComposition({
      cypherGuard: new CypherGuard(registry, { runRead }),
      canonicalConstitutionDigest: HASH,
    });
    expect(result).toEqual(row);
    expect(runRead).toHaveBeenCalledWith(
      CONSTITUTION_CHAIN_CYPHER,
      { constitution_hash: HASH },
      expect.anything(),
    );
  });

  it.each([
    ["missing", [{ ...row, provenance_hash: "" }], "CONSTITUTION_CHAIN_HASH_MISSING"],
    [
      "provenance mismatch",
      [{ ...row, provenance_hash: "b".repeat(64) }],
      "CONSTITUTION_CHAIN_HASH_MISMATCH",
    ],
    [
      "attestation mismatch",
      [{ ...row, attestation_hash: "b".repeat(64) }],
      "CONSTITUTION_CHAIN_HASH_MISMATCH",
    ],
    [
      "subject mismatch",
      [{ ...row, attestation_subject_digest: "b".repeat(64) }],
      "CONSTITUTION_CHAIN_HASH_MISMATCH",
    ],
    ["multiple chains", [row, row], "CONSTITUTION_CHAIN_CARDINALITY_VIOLATION"],
    ["no chain", [], "CONSTITUTION_CHAIN_CARDINALITY_VIOLATION"],
  ])("fails closed for %s", (_, rows, error) => {
    expect(() =>
      assertConstitutionComposition({ canonical_constitution_digest: HASH, rows }),
    ).toThrow(error);
  });
});
