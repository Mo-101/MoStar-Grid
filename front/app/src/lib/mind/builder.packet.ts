import {
  type GridBindingState,
  type ModelBindingGuard,
  type ModelManifestRegistry,
} from "./model-binding-guard";
import {
  deriveMoScriptRegistryHealth,
  MOSCRIPTS_TAG,
  type MoScriptRegistry,
} from "./moscripts-schema";
import {
  deriveGridReadiness,
  type EvidenceSealState,
  type GridReadiness,
  type HostilePathEvidenceState,
  type ModelBindingEvidenceState,
} from "./grid-status-schema";
import {
  deriveInvocationSurfaceGuard,
  type InvocationSurfaceLedger,
} from "./invocation-surface-ledger-schema";
import { verifyConstitutionComposition } from "./constitution-composition";
import type { CypherGuard } from "./cypher-guard";

export { deriveGridReadiness } from "./grid-status-schema";
export type ConstitutionalBindingState = ModelBindingEvidenceState;
export type MindConduitSealStatus = GridReadiness;
export type MindConduitStatus = GridReadiness;

export type BuilderComponentState =
  | "PENDING"
  | "INITIALIZING"
  | "READY"
  | "DEGRADED"
  | "BLOCKED"
  | "FAILED";
export interface BuilderComponentStatus {
  id: string;
  state: BuilderComponentState;
  critical: boolean;
  detail?: string;
}
export type SealState = EvidenceSealState;
export type HostilePathState = HostilePathEvidenceState;
export interface MindConduitSealReceipt {
  schema: "mostar.mind-conduit-seal.v1";
  commit: string;
  constitution_hash: string;
  source_digest: string;
  invocation_surface_digest: string;
  test_suite_digest: string;
  tests: {
    "HP-1": "PASS";
    "HP-2": "PASS";
    "HP-3": "PASS";
    "HP-4-timeout": "PASS";
    "HP-4-5xx": "PASS";
    "HP-5": "PASS";
    "HP-6": "PASS";
    "HP-7A": "PASS";
    "HP-7B": "PASS";
    "HP-7C": "PASS";
    "HP-7D": "PASS";
    "HP-8": "PASS";
  };
  invocation_surface_audit: {
    scanned: boolean;
    direct_runtime_call_sites: number;
    unauthorized_call_sites: number;
    production_entrypoints: string[];
  };
  adapter_contract: {
    backend_calls_conduit_only: boolean;
    direct_ollama_forbidden: boolean;
    direct_dcx_runtime_forbidden: boolean;
    all_model_inference_conduit_only: boolean;
    prohibited_name_scoping: true;
    bypass_flags_forbidden: boolean;
  };
  created_at: string;
}
export interface GridBuilderStatus {
  buildId: string;
  state: "INITIALIZING" | "READY" | "DEGRADED" | "FAILED";
  tags: readonly string[];
  components: Record<string, BuilderComponentStatus>;
  mindBinding: {
    state: "UNINITIALIZED" | "SEALED" | "DEGRADED" | "DETACHED";
    bindingRoot?: string;
    models: Record<string, { process: "ONLINE" | "OFFLINE"; binding: GridBindingState }>;
  };
  constitutionRatification: ConstitutionRatificationState;
  mindConduit: MindConduitSealStatus;
}

export interface ConstitutionRatificationState {
  currentConstitutionHash: string;
  previousConstitutionHash?: string;
  changed: boolean;
  affectedModels: readonly string[];
  manifestsRequiringRegeneration: readonly string[];
}

export interface BuilderDependencies {
  initializeMoScriptEngine(): Promise<void>;
  loadMoScriptRegistry(): Promise<MoScriptRegistry>;
  applyScrollValidator(): Promise<void>;
  enforceThroneLock(): Promise<void>;
  activateResonanceEngine(): Promise<void>;
  populateScrollRegistry(): Promise<void>;
  bindWooInterpreter(): Promise<void>;
  connectDeepCAL(): Promise<void>;
  modelManifestRegistry: ModelManifestRegistry;
  modelBindingGuard: ModelBindingGuard;
  sealCanonicalQueryRegistry(): Promise<void>;
  constitutionCypherGuard: CypherGuard;
  provenanceGateHealthcheck(): Promise<boolean>;
  attestationGuardSelfTest(): Promise<boolean>;
  sealReceiptVerifier: {
    load(): Promise<MindConduitSealReceipt | null>;
    verifySignature(receipt: MindConduitSealReceipt): Promise<boolean>;
    verifySourceDigest(receipt: MindConduitSealReceipt): Promise<boolean>;
  };
  snapshotBuilderSelfTest(): Promise<boolean>;
  inferenceAuditHealthcheck(): Promise<boolean>;
  loadInvocationSurfaceLedger(): Promise<InvocationSurfaceLedger>;
  initializeDcxGateway(): Promise<void>;
  dcxGatewaySelfTest(): Promise<boolean>;
}

