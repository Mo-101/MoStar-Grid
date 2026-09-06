import type { ModelCapability } from "./model-runtime";
import { MOSCRIPTS_TAG } from "./moscripts-schema";
export { MOSCRIPTS_TAG } from "./moscripts-schema";

export type GridBindingState =
  | "SEALED"
  | "MANIFEST_MISSING"
  | "MOSCRIPTS_TAG_MISSING"
  | "MODEL_DIGEST_MISMATCH"
  | "CONSTITUTION_DRIFT"
  | "QUERY_REGISTRY_DRIFT"
  | "PROVENANCE_POLICY_DRIFT"
  | "SNAPSHOT_SCHEMA_DRIFT"
  | "TOOL_POLICY_DRIFT"
  | "DETACHED";

export interface GridBindingComponents {
  constitutionHash: string;
  queryRegistryHash: string;
  relationshipVocabularyHash: string;
  provenancePolicyHash: string;
  moscriptBundleHash: string;
  snapshotSchemaHash: string;
  toolPolicyHash: string;
}

export interface GridBindingDigest extends GridBindingComponents {
  bindingRoot: string;
}

export interface GridManifestBinding {
  constitution_hash: string;
  moscript_bundle_hash: string;
  query_registry_hash: string;
  provenance_policy_hash: string;
  relationship_vocabulary_hash: string;
  snapshot_schema_hash: string;
  tool_policy_hash: string;
  binding_root: string;
}

export interface GridModelManifest {
  schema: "mostar.grid-model-manifest.v1";
  model: {
    model_id: string;
    runtime_id: string;
    family?: string;
    provider?: string;
    capability: ModelCapability;
    model_digest: string;
  };
  maker: "mostar-grid";
  required_tags: readonly ["MoScripts"];
  binding: GridManifestBinding;
  authority: {
    issuer: string;
    key_ref: string;
    issued_at: string;
    valid_until: string;
    signature: string;
  };
}

export interface ModelManifestRegistry {
  initialize(): Promise<void>;
  verifyRegistryIntegrity(): Promise<void>;
  get(modelId: string): Promise<GridModelManifest | undefined>;
  listConfiguredModels(): Promise<string[]>;
}

export interface BindingSource {
  getConstitutionHash(): Promise<string>;
  getQueryRegistryHash(): Promise<string>;
  getRelationshipVocabularyHash(): Promise<string>;
  getProvenancePolicyHash(): Promise<string>;
  getMoScriptBundleHash(): Promise<string>;
  getSnapshotSchemaHash(): Promise<string>;
  getToolPolicyHash(): Promise<string>;
}

export interface ModelRuntimeProbe {
  isOnline(modelId: string): Promise<boolean>;
  getModelDigest(modelId: string): Promise<string | undefined>;
}

export interface ManifestSignatureVerifier {
  verify(manifest: GridModelManifest): Promise<boolean>;
}

async function sha256(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  if (globalThis.crypto?.subtle) {
    const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join(
      "",
    );
  }
  const { createHash } = await import("node:crypto");
  return createHash("sha256").update(bytes).digest("hex");
}

export class ModelBindingGuard {
  constructor(
    private readonly manifests: ModelManifestRegistry,
    private readonly source: BindingSource,
    private readonly runtime: ModelRuntimeProbe,
    private readonly signatures: ManifestSignatureVerifier,
  ) {}

  async computeCurrentBinding(): Promise<GridBindingDigest> {
    const binding: GridBindingComponents = {
      constitutionHash: await this.source.getConstitutionHash(),
      queryRegistryHash: await this.source.getQueryRegistryHash(),
      relationshipVocabularyHash: await this.source.getRelationshipVocabularyHash(),
      provenancePolicyHash: await this.source.getProvenancePolicyHash(),
      moscriptBundleHash: await this.source.getMoScriptBundleHash(),
      snapshotSchemaHash: await this.source.getSnapshotSchemaHash(),
      toolPolicyHash: await this.source.getToolPolicyHash(),
    };
    const canonical = Object.values(binding).join("|");
    return { ...binding, bindingRoot: await sha256(canonical) };
  }

  async verifyModel(modelId: string): Promise<{
    state: GridBindingState;
    processOnline: boolean;
    bindingRoot?: string;
  }> {
    const processOnline = await this.runtime.isOnline(modelId);
    const manifest = await this.manifests.get(modelId);
    if (!manifest) return { state: "MANIFEST_MISSING", processOnline };
    if (!manifest.required_tags.includes(MOSCRIPTS_TAG)) {
      return { state: "MOSCRIPTS_TAG_MISSING", processOnline };
    }
    if (!(await this.signatures.verify(manifest))) return { state: "DETACHED", processOnline };
    const runtimeDigest = await this.runtime.getModelDigest(modelId);
    if (!runtimeDigest || runtimeDigest !== manifest.model.model_digest) {
      return { state: "MODEL_DIGEST_MISMATCH", processOnline };
    }
    const current = await this.computeCurrentBinding();
    const declared = manifest.binding;
    const checks: Array<[boolean, GridBindingState]> = [
      [declared.constitution_hash === current.constitutionHash, "CONSTITUTION_DRIFT"],
      [declared.query_registry_hash === current.queryRegistryHash, "QUERY_REGISTRY_DRIFT"],
      [declared.provenance_policy_hash === current.provenancePolicyHash, "PROVENANCE_POLICY_DRIFT"],
      [declared.snapshot_schema_hash === current.snapshotSchemaHash, "SNAPSHOT_SCHEMA_DRIFT"],
      [declared.tool_policy_hash === current.toolPolicyHash, "TOOL_POLICY_DRIFT"],
    ];
    for (const [ok, failure] of checks) {
      if (!ok) return { state: failure, processOnline, bindingRoot: current.bindingRoot };
    }
    if (
      declared.relationship_vocabulary_hash !== current.relationshipVocabularyHash ||
      declared.moscript_bundle_hash !== current.moscriptBundleHash ||
      declared.binding_root !== current.bindingRoot
    )
      return { state: "DETACHED", processOnline, bindingRoot: current.bindingRoot };
    return { state: "SEALED", processOnline, bindingRoot: current.bindingRoot };
  }
}
