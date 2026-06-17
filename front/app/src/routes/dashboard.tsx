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
      // Route through LLM voice agent first for intelligent response
      let speechText = cmd;
      try {
        const agentRes = await fetch(`${API_BASE}/api/voice-command`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders() },
          body: JSON.stringify({ text: cmd }),
        });
        if (agentRes.ok) {
          const agentData = await agentRes.json();
          if (agentData.speech) speechText = agentData.speech;
        }
      } catch {
        /* fall through — speak raw command if LLM unreachable */
      }

      setVoiceLog((prev) => [...prev, { sender: "woo", text: speechText }]);

      // Speak the LLM response via Piper TTS
      const res = await fetch("http://localhost:41071/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: speechText, mood: "ceremonial" }),
      });
      if (!res.ok) throw new Error(`Voice error: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
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
