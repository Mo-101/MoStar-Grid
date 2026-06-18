import { useEffect, useState } from "react";
import sunVideo from "@/assets/sun5.mp4";
import rawOrbSvg from "./loadord.svg?raw";
import "./awakening.css";

export type RollCallState = "idle" | "awakening" | "ready";

export type TelemetryEventType =
  | "woo.evaluation"
  | "truth.validation"
  | "agent.lifecycle"
  | "governor.cost"
  | "council.decision"
  | "registry.mutation"
  | "voice.synthesis"
  | "omni-symbolic"
  | "memory.append"
  | "ledger.write"
  | "sanctuary.activation"
  | "lingua.activation"
  | "moscripts.execute"
  | "runtime.execution";

export const NODE_EVENT_MAP = {
  "WOO ORACLE": ["woo.evaluation", "truth.validation"],
  "COVENANT CORE": ["agent.lifecycle", "governor.cost"],
  "COUNCIL OF THIRTEEN": ["council.decision", "registry.mutation"],
  "SOUL · MIND · BODY": ["voice.synthesis"],
  "IFÁ-CORPUS · AHP+TOPSIS+GREY": ["omni-symbolic"],
  "NEO4J MEMORY CODEX": ["memory.append", "ledger.write"],
  "SANCTUARY ACTIVATION": ["sanctuary.activation", "voice.synthesis"],
  "IBIBIO LINGUA": ["lingua.activation", "voice.synthesis"],
  MoScripts: ["moscripts.execute", "runtime.execution"],
} as const satisfies Record<string, readonly TelemetryEventType[]>;

const NODES: { label: keyof typeof NODE_EVENT_MAP; color: string }[] = [
  { label: "WOO ORACLE", color: "#ff5a2e" },
  { label: "COVENANT CORE", color: "#9be15d" },
  { label: "COUNCIL OF THIRTEEN", color: "#00d8ff" },
  { label: "SOUL · MIND · BODY", color: "#f6c453" },
  { label: "IFÁ-CORPUS · AHP+TOPSIS+GREY", color: "#3b82f6" },
  { label: "NEO4J MEMORY CODEX", color: "#00ff88" },
  { label: "SANCTUARY ACTIVATION", color: "#168bff" },
  { label: "IBIBIO LINGUA", color: "#6cd9ff" },
  { label: "MoScripts", color: "#ff3b6b" },
];

let ritualHasRun = false;

function AwakeningOrb({
  state,
  progress,
  activeStep = 0,
}: {
  state: RollCallState;
  progress: number;
  activeStep?: number;
}) {
  const glow =
    state === "ready" ? "#dfee0a" : state === "awakening" ? "#03f079" : "#eb0808";

  return (
    <div className="absolute inset-x-0 top-[20%] z-[5] flex justify-center">
      <div className="relative h-[240px] w-[240px]">
        <div
          className="orb-svg relative h-full w-full"
          style={{
            filter:
              state === "ready"
                ? "drop-shadow(0 0 42px #ff1e00)"
                : "drop-shadow(0 0 30px rgba(246,196,83,0.58))",
          }}
          dangerouslySetInnerHTML={{ __html: rawOrbSvg }}
        />

        {NODES.map((node, index) => {
          const lit = index < activeStep || state === "ready";
          const active = index === activeStep && state === "awakening";
          const angle = (index / NODES.length) * Math.PI * 2 - Math.PI / 2;
          const radius = 122;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;

          return (
            <span
              key={node.label}
              className={[
                "absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border transition-all duration-500",
                active ? "animate-blink" : "",
              ].join(" ")}
              style={{
                transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                borderColor: node.color,
                background: lit || active ? node.color : "transparent",
                boxShadow: lit || active ? `0 0 16px ${node.color}` : "none",
                opacity: lit || active ? 1 : 0.35,
              }}
              aria-hidden="true"
            />
          );
        })}

        <div
          className="absolute left-1/2 top-[72%] -translate-x-1/2 font-mono text-[11px] tracking-[0.42em]"
          style={{ color: glow, textShadow: `0 0 12px ${glow}` }}
        >
          {state === "ready"
            ? "GRID ONLINE"
            : state === "awakening"
              ? `${progress}%`
              : "SEALED"}
        </div>
      </div>
    </div>
  );
}

