import { AttestationGuard, type ModelClaimCandidate } from "./attestation-guard";
import { CypherGuard, type QueryParams } from "./cypher-guard";
import { GridModelInvocationContext } from "./dcx-adapter";
import { GridMindSnapshotBuilder, type GridMindSnapshot } from "./grid-mind-snapshot-builder";
import { ProvenanceFilter, type MemoryClaim, type MemoryMoment } from "./provenance-filter";

export interface MindModelBindingGuard {
  verifyModel(modelId: string): Promise<{ state: string; bindingRoot?: string }>;
}
export interface IntentRouter {
  resolve(question: string): Promise<{ query_key: string; params: QueryParams }>;
}
export interface RetrievalProjection {
  readonly claims: readonly MemoryClaim[];
  readonly moments: readonly MemoryMoment[];
}
export interface ModelInferenceResult {
  readonly answer: { readonly text: string; readonly [key: string]: unknown };
  readonly proposedClaims?: readonly ModelClaimCandidate[];
  readonly proposedActions?: readonly { readonly type: string; readonly payload?: unknown }[];
}
export interface ModelInferenceCore {
  invoke(
    ctx: GridModelInvocationContext,
    input: {
      modelId: string;
      question: string;
      snapshot: GridMindSnapshot;
    },
  ): Promise<ModelInferenceResult>;
}
export class MindConduitViolation extends Error {
  readonly code = "MIND_CONDUIT_VIOLATION";
  constructor(
    readonly reason: "MODEL_UNBOUND" | "INFERENCE_NOT_PERMITTED",
    readonly detail: string,
  ) {
    super(`${reason}: ${detail}`);
    this.name = "MindConduitViolation";
  }
}

export class MindConduit {
  constructor(
    private readonly bindingGuard: MindModelBindingGuard,
    private readonly intentRouter: IntentRouter,
    private readonly cypherGuard: CypherGuard,
    private readonly provenanceFilter: ProvenanceFilter,
    private readonly snapshotBuilder: GridMindSnapshotBuilder,
    private readonly inference: ModelInferenceCore,
    private readonly attestationGuard: AttestationGuard,
    private readonly readCurrentSensorState: () => Promise<unknown>,
  ) {}
  async invoke(input: {
    question: string;
    requesting_model_id: string;
  }): Promise<ModelInferenceResult["answer"]> {
    const binding = await this.bindingGuard.verifyModel(input.requesting_model_id);
    if (binding.state !== "SEALED" || !binding.bindingRoot)
      throw new MindConduitViolation("MODEL_UNBOUND", `Model binding state=${binding.state}.`);
    const intent = await this.intentRouter.resolve(input.question);
    const raw = await this.cypherGuard.retrieve<RetrievalProjection>({
      query_key: intent.query_key,
      params: intent.params,
      requestOrigin: input.requesting_model_id,
    });
    const projection = raw[0] ?? { claims: [], moments: [] };
    const filtered = await this.provenanceFilter.filter({
      candidate_claims: projection.claims ?? [],
      candidate_moments: projection.moments ?? [],
    });
    const snapshot = await this.snapshotBuilder.assemble({
      grid_id: "mostar-grid",
      requesting_model_id: input.requesting_model_id,
      binding_root: binding.bindingRoot,
      memory: filtered,
      senses: await this.readCurrentSensorState(),
    });
    const result = await this.inference.invoke(
      GridModelInvocationContext.issueFromMindConduit({
        modelId: input.requesting_model_id,
        bindingRoot: binding.bindingRoot,
        snapshotDigest: snapshot.snapshot_digest,
      }),
      {
        modelId: input.requesting_model_id,
        question: input.question,
        snapshot,
      },
    );
    for (const claim of result.proposedClaims ?? [])
      await this.attestationGuard.stageModelClaim({
        candidate_claim: claim,
        origin_model: input.requesting_model_id,
        attested_by: null,
      });
    return result.answer;
  }
}
