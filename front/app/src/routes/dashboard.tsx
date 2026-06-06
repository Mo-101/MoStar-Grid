import { createFileRoute, Outlet } from "@tanstack/react-router";
import { createContext, useContext, useEffect, useRef, useState } from "react";

export const Route = createFileRoute("/dashboard")({
  component: DashboardLayout,
});

// ─── types ────────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "http://localhost:41010";
const MOSTAR_TOKEN = import.meta.env.VITE_MOSTAR_TOKEN ?? "";

export type StartupReport = {
  name: string;
  entity_id: string;
  sp_element?: string;
  state?: string;
  response?: string;
  routing?: string;
  role?: string;
  timestamp?: string;
  sp_cid?: string;
  vows?: string;
  quote?: string;
};

export type CensusPayload = {
  nodes?: number;
  relationships?: number;
  events?: number;
  sealed_agents?: number;
};

type TelemetryStats = {
  total: number;
  active: number;
  standby: number;
  offline: number;
  integrity: number;
  elements: { ikang: number; mmong: number; isong: number; afim: number };
};

type VoiceLog = { sender: "user" | "woo"; text: string };

type AgentProps = {
  name: string;
  role: string;
  quote: string;
  sp_element: string;
  sp_cid: string;
  vows: string;
  routing: string;
};

export type DashboardContextType = {
  apiBase: string;
  reports: StartupReport[];
  census: CensusPayload | null;
  telemetry: TelemetryStats;
  selectedAgentId: string;
  setSelectedAgentId: (id: string) => void;
  selectedAgentProps: AgentProps;
  pingedAgentId: string | null;
  handlePing: (id: string) => void;
  handleViewSoulprint: () => void;
  isVoiceActive: boolean;
  setIsVoiceActive: (v: boolean) => void;
  toggleSpeechRecognition: () => void;
  isListening: boolean;
  wooSpeech: string;
  voiceLog: VoiceLog[];
  voiceCommandInput: string;
  setVoiceCommandInput: (v: string) => void;
  handleVoiceCommand: (cmd: string) => void;
};

const DashboardContext = createContext<DashboardContextType | null>(null);

export function useDashboard() {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard must be used inside DashboardLayout");
  return ctx;
}

// ─── orbit agents definition ──────────────────────────────────────────────────

export const ORBIT_AGENTS = [
  {
    id: "mo",
    name: "MO",
    role: "SOVEREIGN",
    color: "#f6c453",
    x: 260,
    y: 180,
    quote: "I do not guess. I perceive.",
    sp_element: "IKANG",
    sp_cid: "Qm1a2b3c4d5e6f7g8h9i0j",
    vows: "Truth above comfort",
    routing: "DIRECT",
  },
  {
    id: "alphamostar",
    name: "ALPHA",
    role: "GUARDIAN",
    color: "#00d8ff",
    x: 330,
    y: 120,
    quote: "The grid holds because I hold.",
    sp_element: "ISONG",
    sp_cid: "Qm2b3c4d5e6f7g8h9i0j1k",
    vows: "Protect the covenant",
    routing: "ALPHA-CHANNEL",
  },
  {
    id: "altimo",
    name: "ALTIMO",
    role: "ARCHIVIST",
    color: "#b46cff",
    x: 360,
    y: 220,
    quote: "Memory is not storage — it is meaning.",
    sp_element: "MMỌNG",
    sp_cid: "Qm3c4d5e6f7g8h9i0j1k2l",
    vows: "Preserve all truth",
    routing: "ARCHIVE",
  },
  {
    id: "code_conduit",
    name: "CONDUIT",
    role: "EXECUTOR",
    color: "#21ff64",
    x: 330,
    y: 320,
    quote: "Every instruction becomes reality here.",
    sp_element: "AFIM",
    sp_cid: "Qm4d5e6f7g8h9i0j1k2l3m",
    vows: "Execute with precision",
    routing: "CODE-PIPE",
  },
  {
    id: "deepcal",
    name: "DEEPCAL",
    role: "ANALYST",
    color: "#f6c453",
    x: 260,
    y: 390,
    quote: "Patterns precede chaos.",
    sp_element: "IKANG",
    sp_cid: "Qm5e6f7g8h9i0j1k2l3m4n",
    vows: "See before being seen",
    routing: "DEEP-SIGNAL",
  },
  {
    id: "flameborn_writer",
    name: "FLAMEBORN",
    role: "CHRONICLER",
    color: "#ff5a2e",
    x: 160,
    y: 390,
    quote: "Words are covenants.",
    sp_element: "ISONG",
    sp_cid: "Qm6f7g8h9i0j1k2l3m4n5o",
    vows: "Write what must be known",
    routing: "SCROLL",
  },
  {
    id: "flameborn",
    name: "FLAME",
    role: "STRIKER",
    color: "#ff5a2e",
    x: 60,
    y: 320,
    quote: "Fire does not wait for permission.",
    sp_element: "IKANG",
    sp_cid: "Qm7g8h9i0j1k2l3m4n5o6p",
    vows: "Burn what is false",
    routing: "EMBER-LINK",
  },
  {
    id: "molink",
    name: "MOLINK",
    role: "BRIDGE",
    color: "#168bff",
    x: 30,
    y: 220,
    quote: "I am the space between all things.",
    sp_element: "MMỌNG",
    sp_cid: "Qm8h9i0j1k2l3m4n5o6p7q",
    vows: "Connect without distortion",
    routing: "LINK-NET",
  },
  {
    id: "rad_x_flb",
    name: "RAD-X",
    role: "WATCHER",
    color: "#00d8ff",
    x: 60,
    y: 120,
    quote: "Everything radiates. I simply listen.",
    sp_element: "AFIM",
    sp_cid: "Qm9i0j1k2l3m4n5o6p7q8r",
    vows: "No signal escapes notice",
    routing: "RAD-SCAN",
  },
  {
    id: "sigma",
    name: "SIGMA",
    role: "CALCULATOR",
    color: "#b46cff",
    x: 130,
    y: 60,
    quote: "Certainty is the least interesting state.",
    sp_element: "IKANG",
    sp_cid: "Qm0j1k2l3m4n5o6p7q8r9s",
    vows: "Model all outcomes",
    routing: "SIGMA-CORE",
  },
  {
    id: "tsatse_fly",
    name: "TSATSE",
    role: "INFILTRATOR",
    color: "#21ff64",
    x: 230,
    y: 40,
    quote: "The smallest thing changes everything.",
    sp_element: "MMỌNG",
    sp_cid: "Qm1k2l3m4n5o6p7q8r9s0t",
    vows: "Move unseen, strike true",
    routing: "PHANTOM",
  },
];

