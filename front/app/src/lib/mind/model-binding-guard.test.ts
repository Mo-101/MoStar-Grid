import { describe, expect, it } from "vitest";
import {
  MOSCRIPTS_TAG,
  ModelBindingGuard,
  type BindingSource,
  type GridModelManifest,
  type ModelManifestRegistry,
} from "./model-binding-guard";

const source: BindingSource = {
  getConstitutionHash: async () => "constitution",
  getQueryRegistryHash: async () => "queries",
  getRelationshipVocabularyHash: async () => "relationships",
  getProvenancePolicyHash: async () => "provenance",
  getMoScriptBundleHash: async () => "moscript-bundle",
  getSnapshotSchemaHash: async () => "snapshot",
  getToolPolicyHash: async () => "tools",
};

async function fixture(options: { manifest?: boolean; tags?: string[]; online?: boolean } = {}) {
  let manifest: GridModelManifest | undefined;
  const registry: ModelManifestRegistry = {
    initialize: async () => undefined,
    verifyRegistryIntegrity: async () => undefined,
    get: async () => manifest,
    listConfiguredModels: async () => ["dcx0"],
  };
  const guard = new ModelBindingGuard(
    registry,
    source,
    { isOnline: async () => options.online ?? true, getModelDigest: async () => "model-digest" },
    { verify: async () => true },
  );
  if (options.manifest !== false) {
    manifest = {
      schema: "mostar.grid-model-manifest.v1",
      model: {
        model_id: "dcx0",
        runtime_id: "ollama-local",
        capability: "GENERATIVE_TEXT",
        model_digest: "model-digest",
      },
      maker: "mostar-grid",
      required_tags: (options.tags ?? [MOSCRIPTS_TAG]) as ["MoScripts"],
      binding: {
        constitution_hash: "",
        moscript_bundle_hash: "",
        query_registry_hash: "",
        provenance_policy_hash: "",
        relationship_vocabulary_hash: "",
        snapshot_schema_hash: "",
        tool_policy_hash: "",
        binding_root: "",
      },
      authority: {
        issuer: "test-authority",
        key_ref: "test-key",
        issued_at: "2026-01-01T00:00:00Z",
        valid_until: "2027-01-01T00:00:00Z",
        signature: "sig:dcx0",
      },
    };
    const binding = await guard.computeCurrentBinding();
    manifest.binding = {
      constitution_hash: binding.constitutionHash,
      moscript_bundle_hash: binding.moscriptBundleHash,
      query_registry_hash: binding.queryRegistryHash,
      provenance_policy_hash: binding.provenancePolicyHash,
      relationship_vocabulary_hash: binding.relationshipVocabularyHash,
      snapshot_schema_hash: binding.snapshotSchemaHash,
      tool_policy_hash: binding.toolPolicyHash,
      binding_root: binding.bindingRoot,
    };
  }
  return guard;
}

describe("ModelBindingGuard", () => {
  it("blocks an online model when its manifest is missing", async () => {
    const result = await (await fixture({ manifest: false, online: true })).verifyModel("dcx0");
    expect(result).toMatchObject({ processOnline: true, state: "MANIFEST_MISSING" });
  });

  it("requires the exact MoScripts tag", async () => {
    const missing = await (await fixture({ tags: ["moscripts"] })).verifyModel("dcx0");
    expect(missing.state).toBe("MOSCRIPTS_TAG_MISSING");
    const sealed = await (await fixture()).verifyModel("dcx0");
    expect(sealed.state).toBe("SEALED");
  });

  it("binds the MoScript bundle hash into the root", async () => {
    const guard = await fixture();
    const first = await guard.computeCurrentBinding();
    const changed = new ModelBindingGuard(
      {
        initialize: async () => undefined,
        verifyRegistryIntegrity: async () => undefined,
        get: async () => undefined,
        listConfiguredModels: async () => [],
      },
      { ...source, getMoScriptBundleHash: async () => "changed-moscript-bundle" },
      { isOnline: async () => true, getModelDigest: async () => "model-digest" },
      { verify: async () => true },
    );
    expect((await changed.computeCurrentBinding()).bindingRoot).not.toBe(first.bindingRoot);
  });
  it("HP-8 blocks an online, correctly signed model after constitutional drift", async () => {
    const original = await fixture({ online: true });
    const manifest = (original as unknown as { manifests: ModelManifestRegistry }).manifests;
    const changed = new ModelBindingGuard(
      manifest,
      { ...source, getConstitutionHash: async () => "constitution-amended" },
      { isOnline: async () => true, getModelDigest: async () => "model-digest" },
      { verify: async () => true },
    );
    await expect(changed.verifyModel("dcx0")).resolves.toMatchObject({
      state: "CONSTITUTION_DRIFT",
      processOnline: true,
    });
  });
});
