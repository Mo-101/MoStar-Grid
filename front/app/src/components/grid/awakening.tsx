import { useEffect, useMemo, useRef, useState } from "react";
import sunVideo from "@/assets/sun5.mp4";
import { narrate } from "@/services/gridVoiceClient";
import {
  BootConductor,
  GRID_BOOT_NODES,
  type BootFrame,
  type NarrationPlan,
} from "./bootConductor";
import loadordRaw from "./loadord.svg?raw";
import "./awakening.css";

const BOOT_HANDOFF_MS = 30_000;
const BOOT_EXIT_MS = 420;

async function fetchNarration(labels: string[]): Promise<NarrationPlan> {
  const response = await narrate(labels, "ceremonial");
  return {
    audioUrl: response.audio_url,
    audioMs: response.audio_ms,
    segments: response.segments.map((segment) => ({
      text: segment.text,
      startMs: segment.start_ms,
      endMs: segment.end_ms,
    })),
  };
}

type BootLoaderProps = {
  className?: string;
  onComplete?: () => void;
};

export function AwakeningScreen({ className = "", onComplete }: BootLoaderProps) {
  const conductorRef = useRef<BootConductor | null>(null);
  const onCompleteRef = useRef(onComplete);
  const completedRef = useRef(false);
  const [frame, setFrame] = useState<BootFrame | null>(null);
  const [muted, setMuted] = useState(false);
  const [handoffExiting, setHandoffExiting] = useState(false);
  const [started, setStarted] = useState(false);

  onCompleteRef.current = onComplete;

  const completeOnce = () => {
    if (completedRef.current) return;
    completedRef.current = true;
    onCompleteRef.current?.();
  };

  // Arming only gathers narration and builds the clock; it must never start
  // the ceremony. The Grid waits to be woken deliberately — the operator
  // presses START AWAKENING, and nothing before that point is on a timer.
  useEffect(() => {
    const conductor = new BootConductor(GRID_BOOT_NODES, fetchNarration);
    conductorRef.current = conductor;
    const unsubscribe = conductor.subscribe(setFrame);
    void conductor.arm();
    return () => {
      unsubscribe();
      conductor.destroy();
      conductorRef.current = null;
    };
  }, []);

  // The 30s handoff window is measured from the operator's press, not from
  // mount. Arming latency (narration fetch) therefore never eats into the
  // visible ceremony.
  useEffect(() => {
    if (!started) return;
    const exitTimer = window.setTimeout(
      () => setHandoffExiting(true),
      BOOT_HANDOFF_MS - BOOT_EXIT_MS,
    );
    const handoffTimer = window.setTimeout(completeOnce, BOOT_HANDOFF_MS);
    return () => {
      window.clearTimeout(exitTimer);
      window.clearTimeout(handoffTimer);
    };
  }, [started]);

  const beginAwakening = () => {
    if (started) return;
    setStarted(true);
    void conductorRef.current?.begin();
  };

  const sigilStyle = useMemo(() => {
    const progress = frame?.progress ?? 0;
    return {
      "--boot-progress": String(progress),
      "--boot-dashoffset": String(100 - progress * 100),
    } as React.CSSProperties;
  }, [frame?.progress]);

  const sigilStateClasses = (frame?.nodes ?? [])
    .map((state, index) => `boot-node-${index}--${state.toLowerCase()}`)
    .join(" ");

  const phase = frame?.phase ?? "IDLE";
  const armed = phase === "ARMED";
  const running = ["RUNNING", "HOLDING", "EXITING", "COMPLETE"].includes(phase);
  const preparing = phase === "IDLE";

  return (
    <section
      className={`awakening ${sigilStateClasses} ${className}`.trim()}
      data-phase={phase}
      data-exiting={handoffExiting}
      aria-label="Grid initialization"
      aria-busy={phase !== "COMPLETE"}
    >
      <video
        src={sunVideo}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        className="awakening__sky"
      />
      <div className="awakening__veil" />

      <header className="awakening__header">
        <span>MOSTAR · COVENANT BOOT SEQUENCE</span>
        <strong>GRID AWAKENING</strong>
      </header>

      <div
        className="awakening__sigil"
        style={sigilStyle}
        aria-hidden="true"
        dangerouslySetInnerHTML={{ __html: loadordRaw }}
      />

      <div className="awakening__console">
        {preparing && (
          <p className="awakening__preparing" aria-live="polite">
            Gathering runtime proof and preparing the voice
          </p>
        )}

        {armed && (
          <button className="awakening__begin" type="button" onClick={beginAwakening} autoFocus>
            START AWAKENING
          </button>
        )}

        {running && (
          <>
            <p className="awakening__caption" key={frame?.captionIndex} aria-live="polite">
              {frame?.caption || "Grid awakening in silence"}
            </p>

            <div className="awakening__progress" aria-hidden="true">
              <span style={{ transform: `scaleX(${frame?.progress ?? 0})` }} />
            </div>

            <ol className="awakening__manifest">
              {frame?.nodeLabels.map((label, index) => {
                const state = frame.nodes[index];
                return (
                  <li key={label} data-state={state}>
                    <span className="awakening__glyph" aria-hidden="true" />
                    <span>{label}</span>
                    <strong>
                      {state === "PENDING"
                        ? "AWAITING PROOF"
                        : state === "ACTIVE"
                          ? "VERIFYING"
                          : state}
                    </strong>
                    {state === "DEGRADED" && <em>NO_RUNTIME_RIDGE</em>}
                  </li>
                );
              })}
            </ol>

            <div className="awakening__footer">
              {frame?.voiceLive ? (
                <button
                  className="awakening__sound"
                  type="button"
                  aria-pressed={muted}
                  onClick={() => {
                    const next = !muted;
                    setMuted(next);
                    conductorRef.current?.setMuted(next);
                  }}
                >
                  {muted ? "SOUND OFF" : "SOUND ON"}
                </button>
              ) : (
                <span>VOICE UNAVAILABLE · PROCEEDING IN SILENCE</span>
              )}
              {(frame?.degradedCount ?? 0) > 0 && (
                <span>{frame?.degradedCount} UNVERIFIED SUBSYSTEMS</span>
              )}
            </div>
          </>
        )}
      </div>
    </section>
  );
}
