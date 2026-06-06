import { useEffect, useState } from "react";

type Agent = {
  name: string;
  insignia: string;
  state: string;
  routing: string;
  sp_element: string | string[];
};

const FALLBACK_NODES: Agent[] = [
  { name: "Mo",           insignia: "👑", state: "Prime",            routing: "observe", sp_element: "Ikang" },
  { name: "DeepCAL",      insignia: "🧠", state: "Operational",      routing: "active",  sp_element: "Mmọng" },
  { name: "Sigma",        insignia: "⚖️", state: "Operational",      routing: "observe", sp_element: "Afim"  },
  { name: "Woo-Tak",      insignia: "⚔️", state: "Sanctified",       routing: "observe", sp_element: "Ikang" },
  { name: "Altimo",       insignia: "🛡️", state: "Operational",      routing: "observe", sp_element: "Isong" },
  { name: "Flameborn",    insignia: "🔥", state: "Dormant (ready)",  routing: "observe", sp_element: "Ikang" },
  { name: "RAD-X-FLB",   insignia: "🦟", state: "Operational",      routing: "observe", sp_element: "Isong" },
  { name: "Code Conduit", insignia: "⚙️", state: "Operational",      routing: "observe", sp_element: "Ikang" },
];

function routingColor(routing: string): string {
  if (routing === "active")  return "oklch(0.85 0.22 200)"; // cyan — actively routing
  if (routing === "observe") return "oklch(0.85 0.20 75)";  // gold — observing
  return "oklch(0.55 0.05 0)";                              // dim — unknown
}

function stateOpacity(state: string): number {
  const s = state.toLowerCase();
  if (s.includes("dormant")) return 0.45;
  if (s.includes("ready"))   return 0.72;
  return 1.0;
}

function shortLabel(name: string): string {
  const first = name.split(/[\s\-_(]/)[0].toUpperCase();
  return first.length > 9 ? first.slice(0, 9) : first;
}

export function TelemetryRing() {
  const [agents, setAgents] = useState<Agent[]>(FALLBACK_NODES);

  useEffect(() => {
    fetch("/api/grid/startup-reports")
      .then((r) => r.ok ? r.json() : Promise.reject())
      .then((d) => {
        const reports: Agent[] = d.reports ?? [];
        if (reports.length > 0) setAgents(reports);
      })
      .catch(() => { /* keep fallback */ });
  }, []);

  const radius = 260;
  const count  = agents.length;

  return (
    <div className="pointer-events-none absolute inset-0 z-[4] flex items-center justify-center">
      <div
        className="relative"
        style={{
          width:  radius * 2,
          height: radius * 2,
          animation: "grid-rotate 240s linear infinite",
        }}
      >
        {agents.map((agent, i) => {
          const angle = (i / count) * Math.PI * 2;
          const x     = radius + Math.cos(angle) * radius;
          const y     = radius + Math.sin(angle) * radius;
          const color = routingColor(agent.routing);
          const opacity = stateOpacity(agent.state);

          return (
            <div
              key={agent.name}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{ left: x, top: y }}
            >
              <div
                style={{
                  animation: "grid-rotate-reverse 240s linear infinite",
                  opacity,
                }}
                className="flex flex-col items-center gap-1"
              >
                <div
                  className="h-2 w-2 rounded-full"
                  style={{
                    background: color,
                    boxShadow: `0 0 8px 2px ${color}`,
                  }}
                />
                <span
                  className="font-mono text-[9px] tracking-[0.2em]"
                  style={{ color }}
                >
                  {shortLabel(agent.name)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
