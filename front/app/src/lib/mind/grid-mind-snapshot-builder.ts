import {
  type ProvenanceFilteredMemory,
  type ProvenanceFilteredPayload,
  ProvenanceFilter,
} from "./provenance-filter";

export interface GridMindSnapshot {
  readonly snapshot_id: string;
  readonly snapshot_digest: string;
  readonly created_at: string;
  readonly grid_id: "mostar-grid";
  readonly requesting_model_id: string;
  readonly binding_root: string;
  readonly memory: ProvenanceFilteredPayload;
  readonly senses: unknown;
}
function canonicalize(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  const object = value as Record<string, unknown>;
  return `{${Object.keys(object)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalize(object[key])}`)
    .join(",")}}`;
}
async function digest(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalize(value));
  if (globalThis.crypto?.subtle) {
    const result = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(result), (byte) => byte.toString(16).padStart(2, "0")).join(
      "",
    );
  }
  const { createHash } = await import("node:crypto");
  return createHash("sha256").update(bytes).digest("hex");
}
export class GridMindSnapshotBuilder {
  constructor(private readonly provenanceFilter: ProvenanceFilter) {}
  async assemble(input: {
    grid_id: "mostar-grid";
    requesting_model_id: string;
    binding_root: string;
    memory: ProvenanceFilteredMemory;
    senses: unknown;
  }): Promise<GridMindSnapshot> {
    this.provenanceFilter.assertIssued(input.memory);
    const unsigned = Object.freeze({
      snapshot_id: globalThis.crypto?.randomUUID?.() ?? `snapshot-${Date.now()}`,
      created_at: new Date().toISOString(),
      grid_id: input.grid_id,
      requesting_model_id: input.requesting_model_id,
      binding_root: input.binding_root,
      memory: input.memory.payload,
      senses: input.senses,
    });
    return Object.freeze({ ...unsigned, snapshot_digest: await digest(unsigned) });
  }
}
