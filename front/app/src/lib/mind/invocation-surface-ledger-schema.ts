export type InvocationAuthorization = "AUTHORIZED" | "UNAUTHORIZED" | "UNRESOLVED";

export interface InvocationSurfaceRow {
  surface_id: string;
  source_file: string;
  symbol_or_line: string;
  entrypoint: string;
  caller: string;
  model_or_runtime: string;
  provider: string;
  transport: string;
  invocation_mechanism: string;
  passes_through_mind_conduit: boolean;
  binding_enforced: boolean;
  invocation_capability_required: boolean;
  sovereignty_impact: string;
  capability_impact: string;
  authorized_or_unauthorized: InvocationAuthorization;
  current_disposition: string;
  evidence_ref: string;
  historical_gate_name: "INVOCATION_AUDIT";
  current_gate_name: "INVOCATION_SURFACE_GUARD";
  history_notes: string;
  surface_history_class:
    | "ORIGINAL_AUTHORIZED"
    | "MIGRATED_FORMERLY_UNAUTHORIZED"
    | "NEWLY_DISCOVERED_NEWLY_AUTHORIZED";
}

export interface InvocationSurfaceLedger {
  schema: "mostar.invocation-surface-ledger.v1";
  discovered_surfaces: number;
  accounted_surfaces: number;
  unauthorized_surfaces: number;
  surfaces: readonly InvocationSurfaceRow[];
}

export function assertLedgerIntegrity(ledger: InvocationSurfaceLedger): void {
  if (ledger.discovered_surfaces !== ledger.accounted_surfaces)
    throw new Error("INVOCATION_SURFACE_ACCOUNTING_MISMATCH");
  if (ledger.surfaces.length !== ledger.accounted_surfaces)
    throw new Error("INVOCATION_SURFACE_ROW_COUNT_MISMATCH");
  if (new Set(ledger.surfaces.map((row) => row.surface_id)).size !== ledger.surfaces.length)
    throw new Error("INVOCATION_SURFACE_ID_COLLISION");
}

export function deriveInvocationSurfaceGuard(ledger: InvocationSurfaceLedger): "SEALED" | "FAILED" {
  assertLedgerIntegrity(ledger);
  const unauthorized = ledger.surfaces.filter(
    (row) => row.authorized_or_unauthorized === "UNAUTHORIZED",
  ).length;
  if (unauthorized !== ledger.unauthorized_surfaces)
    throw new Error("INVOCATION_SURFACE_UNAUTHORIZED_COUNT_MISMATCH");
  return unauthorized === 0 ? "SEALED" : "FAILED";
}
