import { useEffect, useState } from "react";

type ServiceStatus = "pending" | "online" | "degraded" | "failed";

type Service = {
  id: string;
  label: string;
  status: ServiceStatus;
  detail: string;
};

type Props = {
  onComplete: () => void;
  onProgress?: (pct: number) => void;
  onStep?: (step: number) => void;
};

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "";

const SERVICES: Array<Pick<Service, "id" | "label">> = [
  { id: "grid", label: "GRID CORE" },
  { id: "mindgraph", label: "MINDGRAPH" },
  { id: "dcx", label: "DCX TRINITY" },
  { id: "moscripts", label: "MOSCRIPTS" },
  { id: "voice", label: "WOO VOICE" },
  { id: "mcp", label: "MCP GATE" },
];

const STATUS_COLOR: Record<ServiceStatus, string> = {
  pending: "#78716c",
  online: "#4ade80",
  degraded: "#f59e0b",
  failed: "#ef4444",
};

const STATUS_LABEL: Record<ServiceStatus, string> = {
  pending: "...",
  online: "ONLINE",
  degraded: "PARTIAL",
  failed: "FAILED",
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
let bootVoiceQueue = Promise.resolve();

async function speakActivation(text: string): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/api/voice/speak`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mood: "ceremonial" }),
    });

    if (!res.ok) return;

    const data = await res.json();
    if (!data.audio_url) return;

    const src = data.audio_url.startsWith("/audio/")
      ? `${API_BASE}/api/voice${data.audio_url}`
      : data.audio_url;

    await new Promise<void>((resolve) => {
      const audio = new Audio(src);
      audio.onended = () => resolve();
      audio.onerror = () => resolve();
      audio.play().catch(() => resolve());
    });
  } catch {
    // Voice failure never blocks entry.
  }
}

function queueBootVoice(text: string): void {
  bootVoiceQueue = bootVoiceQueue.then(() => speakActivation(text));
}

async function checkServices(): Promise<Service[]> {
  const results: Service[] = SERVICES.map((service) => ({
    ...service,
    status: "pending",
    detail: "",
  }));

  try {
    const health = await fetch(`${API_BASE}/api/health`).then((res) => res.json());

    results[0].status =
      health.status === "alive" || health.status === "online" ? "online" : "failed";
    results[0].detail = results[0].status === "online" ? "api responding" : "api degraded";

    results[1].status = health.mindgraph ? "online" : "degraded";
    results[1].detail = health.mindgraph ? "bolt connected" : "graph unavailable";

    results[2].status = health.dcx ? "online" : "degraded";
    results[2].detail = health.dcx ? "trinity online" : "dcx partial";

    results[5].status = health.mcp?.online ? "online" : "degraded";
    results[5].detail = health.mcp?.online ? "gateway active" : "gateway offline";
  } catch {
    results[0].status = "failed";
    results[0].detail = "api unreachable";
  }

  try {
    const data = await fetch(`${API_BASE}/api/moscripts`).then((res) => res.json());
    const scripts = Array.isArray(data) ? data : (data.moscripts ?? []);

    results[3].status = scripts.length > 0 ? "online" : "degraded";
    results[3].detail =
      scripts.length > 0 ? `${scripts.length} scripts loaded` : "no scripts found";
  } catch {
    results[3].status = "failed";
    results[3].detail = "endpoint unreachable";
  }

  try {
    const voice = await fetch(`${API_BASE}/api/voice/health`).then((res) => res.json());

    results[4].status = voice.status === "healthy" ? "online" : "degraded";
    results[4].detail = voice.status === "healthy" ? "piper active" : (voice.status ?? "partial");
  } catch {
    results[4].status = "failed";
    results[4].detail = "voice unreachable";
  }

  return results;
}

function activationPhrase(services: Service[]): string {
  const failed = services.filter((service) => service.status === "failed").length;
  const degraded = services.filter((service) => service.status === "degraded").length;

  if (failed > 0) {
    return "Some systems did not respond. I govern what is present. The Grid holds.";
  }

  if (degraded > 0) {
    return "Partial signal confirmed. The covenant stands. The Grid may enter.";
  }

  return "All systems confirmed. The Grid is awake. Enter when ready.";
}

function serviceVoiceLine(service: Service): string {
  if (service.status === "online") {
    return `Loading ${service.label}. ${service.detail}. Confirmed.`;
  }

  if (service.status === "degraded") {
    return `Loading ${service.label}. ${service.detail}. Partial signal.`;
  }

  if (service.status === "failed") {
    return `Loading ${service.label}. ${service.detail}. No response.`;
  }

  return `Loading ${service.label}.`;
}

export function CeremonialBoot({ onComplete, onProgress, onStep }: Props) {
  const [services, setServices] = useState<Service[]>(
    SERVICES.map((service) => ({ ...service, status: "pending", detail: "" })),
  );
  const [revealed, setRevealed] = useState(0);
  const [phrase, setPhrase] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const results = await checkServices();
      if (cancelled) return;

      for (let index = 0; index < results.length; index += 1) {
        onStep?.(index);
        await sleep(520);
        if (cancelled) return;

        setServices((current) => {
          const next = [...current];
          next[index] = results[index];
          return next;
        });

        setRevealed(index + 1);
        onProgress?.(Math.round(((index + 1) / results.length) * 100));
        queueBootVoice(serviceVoiceLine(results[index]));
      }

      const finalPhrase = activationPhrase(results);
      onStep?.(results.length);
      setPhrase(finalPhrase);

      await sleep(250);
      if (cancelled) return;

      queueBootVoice(finalPhrase);
      if (!cancelled) onComplete();
    }

    void run();

    return () => {
      cancelled = true;
    };
  }, [onComplete, onProgress, onStep]);

  return (
    <div className="pointer-events-none absolute bottom-32 left-8 z-20 min-w-[300px] font-mono text-xs">
      <div className="mb-3 text-[10px] tracking-[0.34em] text-[#f6c45373]">
        SYSTEM BOOT SEQUENCE
      </div>

      {services.slice(0, revealed + 1).map((service) => (
        <div key={service.id} className="mb-1.5 flex items-start gap-3">
          <span style={{ color: STATUS_COLOR[service.status], minWidth: "52px" }}>
            {STATUS_LABEL[service.status]}
          </span>
          <span className="text-[#f6c453cc]">{service.label}</span>
          {service.detail && (
            <span className="mt-px text-[10px] text-[#f6c45359]">{service.detail}</span>
          )}
        </div>
      ))}

      {phrase && (
        <div
          className="mt-4 max-w-xs border-l pl-3 text-[11px] leading-relaxed text-[#f6c453d9]"
          style={{ borderColor: "rgba(246,196,83,0.25)" }}
        >
          <span className="mb-1 block text-[9px] tracking-[0.28em] text-[#f6c45373]">WOO-TAK</span>
          {phrase}
        </div>
      )}
    </div>
  );
}
