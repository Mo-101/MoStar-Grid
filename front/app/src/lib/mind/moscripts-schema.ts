export const MOSCRIPTS_TAG = "MoScripts" as const;

export interface MoScriptImplementationMapping {
  moscript_id: string;
  moscript_source: string;
  moscript_source_digest: string;
  implementation_file: string;
  implementation_symbol: string;
  implementation_digest: string;
  implemented_at_commit: string;
  verified?: boolean;
}

export interface MoScriptRegistry {
  schema: "mostar.moscript-runtime-map.v1";
  authority: "MoScripts";
  mappings: readonly MoScriptImplementationMapping[];
}

export function deriveMoScriptRegistryHealth(registry: MoScriptRegistry): "SEALED" | "FAILED" {
  if (registry.authority !== MOSCRIPTS_TAG || registry.mappings.length === 0) return "FAILED";
  return registry.mappings.every(
    (item) =>
      Boolean(item.moscript_id) &&
      /^[a-f0-9]{64}$/.test(item.moscript_source_digest) &&
      /^[a-f0-9]{64}$/.test(item.implementation_digest) &&
      item.verified !== false,
  )
    ? "SEALED"
    : "FAILED";
}
