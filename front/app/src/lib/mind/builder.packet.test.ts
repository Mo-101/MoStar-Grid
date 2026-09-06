import { describe, expect, it, vi } from "vitest";
import { deriveGridReadiness, MoStarBuilder, type BuilderDependencies } from "./builder.packet";
import {
  ModelBindingGuard,
  type BindingSource,
  type ModelManifestRegistry,
} from "./model-binding-guard";
import { CanonicalQueryRegistry, CypherGuard } from "./cypher-guard";
import { registerConstitutionChainQuery } from "./constitution-composition";

describe("MoStarBuilder", () => {
  it("does not seal the conduit without the hostile-path receipt", () => {
    expect(
      deriveGridReadiness({
        MODEL_BINDING: "SEALED",
        CYPHER_GUARD: "SEALED",
        PROVENANCE_FILTER: "SEALED",
        ATTESTATION_GUARD: "SEALED",
        INVOCATION_SURFACE_GUARD: "SEALED",
        HOSTILE_PATH_TEST: "UNVERIFIED",
      }),
    ).toMatchObject({ MIND_CONDUIT: "PARTIAL", GRID_MIND_READY: false });
  });
  it("blocks downstream AI when an online model has no signed manifest", async () => {
    const constitutionHash = "c".repeat(64);
    const manifests: ModelManifestRegistry = {
      initialize: async () => undefined,
      verifyRegistryIntegrity: async () => undefined,
      get: async () => undefined,
      listConfiguredModels: async () => ["dcx0"],
    };
    const source: BindingSource = {
      getConstitutionHash: async () => constitutionHash,
      getQueryRegistryHash: async () => "q",
      getRelationshipVocabularyHash: async () => "r",
      getProvenancePolicyHash: async () => "p",
      getMoScriptBundleHash: async () => "m",
      getSnapshotSchemaHash: async () => "s",
      getToolPolicyHash: async () => "t",
    };
    const bindingGuard = new ModelBindingGuard(
      manifests,
      source,
      { isOnline: async () => true, getModelDigest: async () => "digest" },
      { verify: async () => true },
    );
    const constitutionRegistry = new CanonicalQueryRegistry();
    registerConstitutionChainQuery(constitutionRegistry);
    constitutionRegistry.seal();
    const constitutionCypherGuard = new CypherGuard(constitutionRegistry, {
      runRead: async () => [
        {
          constitution_hash: constitutionHash,
          provenance_hash: constitutionHash,
          attestation_hash: constitutionHash,
          attestation_subject_digest: constitutionHash,
        },
      ],
    });
    const bindWooInterpreter = vi.fn(async () => undefined);
    const initializeDcxGateway = vi.fn(async () => undefined);
    const ok = async () => undefined;
    const deps: BuilderDependencies = {
      initializeMoScriptEngine: ok,
      loadMoScriptRegistry: async () => ({
        schema: "mostar.moscript-runtime-map.v1",
        authority: "MoScripts",
        mappings: [
          {
            moscript_id: "test",
            moscript_source: "test",
            moscript_source_digest: "a".repeat(64),
            implementation_file: "test",
            implementation_symbol: "test",
            implementation_digest: "b".repeat(64),
            implemented_at_commit: "WORKTREE_UNCOMMITTED",
          },
        ],
      }),
      applyScrollValidator: ok,
      enforceThroneLock: ok,
      activateResonanceEngine: ok,
      populateScrollRegistry: ok,
      bindWooInterpreter,
      connectDeepCAL: ok,
      modelManifestRegistry: manifests,
      modelBindingGuard: bindingGuard,
      sealCanonicalQueryRegistry: ok,
      constitutionCypherGuard,
      provenanceGateHealthcheck: async () => true,
      attestationGuardSelfTest: async () => true,
      sealReceiptVerifier: {
        load: async () => null,
        verifySignature: async () => false,
        verifySourceDigest: async () => false,
      },
      snapshotBuilderSelfTest: async () => true,
      inferenceAuditHealthcheck: async () => true,
      loadInvocationSurfaceLedger: async () => ({
        schema: "mostar.invocation-surface-ledger.v1",
        discovered_surfaces: 0,
        accounted_surfaces: 0,
        unauthorized_surfaces: 0,
        surfaces: [],
      }),
      initializeDcxGateway,
      dcxGatewaySelfTest: async () => true,
    };
    const builder = new MoStarBuilder(deps);
    await expect(builder.initialize()).rejects.toThrow("ONE_OR_MORE_MODELS_NOT_GRID_BOUND");
    expect(builder.getStatus()).toMatchObject({
      state: "FAILED",
      tags: ["MoScripts"],
      mindBinding: {
        state: "DEGRADED",
        models: { dcx0: { process: "ONLINE", binding: "MANIFEST_MISSING" } },
      },
    });
    expect(initializeDcxGateway).not.toHaveBeenCalled();
    expect(bindWooInterpreter).not.toHaveBeenCalled();
  });
});
