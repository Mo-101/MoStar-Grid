export interface ModelClaimCandidate {
  readonly statement: unknown;
  readonly metadata?: Readonly<Record<string, unknown>>;
}
export interface StagedModelClaim extends ModelClaimCandidate {
  readonly origin_model: string;
  readonly attested_by: null;
  readonly is_model_generated: true;
  readonly corroboration_status: "UNCORROBORATED_MODEL_OUTPUT";
  readonly canonical_eligible: false;
}
export class ProvenanceLawViolation extends Error {
  readonly code = "PROVENANCE_LAW_VIOLATION";
  constructor(
    readonly reason:
      | "SELF_ATTESTATION"
      | "MODEL_CANONICAL_WRITE_FORBIDDEN"
      | "INVALID_MODEL_ORIGIN",
    readonly detail: string,
  ) {
    super(`${reason}: ${detail}`);
    this.name = "ProvenanceLawViolation";
  }
}
export interface ModelClaimStageSink {
  stage(candidate: StagedModelClaim): Promise<void>;
}
export class AttestationGuard {
  constructor(private readonly sink: ModelClaimStageSink) {}
  async stageModelClaim(input: {
    candidate_claim: ModelClaimCandidate;
    origin_model: string;
    attested_by?: string | null;
  }): Promise<StagedModelClaim> {
    if (!input.origin_model.trim())
      throw new ProvenanceLawViolation("INVALID_MODEL_ORIGIN", "origin_model is required.");
    if (input.attested_by != null) {
      if (input.attested_by === input.origin_model)
        throw new ProvenanceLawViolation(
          "SELF_ATTESTATION",
          "attested_by must never equal origin_model.",
        );
      throw new ProvenanceLawViolation(
        "MODEL_CANONICAL_WRITE_FORBIDDEN",
        "Independent attestation must use the testimony/adjudication path.",
      );
    }
    const staged = Object.freeze({
      ...input.candidate_claim,
      origin_model: input.origin_model,
      attested_by: null,
      is_model_generated: true,
      corroboration_status: "UNCORROBORATED_MODEL_OUTPUT",
      canonical_eligible: false,
    } as const);
    await this.sink.stage(staged);
    return staged;
  }
}
