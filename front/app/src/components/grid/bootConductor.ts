import { GRID_SERVICES } from "@/config/gridServices";
import type {
  ConstitutionalBindingState,
  GridBuilderStatus,
  MindConduitSealStatus,
} from "@/lib/mind/builder.packet";

/**
 * WHAT CHANGED (bringing this file up to the same standard as
 * gridVoiceClient.ts / personalityClient.ts)
 *
 *   1. fetchNarration now receives the boot node labels and must use
 *      them as the narration request. Previously it was a zero-arg
 *      callback — this file had no influence over what text got
 *      narrated, so segments.length === nodeCount (the "perfect sync"
 *      branch of deriveNodeCues/deriveCeremonyProgress) was never
 *      guaranteed, only hoped for. Requesting exactly one segment per
 *      orb, by construction, is what actually gives sync a chance to
 *      be exact rather than approximate.
 *
 *      CALLER UPDATE REQUIRED: wherever this class is constructed,
 *      fetchNarration must change from `() => narrate(...)` to
 *      `(labels) => narrate(labels, "ceremonial")`.
 *
 *      Text source: node.label is the only established, real text
 *      this file has for each orb. If richer ceremonial phrasing
 *      already exists elsewhere, wire that in instead — this does not
 *      invent new copy.
 *
 *   2. Every network call now runs inside a bounded timeout that
 *      stays armed through body consumption. getJson() and the two
 *      probes that used raw fetch() (council, woo) previously had no
 *      timeout at all — a hung request wouldn't fail until the global
 *      GRACE_MS window closed after narration ended, riding a blunt
 *      global fallback instead of failing fast at a sensible budget.
 *
 *   3. The unexplained 0.82 constant in the no-segments cue fallback
 *      is now named (SYNTHETIC_CUE_SPREAD). Its original rationale
 *      isn't recorded anywhere I have access to — this names the
 *      number, it does not invent a justification for it.
 *
 * Boot phase machine, clocks, hold/exit timing, and node identities
 * are unchanged.
 */

export type SealState = "PENDING" | "ACTIVE" | "SEALED" | "DEGRADED";
export type BootPhase = "IDLE" | "ARMED" | "RUNNING" | "HOLDING" | "EXITING" | "COMPLETE";

export interface BootNode {
  id: string;
  label: string;
  probe: () => Promise<boolean>;
}

export interface NarrationSegment {
  text: string;
  startMs: number;
  endMs: number;
}

export interface NarrationPlan {
  audioUrl: string | null;
  audioMs: number;
  segments: NarrationSegment[];
}

export interface BootFrame {
  phase: BootPhase;
  progress: number;
  elapsedMs: number;
  totalMs: number;
  caption: string;
  captionIndex: number;
  nodes: SealState[];
  nodeLabels: string[];
  voiceLive: boolean;
  degradedCount: number;
}

export interface BootMindSurface {
  cognitive_binding: ConstitutionalBindingState;
  mind_conduit: "SEALED" | "PARTIAL";
  grid_mind_ready: boolean;
  gates: Record<string, string>;
}

export function projectMindStatus(seal: MindConduitSealStatus): BootMindSurface {
  return {
    cognitive_binding: seal.MODEL_BINDING,
    mind_conduit: seal.MIND_CONDUIT,
    grid_mind_ready: seal.GRID_MIND_READY,
    gates: {
      model_binding: seal.MODEL_BINDING,
      cypher_guard: seal.CYPHER_GUARD,
      provenance_filter: seal.PROVENANCE_FILTER,
      attestation_guard: seal.ATTESTATION_GUARD,
      invocation_surface_guard: seal.INVOCATION_SURFACE_GUARD,
      hostile_path_test: seal.HOSTILE_PATH_TEST,
    },
  };
}

export function projectGridMindStatus(builder: GridBuilderStatus): BootMindSurface {
  return projectMindStatus(builder.mindConduit);
}

export function isDcxMindBound(dcx: {
  state?: string;
  sealed?: boolean;
  binding?: string;
}): boolean {
  if (dcx.sealed === true && dcx.state === "SEALED" && dcx.binding === "SEALED") return true;
  return dcx.state === "LOADED";
}

const HOLD_MS = 900;
const EXIT_MS = 420;
const GRACE_MS = 6_000;
const BOOT_PROBE_TIMEOUT_MS = 10_000;