export function AwakeningScreen({
  onComplete,
  stepDuration = 1620,
}: {
  onComplete?: () => void;
  stepDuration?: number;
}) {
  const [state, setState] = useState<RollCallState>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    if (ritualHasRun) {
      setProgress(100);
      setActiveStep(NODES.length);
      setState("ready");
      onComplete?.();
      return;
    }
    ritualHasRun = true;

    const timer = window.setTimeout(() => setState("awakening"), 560);
    return () => window.clearTimeout(timer);
  }, [onComplete]);

  useEffect(() => {
    if (state !== "awakening") return;

    const total = NODES.length;
    const start = performance.now();
    const totalDuration = stepDuration * total;
    let raf = 0;

    const tick = (now: number) => {
      const elapsed = now - start;
      const pct = Math.min(100, Math.round((elapsed / totalDuration) * 100));
      const step = Math.min(total, Math.floor(elapsed / stepDuration));

      setProgress(pct);
      setActiveStep(step);

      if (elapsed < totalDuration) {
        raf = requestAnimationFrame(tick);
      } else {
        setProgress(100);
        setActiveStep(total);
        setState("ready");
        window.setTimeout(() => setExiting(true), 420);
        window.setTimeout(() => onComplete?.(), 1150);
      }
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [onComplete, state, stepDuration]);

  return (
    <div
      className={[
        "fixed inset-0 z-[100] overflow-hidden bg-background transition-[opacity,filter] duration-700 ease-out",
        exiting ? "opacity-0 blur-sm" : "opacity-100 blur-0",
      ].join(" ")}
    >
      <video
        src={sunVideo}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        className="absolute inset-0 h-full w-full object-cover opacity-75"
      />
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(52% 48% at 50% 48%, oklch(0.10 0.03 270 / 0.18) 0%, oklch(0.10 0.04 270 / 0.72) 70%, oklch(0.08 0.04 270 / 0.94) 100%)",
        }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,transparent_0,transparent_38%,oklch(0.06_0.03_270/0.58)_78%)]" />

      <div className="absolute inset-x-0 top-10 z-[5] flex flex-col items-center gap-2 px-5 text-center">
        <div className="max-sm:tracking-[0.24em] text-[10px] tracking-[0.5em] text-[var(--color-neon-cyan)]">
          MOSTAR · COVENANT BOOT SEQUENCE
        </div>
        <div className="neon-text-gold max-sm:text-lg max-sm:tracking-[0.2em] text-2xl tracking-[0.4em]">
          GRID AWAKENING
        </div>
      </div>

      <AwakeningOrb state={state} progress={progress} activeStep={activeStep} />

      <div className="absolute inset-x-0 bottom-12 z-[5] mx-auto flex max-w-[680px] flex-col items-center gap-3 px-6">
        <div className="h-[3px] w-full overflow-hidden rounded-full border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.10_0.05_270/0.7)]">
          <div
            className="h-full rounded-full transition-[width] duration-150"
            style={{
              width: `${progress}%`,
              background:
                "linear-gradient(90deg, var(--color-neon-cyan), var(--color-neon-gold))",
              boxShadow: "0 0 18px var(--color-neon-gold)",
            }}
          />
        </div>

        <div className="grid w-full grid-cols-1 gap-1 font-mono text-[11px] sm:grid-cols-2">
          {NODES.map((node, index) => {
            const done = index < activeStep || state === "ready";
            const active = index === activeStep && state === "awakening";

            return (
              <div
                key={node.label}
                className={[
                  "flex h-7 items-center gap-3 rounded-md border px-3 transition-all duration-300",
                  done || active
                    ? "border-[color-mix(in_oklab,var(--color-neon-cyan)_28%,transparent)] bg-[oklch(0.12_0.04_270/0.64)] opacity-100"
                    : "border-transparent bg-transparent opacity-35",
                ].join(" ")}
              >
                <span
                  className={active ? "animate-blink" : ""}
                  style={{ color: node.color, textShadow: `0 0 8px ${node.color}` }}
                >
                  {done ? "●" : "○"}
                </span>
                <span style={{ color: done ? "rgba(219,232,246,0.9)" : node.color }}>
                  {node.label}
                </span>
                <span className="ml-auto text-[9px] tracking-[0.18em] text-muted-foreground">
                  {done ? "SEALED" : active ? "BINDING" : "WAIT"}
                </span>
              </div>
            );
          })}
        </div>

        <div className="max-sm:tracking-[0.16em] text-center text-[10px] tracking-[0.36em] text-muted-foreground">
          HONOR FIRST · STRIKE FAST · SEE AHEAD · STAY UNTOUCHABLE
        </div>
      </div>
    </div>
  );
}