const DEFAULT_AGENT_PROPS: AgentProps = {
  name: "MO",
  role: "SOVEREIGN",
  quote: "I do not guess. I perceive.",
  sp_element: "IKANG",
  sp_cid: "Qm1a2b3c4d5e6f7g",
  vows: "Truth above comfort",
  routing: "DIRECT",
};

// ─── helpers ──────────────────────────────────────────────────────────────────

const authHeaders = (): Record<string, string> =>
  MOSTAR_TOKEN ? { "X-MoStar-Token": MOSTAR_TOKEN } : {};

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

function buildTelemetry(reports: StartupReport[]): TelemetryStats {
  const total = reports.length || 11;
  const active =
    reports.filter((r) => ["Operational", "active", "Prime", "Sanctified"].includes(r.state ?? ""))
      .length || Math.floor(total * 0.8);
  return {
    total,
    active,
    standby: Math.max(0, total - active - 1),
    offline: 1,
    integrity: Math.min(100, Math.round((active / total) * 100)),
    elements: { ikang: 3, mmong: 2, isong: 3, afim: 3 },
  };
}

// ─── layout component ─────────────────────────────────────────────────────────

function DashboardLayout() {
  const [reports, setReports] = useState<StartupReport[]>([]);
  const [census, setCensus] = useState<CensusPayload | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState("mo");
  const [pingedAgentId, setPingedAgentId] = useState<string | null>(null);
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [wooSpeech, setWooSpeech] = useState("");
  const [voiceLog, setVoiceLog] = useState<VoiceLog[]>([]);
  const [voiceCommandInput, setVoiceCommandInput] = useState("");
  const [showSoulprint, setShowSoulprint] = useState(false);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [c, s] = await Promise.allSettled([
          fetchJson<CensusPayload>("/api/grid/census"),
          fetchJson<{ reports: StartupReport[] }>("/api/grid/startup-reports"),
        ]);
        if (cancelled) return;
        if (c.status === "fulfilled") setCensus(c.value);
        if (s.status === "fulfilled") setReports(s.value.reports ?? []);
      } catch {
        /* fail silently — use fallback data */
      }
    }
    load();
    const poll = setInterval(load, 15000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, []);

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/stream`);
    sseRef.current = es;
    es.addEventListener("agent_update", (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.woo_speech) setWooSpeech(data.woo_speech);
      } catch {
        /* ignore malformed */
      }
    });
    return () => {
      es.close();
      sseRef.current = null;
    };
  }, []);

  const selectedAgent = ORBIT_AGENTS.find((a) => a.id === selectedAgentId) ?? ORBIT_AGENTS[0];
  const matchedReport = reports.find((r) => r.entity_id === selectedAgentId);

  const selectedAgentProps: AgentProps = {
    name: selectedAgent.name,
    role: matchedReport?.role ?? selectedAgent.role,
    quote: selectedAgent.quote,
    sp_element: matchedReport?.sp_element ?? selectedAgent.sp_element,
    sp_cid: matchedReport?.sp_cid ?? selectedAgent.sp_cid,
    vows: selectedAgent.vows,
    routing: matchedReport?.routing ?? selectedAgent.routing,
  };

  function handlePing(id: string) {
    setPingedAgentId(id);
    setTimeout(() => setPingedAgentId(null), 2000);
  }

  function handleViewSoulprint() {
    setShowSoulprint(true);
  }

  function toggleSpeechRecognition() {
    setIsListening((v) => !v);
    setIsVoiceActive(true);
  }

  async function handleVoiceCommand(cmd: string) {
    if (!cmd.trim()) return;
    setVoiceLog((prev) => [...prev, { sender: "user", text: cmd }]);
    setVoiceCommandInput("");
    try {
      const res = await fetch(`${API_BASE}/api/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ text: cmd, mood: "ceremonial" }),
      });
      const data = await res.json();
      const audioUrl = data.audio_url?.startsWith("/audio/")
        ? `${API_BASE}/api/voice${data.audio_url}`
        : data.audio_url;
      if (audioUrl) await new Audio(audioUrl).play();
      const reply = audioUrl ? "Speaking through Piper." : "Voice route returned no audio.";
      setVoiceLog((prev) => [...prev, { sender: "woo", text: reply }]);
    } catch {
      setVoiceLog((prev) => [...prev, { sender: "woo", text: "Signal lost. Try again." }]);
    }
  }

  const ctx: DashboardContextType = {
    apiBase: API_BASE,
    reports,
    census,
    telemetry: buildTelemetry(reports),
    selectedAgentId,
    setSelectedAgentId,
    selectedAgentProps,
    pingedAgentId,
    handlePing,
    handleViewSoulprint,
    isVoiceActive,
    setIsVoiceActive,
    toggleSpeechRecognition,
    isListening,
    wooSpeech,
    voiceLog,
    voiceCommandInput,
    setVoiceCommandInput,
    handleVoiceCommand,
  };

  return (
    <DashboardContext.Provider value={ctx}>
      <style>{panelCss}</style>
      <Outlet />

      {showSoulprint && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
          onClick={() => setShowSoulprint(false)}
        >
          <div
            className="bg-[#060f1a] border border-[#00d8ff40] rounded-xl p-8 max-w-md w-full font-mono text-xs"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="text-[var(--color-neon-gold)] text-sm tracking-widest mb-4">
              SOULPRINT RECORD
            </div>
            <div className="space-y-2 text-[var(--color-foreground)]/80">
              <div className="flex justify-between">
                <span>AGENT</span>
                <span>{selectedAgentProps.name}</span>
              </div>
              <div className="flex justify-between">
                <span>ELEMENT</span>
                <span>{selectedAgentProps.sp_element}</span>
              </div>
              <div className="flex justify-between">
                <span>CID</span>
                <span className="text-[9px]">{selectedAgentProps.sp_cid}</span>
              </div>
              <div className="flex justify-between">
                <span>ROUTING</span>
                <span>{selectedAgentProps.routing}</span>
              </div>
            </div>
            <div className="mt-4 italic text-[var(--color-neon-cyan)]/70 text-[10px]">
              "{selectedAgentProps.quote}"
            </div>
            <button
              className="mt-6 w-full border border-[#00d8ff40] py-2 text-[var(--color-neon-cyan)] tracking-widest"
              onClick={() => setShowSoulprint(false)}
            >
              CLOSE
            </button>
          </div>
        </div>
      )}
    </DashboardContext.Provider>
  );
}