// Leaves trailing buffer before totalMs so the last orb's synthetic cue
// doesn't land exactly as the fallback clock ends. Only used when there
// is no live narration at all (segments.length === 0) — tune alongside
// HOLD_MS/silentFallbackMs if boot pacing changes.
const SYNTHETIC_CUE_SPREAD = 0.82;

interface Clock {
  readonly isAudio: boolean;
  start(): Promise<void>;
  nowMs(): number;
  totalMs(): number;
  ended(): boolean;
  stop(): void;
}

class AudioClock implements Clock {
  readonly isAudio = true;
  private readonly element: HTMLAudioElement;
  private done = false;

  constructor(
    url: string,
    private readonly fallbackMs: number,
  ) {
    this.element = new Audio(url);
    this.element.preload = "auto";
    this.element.volume = 0.44;
    this.element.addEventListener("ended", () => {
      this.done = true;
    });
  }

  async start() {
    await this.element.play();
  }

  nowMs() {
    return this.element.currentTime * 1_000;
  }

  totalMs() {
    const duration = this.element.duration;
    return Number.isFinite(duration) && duration > 0 ? duration * 1_000 : this.fallbackMs;
  }

  ended() {
    return this.done;
  }

  stop() {
    this.element.pause();
    this.element.removeAttribute("src");
    this.element.load();
  }

  setMuted(muted: boolean) {
    this.element.muted = muted;
  }
}

class SyntheticClock implements Clock {
  readonly isAudio = false;
  private startedAt = 0;

  constructor(private readonly durationMs: number) {}

  async start() {
    this.startedAt = performance.now();
  }

  nowMs() {
    return this.startedAt ? performance.now() - this.startedAt : 0;
  }

  totalMs() {
    return this.durationMs;
  }

  ended() {
    return this.nowMs() >= this.durationMs;
  }

  stop() {}
}

export function deriveNodeCues(
  segments: NarrationSegment[],
  nodeCount: number,
  totalMs: number,
): number[] {
  if (!segments.length) {
    return Array.from(
      { length: nodeCount },
      (_, index) => ((index + 1) / nodeCount) * totalMs * SYNTHETIC_CUE_SPREAD,
    );
  }

  // The canonical boot contract is one measured utterance per orb. The
  // utterance start is therefore the exact moment that orb's real probe
  // begins. No percentage or midpoint is inferred.
  if (segments.length === nodeCount) {
    return segments.map((segment) => segment.startMs);
  }

  const perSegment = Math.ceil(nodeCount / segments.length);
  const cues: number[] = [];
  for (const segment of segments) {
    const span = segment.endMs - segment.startMs;
    for (let index = 0; index < perSegment && cues.length < nodeCount; index += 1) {
      cues.push(segment.startMs + (span * (index + 1)) / (perSegment + 1));
    }
  }
  return cues.slice(0, nodeCount).sort((a, b) => a - b);
}

// The ring must hit each orb as a discrete sequence point in lockstep with
// the voice, not sweep continuously like a generic spinner. Progress is
// therefore a step function: it jumps to (index + 1) / nodeCount the exact
// instant a segment's measured utterance begins (the same moment that
// orb's real probe launches), and holds there until the next one fires.
export function deriveCeremonyProgress(
  elapsedMs: number,
  totalMs: number,
  segments: NarrationSegment[],
  nodeCount: number,
): number {
  if (!segments.length || segments.length !== nodeCount) {
    return totalMs ? Math.min(Math.max(elapsedMs / totalMs, 0), 1) : 0;
  }

  let hit = 0;
  for (const segment of segments) {
    if (elapsedMs >= segment.startMs) hit += 1;
  }
  return hit / nodeCount;
}

export class BootConductor {
  private clock: Clock | null = null;
  private plan: NarrationPlan | null = null;
  private cues: number[] = [];
  private results: Array<boolean | undefined>;
  private probeStarted: boolean[];
  private phase: BootPhase = "IDLE";
  private animationFrame = 0;
  private holdStartedAt = 0;
  private exitStartedAt = 0;
  private narrationEndedAt = 0;
  private listeners = new Set<(frame: BootFrame) => void>();

  constructor(
    private readonly nodes: BootNode[],
    private readonly fetchNarration: (labels: string[]) => Promise<NarrationPlan>,
    private readonly silentFallbackMs = 14_800,
  ) {
    this.results = nodes.map(() => undefined);
    this.probeStarted = nodes.map(() => false);
  }

  subscribe(listener: (frame: BootFrame) => void) {
    this.listeners.add(listener);
    listener(this.frame());
    return () => this.listeners.delete(listener);
  }