export class MoStarBuilder {
  private readonly status: GridBuilderStatus = {
    buildId: globalThis.crypto?.randomUUID?.() ?? `build-${Date.now()}`,
    state: "INITIALIZING",
    tags: [MOSCRIPTS_TAG],
    components: {},
    mindBinding: { state: "UNINITIALIZED", models: {} },
    constitutionRatification: {
      currentConstitutionHash: "",
      changed: false,
      affectedModels: [],
      manifestsRequiringRegeneration: [],
    },
    mindConduit: deriveGridReadiness({
      MODEL_BINDING: "UNVERIFIED",
      CYPHER_GUARD: "UNVERIFIED",
      PROVENANCE_FILTER: "UNVERIFIED",
      ATTESTATION_GUARD: "UNVERIFIED",
      INVOCATION_SURFACE_GUARD: "UNVERIFIED",
      HOSTILE_PATH_TEST: "UNVERIFIED",
    }),
  };
  constructor(private readonly deps: BuilderDependencies) {}
  getStatus(): GridBuilderStatus {
    return structuredClone(this.status);
  }

  async initialize(): Promise<GridBuilderStatus> {
    try {
      await this.step("moscript-runtime", true, () => this.deps.initializeMoScriptEngine());
      await this.step("moscript-runtime-map", true, async () => {
        if (deriveMoScriptRegistryHealth(await this.deps.loadMoScriptRegistry()) !== "SEALED")
          throw new Error("MOSCRIPT_RUNTIME_MAPPING_FAILED");
      });
      await this.step("scroll-validator", true, () => this.deps.applyScrollValidator());
      await this.step("thronelock", true, () => this.deps.enforceThroneLock());
      await this.step("resonance-engine", true, () => this.deps.activateResonanceEngine());
      await this.step("scroll-registry", true, () => this.deps.populateScrollRegistry());
      await this.step("model-manifest-registry", true, async () => {
        await this.deps.modelManifestRegistry.initialize();
        await this.deps.modelManifestRegistry.verifyRegistryIntegrity();
      });
      await this.step("cypher-guard", true, async () => {
        await this.deps.sealCanonicalQueryRegistry();
        const binding = await this.deps.modelBindingGuard.computeCurrentBinding();
        await verifyConstitutionComposition({
          cypherGuard: this.deps.constitutionCypherGuard,
          canonicalConstitutionDigest: binding.constitutionHash,
        });
      });
      await this.step("provenance-filter", true, async () => {
        if (!(await this.deps.provenanceGateHealthcheck()))
          throw new Error("PROVENANCE_GATE_UNAVAILABLE");
      });
      await this.step("grid-mind-snapshot-builder", true, async () => {
        if (!(await this.deps.snapshotBuilderSelfTest()))
          throw new Error("SNAPSHOT_BUILDER_SELF_TEST_FAILED");
      });
      await this.step("inference-audit-writer", true, async () => {
        if (!(await this.deps.inferenceAuditHealthcheck()))
          throw new Error("INFERENCE_AUDIT_UNAVAILABLE");
      });
      let constitutionDrift = false;
      await this.step("model-binding", true, async () => {
        const current = await this.deps.modelBindingGuard.computeCurrentBinding();
        this.status.mindBinding.bindingRoot = current.bindingRoot;
        this.status.constitutionRatification.currentConstitutionHash = current.constitutionHash;
        const models = await this.deps.modelManifestRegistry.listConfiguredModels();
        if (!models.length) {
          this.status.mindBinding.state = "DETACHED";
          throw new Error("NO_CONFIGURED_GRID_MODELS");
        }
        for (const modelId of models) {
          const result = await this.deps.modelBindingGuard.verifyModel(modelId);
          this.status.mindBinding.models[modelId] = {
            process: result.processOnline ? "ONLINE" : "OFFLINE",
            binding: result.state,
          };
        }
        const driftedModels = Object.entries(this.status.mindBinding.models)
          .filter(([, model]) => model.binding === "CONSTITUTION_DRIFT")
          .map(([modelId]) => modelId);
        if (driftedModels.length) {
          constitutionDrift = true;
          this.status.constitutionRatification = {
            currentConstitutionHash: current.constitutionHash,
            changed: true,
            affectedModels: Object.freeze(driftedModels),
            manifestsRequiringRegeneration: Object.freeze(driftedModels),
          };
          this.status.mindBinding.state = "DEGRADED";
          return;
        }
        if (
          Object.values(this.status.mindBinding.models).some((model) => model.binding !== "SEALED")
        ) {
          this.status.mindBinding.state = "DEGRADED";
          throw new Error("ONE_OR_MORE_MODELS_NOT_GRID_BOUND");
        }
        this.status.mindBinding.state = "SEALED";
      });
      if (constitutionDrift) {
        this.status.components["model-binding"] = {
          id: "model-binding",
          state: "BLOCKED",
          critical: true,
          detail: "CONSTITUTION_DRIFT:AUTHORIZED_MANIFEST_REGENERATION_REQUIRED",
        };
      }
      await this.step("attestation-guard", true, async () => {
        if (!(await this.deps.attestationGuardSelfTest()))
          throw new Error("ATTESTATION_GUARD_SELF_TEST_FAILED");
      });
      const receiptSeal = await this.verifyMindConduitSealReceipt();
      const invocationSurface = deriveInvocationSurfaceGuard(
        await this.deps.loadInvocationSurfaceLedger(),
      );
      this.status.mindConduit = deriveGridReadiness({
        MODEL_BINDING: constitutionDrift
          ? "CONSTITUTION_DRIFT"
          : this.status.components["model-binding"]?.state === "READY"
            ? "SEALED"
            : "FAILED",
        CYPHER_GUARD:
          this.status.components["cypher-guard"]?.state === "READY" ? "SEALED" : "FAILED",
        PROVENANCE_FILTER:
          this.status.components["provenance-filter"]?.state === "READY" ? "SEALED" : "FAILED",
        ATTESTATION_GUARD:
          this.status.components["attestation-guard"]?.state === "READY" ? "SEALED" : "FAILED",
        INVOCATION_SURFACE_GUARD:
          invocationSurface === "SEALED" && receiptSeal.invocationSurfacePassed
            ? "SEALED"
            : invocationSurface,
        HOSTILE_PATH_TEST: receiptSeal.hostilePathPassed ? "PASS" : "UNVERIFIED",
      });
      if (!this.status.mindConduit.GRID_MIND_READY) {
        this.status.state = "DEGRADED";
        const detail = `MIND_CONDUIT_PARTIAL:${this.status.mindConduit.blockers.join(",")}`;
        this.status.components["dcx-gateway"] = {
          id: "dcx-gateway",
          state: "BLOCKED",
          critical: true,
          detail,
        };
        this.status.components["woo-interpreter"] = {
          id: "woo-interpreter",
          state: "BLOCKED",
          critical: true,
          detail: "GRID_MIND_NOT_READY",
        };
        this.status.components["deepcal-model-reasoning"] = {
          id: "deepcal-model-reasoning",
          state: "BLOCKED",
          critical: false,
          detail: "GRID_MIND_NOT_READY",
        };
        return this.getStatus();
      }
      await this.step("dcx-gateway", true, async () => {
        await this.deps.initializeDcxGateway();
        if (!(await this.deps.dcxGatewaySelfTest()))
          throw new Error("DCX_GATEWAY_SELF_TEST_FAILED");
      });
      await this.step("woo-interpreter", true, () => this.deps.bindWooInterpreter());
      await this.step("deepcal", false, () => this.deps.connectDeepCAL());
      this.status.state = Object.values(this.status.components).some(
        (value) => value.state === "DEGRADED",
      )
        ? "DEGRADED"
        : "READY";
      return this.getStatus();
    } catch (error) {
      this.status.state = "FAILED";
      throw error;
    }
  }

