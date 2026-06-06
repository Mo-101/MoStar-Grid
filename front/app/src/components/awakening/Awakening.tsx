import { useCallback, useState } from "react";
import { AwakeningOrb } from "./AwakeningOrb";
import { EnterGridButton } from "./EnterGridButton";
import { TelemetryRing } from "./TelemetryRing";
import { VideoBackground } from "./VideoBackground";

type RollCallState = "idle" | "awakening" | "ready";

type StartupReport = {
  name?: string;
  entity_id?: string;
  role?: string;
  state?: string;
  response?: string;
  voiceLine?: string;
  vows?: string;
};

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "";

function lineFor(report: StartupReport): string {
  const name = report.name ?? report.entity_id ?? "Grid entity";
  const role = report.role ? ` ${report.role}.` : "";
  const text = report.voiceLine || report.response || report.vows;
  return text ? `${name} reporting.${role} ${text}` : `${name} reporting.${role} Standing by.`;
}

async function speak(text: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/voice/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, mood: "ceremonial" }),
  });

  if (!res.ok) {
    throw new Error(`/api/voice/speak returned ${res.status}`);
  }

  const data = await res.json();
  if (!data.audio_url) return;

  const src = data.audio_url.startsWith("/audio/")
    ? `${API_BASE}/api/voice${data.audio_url}`
    : data.audio_url;

  await new Promise<void>((resolve) => {
    const audio = new Audio(src);
    audio.onended = () => resolve();
    audio.onerror = () => resolve();

    const playback = audio.play();
    if (playback) playback.catch(() => resolve());
  });
}

export function Awakening() {
  const [state, setState] = useState<RollCallState>("idle");
  const [progress, setProgress] = useState(0);
  const [activeStep, setActiveStep] = useState(-1);
  const [feed, setFeed] = useState<string[]>(["INITIALIZING GRID SENTINELS..."]);

  const runRollCall = useCallback(async () => {
    if (state === "awakening") return;

    setState("awakening");
    setProgress(1);
    setActiveStep(0);
    setFeed(["ROLL CALL REQUESTED"]);

    try {
      const res = await fetch(`${API_BASE}/api/grid/startup-reports`);
      if (!res.ok) {
        throw new Error(`/api/grid/startup-reports returned ${res.status}`);
      }

      const data = await res.json();
      const reports: StartupReport[] = Array.isArray(data.reports) ? data.reports : [];
      if (reports.length === 0) {
        throw new Error("startup reports returned no agents");
      }

      for (let index = 0; index < reports.length; index += 1) {
        const report = reports[index];
        const name = report.name ?? report.entity_id ?? `AGENT ${index + 1}`;
        const line = lineFor(report);

        setActiveStep(index % 8);
        setFeed((current) => [...current.slice(-7), `[${name.toUpperCase()}] ${line}`]);

        await speak(line);
        setProgress(Math.round(((index + 1) / reports.length) * 100));
      }

      setActiveStep(7);
      setProgress(100);
      setState("ready");
      setFeed((current) => [...current.slice(-7), "[GRID] ROLL CALL COMPLETE"]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "roll call failed";
      setState("idle");
      setProgress(0);
      setActiveStep(-1);
      setFeed((current) => [...current.slice(-7), `[ERROR] ${message}`]);
    }
  }, [state]);

  return (
    <div className="fixed inset-0 overflow-hidden bg-[#050608]">
      <VideoBackground progress={progress} />

      <div
        className="pointer-events-none absolute inset-0 z-[2]"
        style={{
          background:
            "linear-gradient(180deg, rgba(5,6,8,0.42) 0%, rgba(5,6,8,0.10) 28%, rgba(5,6,8,0.58) 100%)",
        }}
      />

      <AwakeningOrb state={state} progress={progress} activeStep={activeStep} />

      {state !== "awakening" && <TelemetryRing />}

      <div className="pointer-events-none absolute bottom-32 left-8 z-[8] max-w-[min(520px,calc(100vw-4rem))] font-mono">
        <div className="mb-3 text-[10px] tracking-[0.34em] text-[#f6c45399]">AWAKENING LOG</div>
        <div className="space-y-1 text-[11px] leading-relaxed text-[#f6c453cc]">
          {feed.map((line, index) => (
            <div key={`${line}-${index}`}>{line}</div>
          ))}
        </div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[10] flex flex-col items-center px-5 pb-6">
        <div
          className="font-mono text-3xl font-extrabold tracking-[0.36em]"
          style={{ color: "#f6c453", textShadow: "0 0 24px rgba(246,196,83,0.45)" }}
        >
          MOSTAR
        </div>
        <div className="mt-1 font-mono text-[11px] tracking-[0.35em] text-[#00d8ff]">
          GRID ROLL CALL
        </div>

        <div className="mt-6 w-[min(760px,88vw)]">
          <div className="mb-2 flex justify-between font-mono text-[10px] tracking-[0.24em] text-[#f6c453aa]">
            <span>
              {state === "awakening" ? "AWAKENING" : state === "ready" ? "READY" : "STANDING BY"}
            </span>
            <span>{progress.toString().padStart(3, "0")}%</span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-[#f6c4531f]">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: "linear-gradient(90deg, #f6c453, #00d8ff)",
                boxShadow: "0 0 18px rgba(0,216,255,0.55)",
              }}
            />
          </div>
        </div>

        <div className="pointer-events-auto mt-6">
          <EnterGridButton state={state} onBegin={runRollCall} />
        </div>
      </div>
    </div>
  );
}
