import type { GridReadiness } from "./grid-status-schema";

const HUMAN_AUTHORIZATION = Symbol("MOSTAR_HUMAN_SEAL_AUTHORIZATION");

export class HumanAuthorization {
  private constructor(
    private readonly authority: symbol,
    readonly authorizedBy: string,
  ) {}
  static issueFromHumanCeremony(authorizedBy: string): HumanAuthorization {
    if (!authorizedBy.trim()) throw new Error("HUMAN_AUTHORITY_ID_REQUIRED");
    return new HumanAuthorization(HUMAN_AUTHORIZATION, authorizedBy);
  }
  assertValid(): void {
    if (this.authority !== HUMAN_AUTHORIZATION) throw new Error("NO_HUMAN_AUTHORIZATION");
  }
}

export type ReceiptWithheld = {
  disposition: "WITHHELD";
  reason: "NO_HUMAN_AUTHORIZATION" | "WORKTREE_NOT_COMMITTED" | "GRID_NOT_FULLY_SEALED";
};

export function mintSealReceipt(input: {
  readiness: GridReadiness;
  worktreeCommit: string | null;
  humanAuthorization?: HumanAuthorization;
}): ReceiptWithheld | { disposition: "MINTED"; commit: string; authorized_by: string } {
  if (!input.humanAuthorization)
    return { disposition: "WITHHELD", reason: "NO_HUMAN_AUTHORIZATION" };
  input.humanAuthorization.assertValid();
  if (!input.worktreeCommit) return { disposition: "WITHHELD", reason: "WORKTREE_NOT_COMMITTED" };
  if (!input.readiness.GRID_MIND_READY)
    return { disposition: "WITHHELD", reason: "GRID_NOT_FULLY_SEALED" };
  return {
    disposition: "MINTED",
    commit: input.worktreeCommit,
    authorized_by: input.humanAuthorization.authorizedBy,
  };
}
