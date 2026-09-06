export interface MemoryClaim {
  readonly canonical_id: string;
  readonly withdrawal_status?: string;
  readonly contested?: boolean;
  readonly status?: string;
  readonly [key: string]: unknown;
}
export interface MemoryMoment {
  readonly event_id?: string;
  readonly canonical_id?: string;
  readonly [key: string]: unknown;
}
export interface ProvenanceGate {
  isReachable(): Promise<boolean>;
  passesLicense(candidate: MemoryClaim | MemoryMoment): Promise<boolean>;
  passesConsent(candidate: MemoryClaim): Promise<boolean>;
  permitsDerivation(
    candidate: MemoryClaim | MemoryMoment,
    purpose: "INFERENCE_CONTEXT",
  ): Promise<boolean>;
}
export class ProvenanceGateViolation extends Error {
  readonly code = "PROVENANCE_GATE_VIOLATION";
  constructor(
    readonly reason:
      | "PROVENANCE_GATE_UNREACHABLE"
      | "PROVENANCE_GATE_FAILED"
      | "UNSEALED_MEMORY_ENVELOPE",
    readonly detail: string,
  ) {
    super(`${reason}: ${detail}`);
    this.name = "ProvenanceGateViolation";
  }
}
export interface ProvenanceFilteredPayload {
  readonly relevant_claims: readonly MemoryClaim[];
  readonly relevant_moments: readonly MemoryMoment[];
  readonly contested_claims: readonly MemoryClaim[];
  readonly provenance_filtered: true;
}
export class ProvenanceFilteredMemory {
  private constructor(readonly payload: ProvenanceFilteredPayload) {}
  static create(token: symbol, expected: symbol, payload: ProvenanceFilteredPayload) {
    if (token !== expected)
      throw new ProvenanceGateViolation(
        "UNSEALED_MEMORY_ENVELOPE",
        "Only ProvenanceFilter may issue memory.",
      );
    return Object.freeze(new ProvenanceFilteredMemory(Object.freeze(payload)));
  }
}
export class ProvenanceFilter {
  readonly #sealToken = Symbol("provenance-filter-seal");
  readonly #issued = new WeakSet<ProvenanceFilteredMemory>();
  constructor(private readonly gate: ProvenanceGate) {}
  async filter(input: {
    candidate_claims: readonly MemoryClaim[];
    candidate_moments: readonly MemoryMoment[];
  }): Promise<ProvenanceFilteredMemory> {
    let reachable: boolean;
    try {
      reachable = await this.gate.isReachable();
    } catch (error) {
      throw new ProvenanceGateViolation(
        "PROVENANCE_GATE_UNREACHABLE",
        error instanceof Error ? error.message : "Reachability failed.",
      );
    }
    if (!reachable)
      throw new ProvenanceGateViolation(
        "PROVENANCE_GATE_UNREACHABLE",
        "Snapshot assembly refused.",
      );
    try {
      const claims: MemoryClaim[] = [];
      for (const claim of input.candidate_claims) {
        if (claim.withdrawal_status === "WITHDRAWN") continue;
        if (!(await this.gate.passesLicense(claim))) continue;
        if (!(await this.gate.passesConsent(claim))) continue;
        if (!(await this.gate.permitsDerivation(claim, "INFERENCE_CONTEXT"))) continue;
        claims.push(claim);
      }
      const moments: MemoryMoment[] = [];
      for (const moment of input.candidate_moments)
        if (
          (await this.gate.passesLicense(moment)) &&
          (await this.gate.permitsDerivation(moment, "INFERENCE_CONTEXT"))
        )
          moments.push(moment);
      const payload = {
        relevant_claims: Object.freeze(claims),
        relevant_moments: Object.freeze(moments),
        contested_claims: Object.freeze(
          claims.filter(
            (claim) => claim.contested === true || claim.status === "ACCEPTED_WITH_DISPUTE",
          ),
        ),
        provenance_filtered: true as const,
      };
      const envelope = ProvenanceFilteredMemory.create(this.#sealToken, this.#sealToken, payload);
      this.#issued.add(envelope);
      return envelope;
    } catch (error) {
      if (error instanceof ProvenanceGateViolation) throw error;
      throw new ProvenanceGateViolation(
        "PROVENANCE_GATE_FAILED",
        error instanceof Error ? error.message : "Evaluation failed.",
      );
    }
  }
  assertIssued(memory: ProvenanceFilteredMemory): void {
    if (!this.#issued.has(memory))
      throw new ProvenanceGateViolation(
        "UNSEALED_MEMORY_ENVELOPE",
        "SnapshotBuilder received unissued memory.",
      );
  }
}