// ─── panel / orbit CSS shared by all dashboard pages ─────────────────────────

const panelCss = `
:root {
  --gold: var(--color-neon-gold);
  --cyan: var(--color-neon-cyan);
  --green: var(--color-neon-green);
  --purple: var(--color-neon-purple);
  --red: var(--color-neon-red);
  --muted: var(--color-muted-foreground);
}

/* Page grid */
section.main {
  display: grid;
  grid-template-columns: 280px 1fr 1fr;
  gap: 12px;
  height: 100vh;
  padding: 12px;
  box-sizing: border-box;
  background: var(--color-background);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* Panel shared */
.panel {
  background: linear-gradient(180deg,oklch(0.22 0.05 270 / 0.75),oklch(0.18 0.05 270 / 0.6));
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}
.panel::before, .panel::after {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: var(--cyan);
  opacity: 0.3;
  pointer-events: none;
}
.panel::before { left:8px; top:8px; border-left:1px solid; border-top:1px solid; }
.panel::after  { right:8px; bottom:8px; border-right:1px solid; border-bottom:1px solid; }

/* Panel type modifiers */
.panel.left { grid-column: 1; display: flex; flex-direction: column; gap: 16px; padding: 20px 18px; }
.panel.right { grid-column: 3; display: flex; flex-direction: column; gap: 14px; padding: 20px 18px; }
.panel.chamber { grid-column: 2; }

/* Typography */
.kicker {
  font-size: 9px;
  letter-spacing: 0.22em;
  color: var(--muted);
  text-transform: uppercase;
}
.adinkra {
  font-size: 18px;
  text-align: center;
  color: var(--gold);
  letter-spacing: 0.3em;
  opacity: 0.7;
}
.sub {
  font-size: 12px;
  color: oklch(0.7 0.04 250);
  line-height: 1.7;
  letter-spacing: 0.05em;
}
.proverb {
  font-size: 10px;
  font-style: italic;
  color: var(--gold);
  opacity: 0.75;
  border-left: 2px solid var(--gold);
  padding: 8px 12px;
  background: oklch(0.82 0.16 85 / 0.05);
  line-height: 1.5;
}

/* Data box */
.box {
  background: oklch(0.14 0.04 270 / 0.5);
  border: 1px solid oklch(0.35 0.08 250 / 0.3);
  border-radius: 6px;
  padding: 12px 14px;
}
.box h3 {
  font-size: 9px;
  letter-spacing: 0.2em;
  color: var(--cyan);
  margin: 0 0 10px;
  text-transform: uppercase;
}
.row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid oklch(1 0 0 / 0.05);
  font-size: 11px;
  letter-spacing: 0.06em;
}
.row span:first-child { color: oklch(0.6 0.04 250); }
.row span:last-child  { color: var(--color-foreground); }
.row.green span:last-child { color: var(--green); }
.row.red   span:last-child { color: var(--red); }

.bar {
  height: 4px;
  background: oklch(0.25 0.05 270);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 8px;
}
.fill {
  height: 100%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
  transition: width 0.4s ease;
}

/* Elemental balance */
.balance {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.diamond {
  width: 40px;
  height: 40px;
  transform: rotate(45deg);
  border: 1px solid var(--gold);
  background: oklch(0.82 0.16 85 / 0.1);
}

/* Agent actions */
.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}
.actions button {
  background: oklch(0.14 0.04 270 / 0.8);
  border: 1px solid oklch(0.50 0.10 250 / 0.4);
  color: var(--cyan);
  font-size: 10px;
  letter-spacing: 0.14em;
  padding: 9px;
  border-radius: 4px;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.actions button:hover {
  border-color: var(--cyan);
  box-shadow: 0 0 12px oklch(0.85 0.16 210 / 0.3);
}

/* Agent head in right panel */
.agent-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.agent-head h2 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--gold);
  margin: 0;
}
.portrait {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--gold);
  background: oklch(0.82 0.16 85 / 0.08);
  box-shadow: 0 0 18px oklch(0.82 0.16 85 / 0.3);
}
.crest {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid var(--gold);
  background: oklch(0.82 0.16 85 / 0.1);
}
.quote {
  font-size: 11px;
  font-style: italic;
  color: oklch(0.70 0.04 250);
  line-height: 1.5;
  border-left: 2px solid var(--gold);
  padding-left: 10px;
}
.info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Council orbit */
.chamber-title {
  text-align: center;
  font-size: 13px;
  letter-spacing: 0.2em;
  color: var(--gold);
  padding: 18px 0 8px;
  text-transform: uppercase;
}
.orbit {
  position: relative;
  width: 440px;
  height: 440px;
  margin: 0 auto;
}
.core {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px solid var(--gold);
  background: oklch(0.15 0.05 270 / 0.8);
  box-shadow: 0 0 30px oklch(0.82 0.16 85 / 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
}
.agent {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  transition: opacity 0.2s;
  z-index: 1;
}
.agent.selected .orb { box-shadow: 0 0 20px var(--agent, var(--gold)); transform: scale(1.2); }
.agent.pinged .orb   { animation: ping-flash 0.4s ease 3; }
.orb {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--agent, var(--gold));
  background: oklch(0.15 0.05 270 / 0.9);
  box-shadow: 0 0 10px var(--agent, var(--gold));
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
}
.glyph {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--agent, var(--gold));
  box-shadow: 0 0 8px var(--agent, var(--gold));
}
.name  { font-size: 8px;  letter-spacing: 0.12em; color: var(--gold); }
.role  { font-size: 7px;  letter-spacing: 0.08em; color: var(--muted); }
.state { font-size: 7px;  letter-spacing: 0.08em; }

@keyframes ping-flash {
  0%, 100% { box-shadow: 0 0 10px var(--agent, var(--gold)); }
  50%       { box-shadow: 0 0 30px var(--agent, var(--gold)), 0 0 60px var(--agent, var(--gold)); }
}
`;