  private async step(id: string, critical: boolean, operation: () => Promise<void>): Promise<void> {
    this.status.components[id] = { id, critical, state: "INITIALIZING" };
    try {
      await operation();
      this.status.components[id] = { id, critical, state: "READY" };
    } catch (error) {
      const detail = error instanceof Error ? error.message : "UNKNOWN_ERROR";
      this.status.components[id] = {
        id,
        critical,
        state: critical ? "FAILED" : "DEGRADED",
        detail,
      };
      if (critical) throw error;
    }
  }

  private async verifyMindConduitSealReceipt(): Promise<{
    hostilePathPassed: boolean;
    invocationSurfacePassed: boolean;
  }> {
    const receipt = await this.deps.sealReceiptVerifier.load();
    if (!receipt || receipt.schema !== "mostar.mind-conduit-seal.v1")
      return { hostilePathPassed: false, invocationSurfacePassed: false };
    const [signatureValid, sourceValid] = await Promise.all([
      this.deps.sealReceiptVerifier.verifySignature(receipt),
      this.deps.sealReceiptVerifier.verifySourceDigest(receipt),
    ]);
    const tests = receipt.tests;
    const hostileTestsPass = [
      "HP-1",
      "HP-2",
      "HP-3",
      "HP-4-timeout",
      "HP-4-5xx",
      "HP-5",
      "HP-6",
      "HP-7A",
      "HP-7B",
      "HP-7C",
      "HP-7D",
      "HP-8",
    ].every((name) => tests[name as keyof typeof tests] === "PASS");
    const auditSealed =
      receipt.invocation_surface_audit.scanned &&
      receipt.invocation_surface_audit.unauthorized_call_sites === 0;
    const contract = receipt.adapter_contract;
    const adapterSealed =
      contract.backend_calls_conduit_only &&
      contract.direct_ollama_forbidden &&
      contract.direct_dcx_runtime_forbidden &&
      contract.all_model_inference_conduit_only &&
      contract.prohibited_name_scoping &&
      contract.bypass_flags_forbidden;
    const receiptBoundToConstitution =
      receipt.constitution_hash === this.status.constitutionRatification.currentConstitutionHash;
    const receiptValid = signatureValid && sourceValid && receiptBoundToConstitution;
    return {
      hostilePathPassed: receiptValid && hostileTestsPass,
      invocationSurfacePassed: receiptValid && auditSealed && adapterSealed,
    };
  }
}
