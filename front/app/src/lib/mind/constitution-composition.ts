import { type CanonicalQueryRegistry, type CypherGuard, type QueryParams } from "./cypher-guard";

export const CONSTITUTION_CHAIN_QUERY_KEY = "mind.constitution-chain.v1";
export const CONSTITUTION_CHAIN_CYPHER = `
MATCH (c:Constitution {constitution_hash: $constitution_hash})
MATCH (c)-[:ORIGINATES_FROM]->(p:Provenance)
MATCH (p)-[:ATTESTED_BY]->(a:Attestation)
WHERE p.constitution_hash = c.constitution_hash
  AND a.constitution_hash = c.constitution_hash
RETURN c.constitution_hash AS constitution_hash,
       p.constitution_hash AS provenance_hash,
       a.constitution_hash AS attestation_hash,
       a.subject_digest AS attestation_subject_digest
LIMIT 2
`.trim();

export interface ConstitutionChainRow {
  constitution_hash: string;
  provenance_hash: string;
  attestation_hash: string;
  attestation_subject_digest: string;
}

export function registerConstitutionChainQuery(registry: CanonicalQueryRegistry): void {
  registry.register<QueryParams, ConstitutionChainRow>({
    key: CONSTITUTION_CHAIN_QUERY_KEY,
    cypher: CONSTITUTION_CHAIN_CYPHER,
    timeoutMs: 2_000,
    maxRows: 2,
    allowedOrigins: ["mostar-grid-builder"],
    validateParams(value: unknown): asserts value is QueryParams {
      const hash = (value as { constitution_hash?: unknown } | null)?.constitution_hash;
      if (typeof hash !== "string" || !/^[a-f0-9]{64}$/.test(hash))
        throw new Error("INVALID_CONSTITUTION_HASH_PARAMETER");
    },
    validateRows(value: unknown): asserts value is readonly ConstitutionChainRow[] {
      if (!Array.isArray(value)) throw new Error("INVALID_CONSTITUTION_CHAIN_ROWS");
    },
  });
}

export function assertConstitutionComposition(input: {
  canonical_constitution_digest: string;
  rows: readonly ConstitutionChainRow[];
}): ConstitutionChainRow {
  if (input.rows.length !== 1) throw new Error("CONSTITUTION_CHAIN_CARDINALITY_VIOLATION");
  const [row] = input.rows;
  const hashes = [
    row.constitution_hash,
    row.provenance_hash,
    row.attestation_hash,
    row.attestation_subject_digest,
  ];
  if (hashes.some((hash) => !hash)) throw new Error("CONSTITUTION_CHAIN_HASH_MISSING");
  if (hashes.some((hash) => hash !== input.canonical_constitution_digest))
    throw new Error("CONSTITUTION_CHAIN_HASH_MISMATCH");
  return Object.freeze(row);
}

export async function verifyConstitutionComposition(input: {
  cypherGuard: CypherGuard;
  canonicalConstitutionDigest: string;
}): Promise<ConstitutionChainRow> {
  const rows = await input.cypherGuard.retrieve<ConstitutionChainRow>({
    query_key: CONSTITUTION_CHAIN_QUERY_KEY,
    params: { constitution_hash: input.canonicalConstitutionDigest },
    requestOrigin: "mostar-grid-builder",
  });
  return assertConstitutionComposition({
    canonical_constitution_digest: input.canonicalConstitutionDigest,
    rows,
  });
}
