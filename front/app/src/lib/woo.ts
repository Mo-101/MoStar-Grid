/**
 * Woo shadow-mode activation and trace lineage.
 *
 * This module is environment-agnostic: it uses `localStorage` for trace
 * persistence and `crypto.subtle` for hashes when available, with a Node
 * fallback for SSR/tests. It does not read `process.env` directly; callers
 * pass configuration so the same code can run on the server and in tests.
 */

export type WooMode = "shadow" | "advisory" | "enforcing";

export type WooTrace = Readonly<{
  traceId: string;
  requestId: string;
  scrollId: string;

  actor: string;
  wooVersion: string;
  resonanceEngineVersion: string;

  status: "approved" | "warning" | "denied";
  resonanceScore: number;

  graphRunId: string | null;
  evidenceNodeIds: readonly string[];

  inputHash: string;
  outputHash: string;

  mode: WooMode;
  createdAt: string;
}>;

export type WooActivationConfig = Readonly<{
  enabled: boolean;
  mode: WooMode;
  executionEnabled: boolean;
  graphWriteEnabled: boolean;
  denyThreshold: number;
  approveThreshold: number;
  graphRunId: string;
}>;

export type WooActivationDependencies = Readonly<{
  initializeMoScriptEngine(): Promise<void>;
  applyScrollValidator(): Promise<void>;
  enforceThroneLock(): Promise<void>;
  activateResonanceEngine(): Promise<void>;
  validateWooIdentity(): Promise<boolean>;
  verifyGraphRun(runId: string): Promise<boolean>;
  bindWooInterpreter(): Promise<void>;
}>;

export const WOO_TRACE_STORAGE_KEY = "mostar:woo:traces";
export const WOO_VERSION = "1.0.0-shadow";
export const RESONANCE_ENGINE_VERSION = "1.0.0";

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function getStorage(): Storage {
  if (!isBrowser()) {
    throw new Error("Woo trace storage is only available in browser-like environments");
  }
  return window.localStorage;
}

function isValidSha256Hex(hash: string): boolean {
  return /^[0-9a-f]{64}$/i.test(hash);
}

async function hashString(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  if (typeof crypto !== "undefined" && crypto.subtle) {
    const buffer = await crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(buffer))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }
  // Node/SSR fallback for tests and server-side usage
  const { createHash } = await import("node:crypto");
  return createHash("sha256").update(data).digest("hex");
}

function generateTraceId(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let out = "woo-";
  for (let i = 0; i < 24; i += 1) {
    out += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return out;
}

export function getWooTraces(): readonly WooTrace[] {
  try {
    const raw = getStorage().getItem(WOO_TRACE_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown[];
    return parsed.filter((item): item is WooTrace => isWooTrace(item));
  } catch {
    return [];
  }
}

export function appendWooTrace(trace: WooTrace): void {
  const existing = getWooTraces();
  const next = [...existing, trace];
  getStorage().setItem(WOO_TRACE_STORAGE_KEY, JSON.stringify(next));
}

export function clearWooTraces(): void {
  if (!isBrowser()) return;
  getStorage().removeItem(WOO_TRACE_STORAGE_KEY);
}

function isWooTrace(value: unknown): value is WooTrace {
  if (typeof value !== "object" || value === null) return false;
  const t = value as Record<string, unknown>;
  return (
    typeof t.traceId === "string" &&
    typeof t.requestId === "string" &&
    typeof t.scrollId === "string" &&
    typeof t.actor === "string" &&
    typeof t.wooVersion === "string" &&
    typeof t.resonanceEngineVersion === "string" &&
    (t.status === "approved" || t.status === "warning" || t.status === "denied") &&
    typeof t.resonanceScore === "number" &&
    (t.graphRunId === null || typeof t.graphRunId === "string") &&
    Array.isArray(t.evidenceNodeIds) &&
    t.evidenceNodeIds.every((id) => typeof id === "string") &&
    typeof t.inputHash === "string" &&
    typeof t.outputHash === "string" &&
    (t.mode === "shadow" || t.mode === "advisory" || t.mode === "enforcing") &&
    typeof t.createdAt === "string"
  );
}

export async function activateWoo(
  config: WooActivationConfig,
  dependencies: WooActivationDependencies,
): Promise<void> {
  if (!config.enabled) {
    return;
  }

  if (
    config.denyThreshold < 0 ||
    config.approveThreshold > 1 ||
    config.denyThreshold >= config.approveThreshold
  ) {
    throw new Error("Invalid Woo resonance thresholds");
  }

  if (config.mode === "shadow") {
    if (config.executionEnabled || config.graphWriteEnabled) {
      throw new Error("Shadow mode cannot execute or mutate graph data");
    }
  }

  await dependencies.initializeMoScriptEngine();
  await dependencies.applyScrollValidator();
  await dependencies.enforceThroneLock();
  await dependencies.activateResonanceEngine();

  const identityValid = await dependencies.validateWooIdentity();
  if (!identityValid) {
    throw new Error("Woo identity validation failed");
  }

  const graphRunValid = await dependencies.verifyGraphRun(config.graphRunId);
  if (!graphRunValid) {
    throw new Error("Woo graph context lineage is invalid");
  }

  await dependencies.bindWooInterpreter();
}

export type WooEvaluationInput = Readonly<{
  scrollId: string;
  requestId: string;
  actor: string;
  sealedScrollText: string;
  mode: WooMode;
  graphRunId: string;
  evidenceNodeIds: readonly string[];
}>;

export type WooEvaluationOptions = Readonly<{
  denyThreshold: number;
  approveThreshold: number;
  getResonanceScore(input: string): Promise<number>;
}>;

export async function evaluateWoo(
  input: WooEvaluationInput,
  options: WooEvaluationOptions,
): Promise<WooTrace> {
  const resonanceScore = await options.getResonanceScore(input.sealedScrollText);

  let status: WooTrace["status"];
  if (resonanceScore >= options.approveThreshold) {
    status = "approved";
  } else if (resonanceScore >= options.denyThreshold) {
    status = "warning";
  } else {
    status = "denied";
  }

  const output = JSON.stringify({ status, resonanceScore });
  const [inputHash, outputHash] = await Promise.all([
    hashString(input.sealedScrollText),
    hashString(output),
  ]);

  const trace: WooTrace = {
    traceId: generateTraceId(),
    requestId: input.requestId,
    scrollId: input.scrollId,
    actor: input.actor,
    wooVersion: WOO_VERSION,
    resonanceEngineVersion: RESONANCE_ENGINE_VERSION,
    status,
    resonanceScore,
    graphRunId: input.graphRunId,
    evidenceNodeIds: input.evidenceNodeIds,
    inputHash,
    outputHash,
    mode: input.mode,
    createdAt: new Date().toISOString(),
  };

  appendWooTrace(trace);
  return trace;
}

export { isValidSha256Hex, hashString };
