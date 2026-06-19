import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import sunVideo from "@/assets/sun5.mp4";
import loadord from "./loadord.svg";
import { speak } from "@/services/gridVoiceClient";
import "./awakening.css";

const BOOT_NARRATION =
  "Covenant boot sequence initiated. Sealing the council. The grid is awakening.";

export type BootState = "idle" | "awakening" | "ready";

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

const NODES = [
  { label: "COVENANT CORE", color: "#eba709" },
  { label: "COUNCIL OF ELEVEN", color: "#f53905" },
  { label: "NEO4J SOULPRINT", color: "#04b9da" },
  { label: "ELEMENTAL QUADRANTS", color: "#7a06f7" },
  { label: "CODE CONDUIT", color: "#145e06" },
  { label: "WOO ORACLE", color: "#064fec" },
  { label: "DCX TRINITY", color: "#f80441" },
  { label: "GRID PERIMETER", color: "#03eea7" },
];

type BootLoaderProps = {
  /** Put loadord.svg inside your public folder. */
  src?: string;
  className?: string;
  showReplay?: boolean;
  onComplete?: () => void;
};

const NODE_COUNT = 8;
const STEP_MS = 1_000;
const COMPLETE_MS = 9_000;
const EXIT_FADE_MS = 900;

export function AwakeningScreen({
  src = loadord,
  className = "",
  showReplay = false,
  onComplete,
}: BootLoaderProps) {
  const [cycle, setCycle] = useState(0);
  const [status, setStatus] = useState("Initializing ring");
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [bootState, setBootState] = useState<BootState>("awakening");
  const [isExiting, setIsExiting] = useState(false);
  const timeoutIds = useRef<number[]>([]);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animatedSrc = useMemo(
    () => `${src}${src.includes("?") ? "&" : "?"}cycle=${cycle}`,
    [src, cycle],
  );

  const clearTimers = useCallback(() => {
    timeoutIds.current.forEach(window.clearTimeout);
    timeoutIds.current = [];
  }, []);

  useEffect(() => {
    clearTimers();
    setStatus("Initializing ring");
    setActiveStep(0);
    setProgress(0);
    setBootState("awakening");
    setIsExiting(false);

    for (let index = 0; index < NODE_COUNT; index += 1) {
      timeoutIds.current.push(
        window.setTimeout(() => {
          setStatus(`Node ${String(index + 1).padStart(2, "0")} online`);
          setActiveStep(index + 1);
          setProgress(Math.round(((index + 1) / NODE_COUNT) * 90));
        }, index * STEP_MS + 350),
      );
    }

    timeoutIds.current.push(
      window.setTimeout(() => {
        setStatus("Core ignition");
        setProgress(96);
      }, 8_100),
    );

    timeoutIds.current.push(
      window.setTimeout(() => {
        setStatus("Grid online");
        setProgress(100);
        setBootState("ready");
        setIsExiting(true);
        timeoutIds.current.push(
          window.setTimeout(() => {
            onCompleteRef.current?.();
          }, EXIT_FADE_MS),
        );
      }, COMPLETE_MS),
    );

    return clearTimers;
    // `cycle` is the only intentional restart trigger — onComplete is read via
    // a ref so a fresh inline callback from the parent doesn't reset the
    // sequence (which previously made the SVG, locked to its own one-shot
    // CSS timeline via `src`, look "done" instantly while the status text
    // kept restarting).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clearTimers, cycle]);

  const replay = useCallback(() => {
    setCycle((current) => current + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await speak({ text: BOOT_NARRATION });
        if (cancelled || !res.audio_url) return;
        const audio = audioRef.current;
        if (!audio) return;
        audio.src = res.audio_url;
        await audio.play().catch(() => {
          // Autoplay blocked without prior user interaction — boot continues silently.
        });
      } catch {
        // Voice service unreachable — boot continues silently.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [cycle]);

  return (
    <div
      className={[
        "boot-screen fixed inset-0 z-[100] overflow-hidden bg-background",
        isExiting ? "boot-screen--exit" : "",
        className,
      ].join(" ")}
    >
      <audio ref={audioRef} className="hidden" />
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

      <div className="absolute inset-x-0 top-10 z-[50] flex flex-col items-center gap-2 px-5 text-center">
        <div className="text-[10px] tracking-[0.5em] text-[var(--color-neon-cyan)] max-sm:tracking-[0.24em]">
          MOSTAR · COVENANT BOOT SEQUENCE
        </div>
        <div className="text-2xl tracking-[0.4em] neon-text-gold max-sm:text-lg max-sm:tracking-[0.2em]">
          GRID AWAKENING
        </div>
      </div>

      <div className="absolute inset-x-0 top-[15vh] z-[10] flex flex-col items-center gap-5 px-5 max-sm:top-[13vh]">
        <img
          className="boot-image"
          src={animatedSrc}
          width="404"
          height="410"
          alt="Sequential MoStar ring boot sequence"
        />

        {showReplay && bootState === "ready" && (
          <button
            type="button"
            onClick={replay}
            className="rounded-md border border-[var(--color-neon-cyan)]/30 bg-black/30 px-4 py-2 text-[10px] tracking-[0.3em] text-[var(--color-neon-cyan)] hover:bg-white/5"
          >
            REPLAY BOOT
          </button>
        )}
      </div>

      <div className="absolute inset-x-0 bottom-10 z-[20] mx-auto flex max-w-[760px] flex-col items-center gap-3 px-6 max-sm:bottom-6">
        <p
          className="font-mono text-xs tracking-[0.4em] text-[var(--color-neon-cyan)] max-sm:tracking-[0.2em]"
          aria-live="polite"
        >
          {status}
        </p>

        <div className="h-[3px] w-full overflow-hidden rounded-full border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.10_0.05_270/0.7)]">
          <div
            className="h-full transition-all duration-500 ease-out"
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
            const done = index < activeStep || bootState === "ready";
            const active = index === activeStep && bootState === "awakening";
            return (
              <div
                key={node.label}
                className={[
                  "flex h-7 items-center gap-3 rounded-md border px-3 transition-all duration-300",
                  done || active
                    ? "border-[color-mix(in_oklab,var(--color-neon-cyan)_28%,transparent)] bg-[oklch(0.12_0.04_270/0.64)] opacity-100"
                    : "border-[color-mix(in_oklab,var(--color-neon-cyan)_14%,transparent)] bg-[oklch(0.08_0.03_270/0.34)] opacity-35",
                ].join(" ")}
              >
                <span
                  className={active ? "animate-blink" : ""}
                  style={{ color: node.color, textShadow: `0 0 8px ${node.color}` }}
                >
                  {done ? "●" : "○"}
                </span>

                <span
                  className="truncate"
                  style={{
                    color: done || active ? "rgba(219,232,246,0.92)" : node.color,
                  }}
                >
                  {node.label}
                </span>

                <span className="ml-auto shrink-0 text-[9px] tracking-[0.18em] text-muted-foreground">
                  {done ? "SEALED" : active ? "BINDING" : "WAIT"}
                </span>
              </div>
            );
          })}
        </div>

        <div className="text-center text-[10px] tracking-[0.36em] text-muted-foreground max-sm:tracking-[0.16em]">
          HONOR FIRST · STRIKE FAST · SEE AHEAD · STAY UNTOUCHABLE
        </div>
      </div>
    </div>
  );
}