  async arm() {
    // narrate() owns its own bounded timeout (see gridVoiceClient's
    // NARRATE_TIMEOUT_MS) and never throws for the silent case — it
    // resolves with `audioUrl: null` plus real, already-timed segments.
    // A second timeout race here would just be two clocks disagreeing
    // about how long is too long. This catch is only a defensive net for
    // a fetchNarration implementation that isn't narrate() (e.g. tests).
    //
    // Requesting one label per node is what makes segments.length ===
    // nodeCount possible in the first place — see WHAT CHANGED §1.
    try {
      this.plan = await this.fetchNarration(this.nodes.map((node) => node.label));
    } catch {
      this.plan = { audioUrl: null, audioMs: this.silentFallbackMs, segments: [] };
    }

    this.clock = this.plan.audioUrl
      ? new AudioClock(this.plan.audioUrl, this.plan.audioMs)
      : new SyntheticClock(this.plan.audioMs || this.silentFallbackMs);

    this.cues = deriveNodeCues(
      this.plan.segments,
      this.nodes.length,
      this.plan.audioMs || this.silentFallbackMs,
    );
    this.phase = "ARMED";
    this.emit();
  }

  async begin() {
    if (!this.clock || this.phase !== "ARMED") return;

    try {
      await this.clock.start();
    } catch {
      this.clock.stop();
      this.clock = new SyntheticClock(this.silentFallbackMs);
      await this.clock.start();
    }

    this.phase = "RUNNING";
    this.launchDueProbes(0);
    this.emit();
    this.tick();
  }

  setMuted(muted: boolean) {
    if (this.clock instanceof AudioClock) this.clock.setMuted(muted);
  }

  destroy() {
    cancelAnimationFrame(this.animationFrame);
    this.clock?.stop();
    this.listeners.clear();
  }

  private tick = () => {
    if (!this.clock) return;

    if (this.phase === "RUNNING") {
      this.launchDueProbes(this.clock.nowMs());

      if (this.clock.ended() && !this.narrationEndedAt) {
        this.narrationEndedAt = performance.now();
      }

      const allSettled = this.results.every((result) => result !== undefined);
      const graceExpired = Boolean(
        this.narrationEndedAt && performance.now() - this.narrationEndedAt > GRACE_MS,
      );

      if (graceExpired) {
        this.results = this.results.map((result) => result ?? false);
      }

      if (this.clock.ended() && (allSettled || graceExpired)) {
        this.phase = "HOLDING";
        this.holdStartedAt = performance.now();
      }
    } else if (this.phase === "HOLDING" && performance.now() - this.holdStartedAt >= HOLD_MS) {
      this.phase = "EXITING";
      this.exitStartedAt = performance.now();
      this.emit();
    } else if (this.phase === "EXITING" && performance.now() - this.exitStartedAt >= EXIT_MS) {
      this.phase = "COMPLETE";
      this.emit();
      return;
    }

    this.emit();
    this.animationFrame = requestAnimationFrame(this.tick);
  };

  private nodeStates(elapsedMs: number): SealState[] {
    return this.nodes.map((_, index) => {
      if (elapsedMs < (this.cues[index] ?? Number.POSITIVE_INFINITY)) {
        return "PENDING";
      }
      const result = this.results[index];
      if (result === undefined) return "ACTIVE";
      return result ? "SEALED" : "DEGRADED";
    });
  }

  private launchDueProbes(elapsedMs: number) {
    this.nodes.forEach((node, index) => {
      if (this.probeStarted[index] || elapsedMs < (this.cues[index] ?? Number.POSITIVE_INFINITY)) {
        return;
      }

      this.probeStarted[index] = true;
      void node
        .probe()
        .then((ready) => {
          this.results[index] = ready;
          this.emit();
        })
        .catch(() => {
          this.results[index] = false;
          this.emit();
        });
    });
  }

  private captionAt(elapsedMs: number): [string, number] {
    const segments = this.plan?.segments ?? [];
    for (let index = segments.length - 1; index >= 0; index -= 1) {
      if (elapsedMs >= segments[index].startMs) {
        return [segments[index].text, index];
      }
    }
    return [segments[0]?.text ?? "", 0];
  }

