import { useCallback, useState } from "react";
import { AwakeningOrb } from "./AwakeningOrb";
import { CeremonialBoot } from "./CeremonialBoot";
import { EnterGridButton } from "./EnterGridButton";
import { TelemetryRing } from "./TelemetryRing";
import { VideoBackground } from "./VideoBackground";

type BootState = "idle" | "awakening" | "ready";

export function Awakening() {
  const [state, setState]         = useState<BootState>("idle");
  const [progress, setProgress]   = useState(0);
  const [activeStep, setActiveStep] = useState(-1);

  const handleBegin = useCallback(async () => {
    setState("awakening");
    setProgress(0);
    try {
      const res = await fetch("http://localhost:41071/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "Grid boot sequence initiated.", mood: "ceremonial" }),
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => URL.revokeObjectURL(url);
        audio.play().catch(() => {});
      }
    } catch { /* voice failure never blocks boot */ }
  }, []);

  const handleBootComplete = useCallback(() => {
    setProgress(100);
    setState("ready");
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden bg-[#050608]">
      <VideoBackground progress={progress} />
      <div
        className="pointer-events-none absolute inset-0 z-[2]"
        style={{ background: "linear-gradient(180deg, rgba(5,6,8,0.42) 0%, rgba(5,6,8,0.10) 28%, rgba(5,6,8,0.58) 100%)" }}
      />
      <AwakeningOrb state={state} progress={progress} activeStep={activeStep} />
      {state !== "awakening" && <TelemetryRing />}
      {state === "awakening" && (
        <CeremonialBoot onComplete={handleBootComplete} onProgress={setProgress} onStep={setActiveStep} />
      )}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[10] flex flex-col items-center px-5 pb-6">
        <div className="font-mono text-3xl font-extrabold tracking-[0.36em]" style={{ color: "#f6c453", textShadow: "0 0 24px rgba(246,196,83,0.45)" }}>
          MOSTAR
        </div>
        <div className="mt-1 font-mono text-[11px] tracking-[0.35em] text-[#00d8ff]">
          {state === "idle" ? "WOO ORCHESTRATION · SOVEREIGN BOOT" : state === "awakening" ? "WOO ORCHESTRATION · AWAKENING" : "WOO ORCHESTRATION · GRID ONLINE"}
        </div>
        <div className="mt-6 w-[min(760px,88vw)]">
          <div className="mb-2 flex justify-between font-mono text-[10px] tracking-[0.24em] text-[#f6c453aa]">
            <span>{state === "awakening" ? "AWAKENING" : state === "ready" ? "READY" : "STANDING BY"}</span>
            <span>{progress.toString().padStart(3, "0")}%</span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-[#f6c4531f]">
            <div className="h-full rounded-full transition-all duration-500" style={{ width: `${progress}%`, background: "linear-gradient(90deg, #f6c453, #00d8ff)", boxShadow: "0 0 18px rgba(0,216,255,0.55)" }} />
          </div>
        </div>
        <div className="pointer-events-auto mt-6">
          <EnterGridButton state={state} onBegin={handleBegin} />
        </div>
      </div>
    </div>
  );
}
