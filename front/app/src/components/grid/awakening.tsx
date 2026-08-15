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

const BOOT_NARRATION = [
  "Covenant core. Verifying sovereign runtime.",
  "Council of Eleven. Verifying the sealed advisory council.",
  "Neo four J soulprint. Verifying graph memory.",
  "Elemental quadrants. Verifying Grid readiness.",
  "Code conduit. Verifying process liveness.",
  "Woo oracle. Verifying sovereign voice.",
  "D C X trinity. Verifying mind, soul, and body.",
  "Grid perimeter. Verifying local relational authority.",
] as const;

async function fetchNarration(): Promise<NarrationPlan> {
  const response = await narrate([...BOOT_NARRATION], "ceremonial");
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
  const [frame, setFrame] = useState<BootFrame | null>(null);
  const [muted, setMuted] = useState(false);

  onCompleteRef.current = onComplete;

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

  useEffect(() => {
    if (frame?.phase === "COMPLETE") onCompleteRef.current?.();
  }, [frame?.phase]);

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
  const running = ["RUNNING", "HOLDING", "EXITING"].includes(phase);
  const preparing = phase === "IDLE";

  return (
    <section
      className={`awakening ${sigilStateClasses} ${className}`.trim()}
      data-phase={phase}
      data-exiting={phase === "EXITING" || phase === "COMPLETE"}
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
          <button
            className="awakening__begin"
            type="button"
            onClick={() => void conductorRef.current?.begin()}
          >
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
