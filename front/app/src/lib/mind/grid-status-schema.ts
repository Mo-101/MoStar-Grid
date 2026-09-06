export type EvidenceSealState = "SEALED" | "UNVERIFIED" | "UNRESOLVED" | "FAILED";
export type ModelBindingEvidenceState =
  | EvidenceSealState
  | "CONSTITUTION_DRIFT"
  | "MANIFEST_REGEN_REQUIRED";
export type HostilePathEvidenceState = "PASS" | "UNVERIFIED" | "UNRESOLVED" | "FAIL";

export interface GridSealStatus {
  MODEL_BINDING: ModelBindingEvidenceState;
  CYPHER_GUARD: EvidenceSealState;
  PROVENANCE_FILTER: EvidenceSealState;
  ATTESTATION_GUARD: EvidenceSealState;
  INVOCATION_SURFACE_GUARD: EvidenceSealState;
  HOSTILE_PATH_TEST: HostilePathEvidenceState;
}

export interface GridReadiness extends GridSealStatus {
  MIND_CONDUIT: "SEALED" | "PARTIAL";
  GRID_MIND_READY: boolean;
  blockers: readonly string[];
}

export function deriveGridReadiness(evidence: GridSealStatus): GridReadiness {
  const blockers = Object.entries(evidence)
    .filter(([gate, state]) =>
      gate === "HOSTILE_PATH_TEST" ? state !== "PASS" : state !== "SEALED",
    )
    .map(([gate]) => gate);
  const fullySealed = blockers.length === 0;
  return Object.freeze({
    ...evidence,
    MIND_CONDUIT: fullySealed ? "SEALED" : "PARTIAL",
    GRID_MIND_READY: fullySealed,
    blockers: Object.freeze(blockers),
  });
}