  private frame(): BootFrame {
    const totalMs = this.clock?.totalMs() ?? this.silentFallbackMs;
    const elapsedMs = this.clock?.nowMs() ?? 0;
    const [caption, captionIndex] = this.captionAt(elapsedMs);
    const nodes = this.nodeStates(elapsedMs);
    const progress = deriveCeremonyProgress(
      elapsedMs,
      totalMs,
      this.plan?.segments ?? [],
      this.nodes.length,
    );
    return {
      phase: this.phase,
      progress,
      elapsedMs,
      totalMs,
      caption,
      captionIndex,
      nodes,
      nodeLabels: this.nodes.map((node) => node.label),
      voiceLive: Boolean(this.clock?.isAudio),
      degradedCount: nodes.filter((state) => state === "DEGRADED").length,
    };
  }

  private emit() {
    const frame = this.frame();
    this.listeners.forEach((listener) => listener(frame));
  }
}

/**
 * Runs one request/response transaction inside a single timeout budget.
 * The abort stays armed until the body has actually been consumed —
 * same pattern as gridVoiceClient/personalityClient. Every boot probe
 * below goes through this rather than a bare fetch(), so a hung
 * dependency fails at BOOT_PROBE_TIMEOUT_MS instead of riding the
 * global GRACE_MS window to resolution.
 */
async function fetchWithinBudget<T>(
  input: string,
  init: RequestInit,
  ms: number,
  consume: (response: Response) => Promise<T>,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    return await consume(response);
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      throw new Error(`Boot probe aborted after ${ms}ms: ${input}`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

// Every existing call site in this file already treats a non-ok status
// and a rejected promise identically — launchDueProbes() catches both
// into the same `results[index] = false`. So this throws uniformly on
// !response.ok rather than mixing "return false" and "throw" across
// probes; the observable outcome per node is unchanged.
function fetchJsonWithinBudget<T>(input: string, ms = BOOT_PROBE_TIMEOUT_MS): Promise<T> {
  return fetchWithinBudget(input, {}, ms, async (response) => {
    if (!response.ok) throw new Error(`${input} returned ${response.status}`);
    return (await response.json()) as T;
  });
}

async function getJson(path: string): Promise<Record<string, unknown>> {
  return fetchJsonWithinBudget<Record<string, unknown>>(`${GRID_SERVICES.api}${path}`);
}

async function gridStatus() {
  return await getJson("/api/status");
}

async function dependencies() {
  return await getJson("/health/dependencies");
}

export const GRID_BOOT_NODES: BootNode[] = [
  {
    id: "covenant",
    label: "COVENANT CORE",
    probe: async () => (await getJson("/health/ready")).status === "ready",
  },
  {
    id: "council",
    label: "COUNCIL OF ELEVEN",
    probe: async () => {
      const payload = await fetchJsonWithinBudget<{ advisors?: Record<string, unknown> }>(
        `${GRID_SERVICES.api}/api/semantic/advisors`,
      );
      return Object.keys(payload.advisors ?? {}).length > 0;
    },
  },
  {
    id: "neo4j",
    label: "NEO4J SOULPRINT",
    probe: async () => {
      const value = await dependencies();
      const dependencyMap = value.dependencies as Record<string, unknown> | undefined;
      const neo4j = dependencyMap?.neo4j as { status?: string } | undefined;
      return neo4j?.status === "ready";
    },
  },
  {
    id: "elements",
    label: "ELEMENTAL QUADRANTS",
    probe: async () => (await gridStatus()).grid === "ready",
  },
  {
    id: "conduit",
    label: "CODE CONDUIT",
    probe: async () => (await getJson("/health/live")).status === "alive",
  },
  {
    id: "woo",
    label: "WOO ORACLE",
    probe: async () => {
      const payload = await fetchJsonWithinBudget<{ status?: string }>(
        `${GRID_SERVICES.voice}/health`,
      );
      return payload.status === "healthy";
    },
  },
  {
    id: "dcx",
    label: "DCX TRINITY",
    probe: async () => {
      // `connected` only means Ollama answered. The orb must light for a
      // sealed trinity, not a reachable transport, so require the measured
      // seal state. /api/status never reports SEALED (validation lives in
      // the deep probe), so a LOADED trinity also satisfies this orb —
      // but PARTIAL/ABSENT/UNREACHABLE must not.
      const status = await gridStatus();
      const dcx = status.dcx as { state?: string; sealed?: boolean; binding?: string } | undefined;
      return dcx ? isDcxMindBound(dcx) : false;
    },
  },
  {
    id: "perimeter",
    label: "GRID PERIMETER",
    probe: async () => {
      const value = await dependencies();
      const dependencyMap = value.dependencies as Record<string, unknown> | undefined;
      const postgres = dependencyMap?.local_postgres as { status?: string } | undefined;
      return postgres?.status === "ready";
    },
  },
];
