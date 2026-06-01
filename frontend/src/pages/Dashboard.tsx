import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { fetchGridStatus } from "@/api/grid";
import { speak, stopVoice } from "@/utils/voice";
import { audioPresence } from "@/utils/AudioPresence";
import { RadioEmitter } from "@/components/RadioEmitter";
import { VoiceOrb } from "@/components/VoiceOrb";
import {
  Activity,
  Bell,
  CreditCard,
  Database,
  Flame,
  Grid3x3,
  LayoutDashboard,
  LogOut,
  Settings,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const pulseData = [
  { t: "00:00", grid: 320, trinity: 240, ledger: 180 },
  { t: "04:00", grid: 410, trinity: 290, ledger: 220 },
  { t: "08:00", grid: 520, trinity: 360, ledger: 280 },
  { t: "12:00", grid: 680, trinity: 460, ledger: 340 },
  { t: "16:00", grid: 590, trinity: 520, ledger: 380 },
  { t: "20:00", grid: 760, trinity: 610, ledger: 450 },
  { t: "24:00", grid: 880, trinity: 720, ledger: 530 },
];

const odeBars = [
  { o: "Ogbe", v: 88 },
  { o: "Oyeku", v: 72 },
  { o: "Iwori", v: 95 },
  { o: "Odi", v: 64 },
  { o: "Irosun", v: 81 },
  { o: "Owonrin", v: 77 },
  { o: "Obara", v: 90 },
  { o: "Okanran", v: 68 },
];


const elements = [
  { g: "🜂", name: "Ikang", role: "Interpretation", threshold: 0.75, value: 0.82, color: "primary" },
  { g: "🜄", name: "Mmọng", role: "Memory & Message", threshold: 0.70, value: 0.78, color: "primary" },
  { g: "🜁", name: "Afim", role: "Agent Voice", threshold: 0.65, value: 0.71, color: "secondary" },
  { g: "🜃", name: "Isong", role: "Execution", threshold: 0.80, value: 0.86, color: "secondary" },
];

const clusters = [
  { name: "nairobi-α", graph: "neo4j-local", pulse: 98, status: "online" },
  { name: "kampala-β", graph: "neo4j-kampala", pulse: 94, status: "online" },
  { name: "lagos-γ", graph: "neo4j-lagos", pulse: 71, status: "syncing" },
];

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", active: true, path: "/dashboard" },
  { icon: Grid3x3, label: "Watchtower", path: "/watchtower" },
  { icon: Activity, label: "TruthEngine", path: "/dashboard" },
  { icon: Database, label: "Proposals", path: "/proposals" },
  { icon: Users, label: "Disputes", path: "/disputes" },
];

type WakeState = 'booting' | 'signal' | 'memory' | 'resonance' | 'world' | 'online' | 'complete';

interface DashboardProps {
  role?: string;
}

let globalHasBriefed = false;

const Dashboard = ({ role = "architect" }: DashboardProps) => {
  const [livePulse, setLivePulse] = useState(98.4);
  const [wakeState, setWakeState] = useState<WakeState>('booting');
  const [census, setCensus] = useState({
    nodes: 95332,
    relationships: 25050,
    events: 1350,
    utterances: 1345,
    last_heartbeat: null,
    seal: "🜃∴🜂"
  });
  const hasBriefedRef = useRef(false);

  useEffect(() => {
    // Fetch census details
    const fetchCensus = async () => {
      try {
        const res = await fetch("/api/grid/census");
        if (res.ok) {
          const data = await res.json();
          setCensus(data);
        }
      } catch (err) {
        console.error("Failed to fetch census", err);
      }
    };
    fetchCensus();
    const censusInterval = setInterval(fetchCensus, 10000);

    document.title = "Grid Dashboard — MoStar Sovereign";
    const desc = "Real-time Sovereign Grid telemetry: Trinity nodes, Ledger pulse, and Odu resonance.";
    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.setAttribute("name", "description");
      document.head.appendChild(meta);
    }
    meta.setAttribute("content", desc);

    // SSE Listener for live telemetry and autonomous announcements
    const eventSource = new EventSource("/api/stream");
    eventSource.onmessage = async (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "event" && data.event) {
          const ev = data.event;
          if (ev.severity === "high" || ev.severity === "critical") {
            const speech = ev.payload?.speech || ev.text;
            if (speech) {
              audioPresence.dipHumForVoice();
              audioPresence.playChime(ev.severity);
              document.body.setAttribute("data-voice-state", "speaking");
              await speak(speech, ev.severity === "critical" ? "alert" : "stable");
              document.body.setAttribute("data-voice-state", "idle");
              audioPresence.restoreHum();
            }
          }
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    return () => {
      clearInterval(censusInterval);
      stopVoice();
      eventSource.close();
      audioPresence.stop();
    };
  }, []);

  useEffect(() => {
    if (wakeState === 'booting') {
      setTimeout(() => setWakeState('signal'), 1500);
    } else if (wakeState === 'signal') {
      setTimeout(() => setWakeState('memory'), 1000);
    } else if (wakeState === 'memory') {
      setTimeout(() => setWakeState('resonance'), 1000);
    } else if (wakeState === 'resonance') {
      setTimeout(() => setWakeState('world'), 1000);
    } else if (wakeState === 'world') {
      setTimeout(() => setWakeState('online'), 1000);
    } else if (wakeState === 'online') {
      setTimeout(() => {
        setWakeState('complete');
        audioPresence.wakeGrid();
      }, 1500);
    }
  }, [wakeState]);

  // Single briefing on first mount after wake completes
  useEffect(() => {
    if (wakeState !== 'complete') return;
    if (globalHasBriefed || hasBriefedRef.current) return;
    hasBriefedRef.current = true;
    globalHasBriefed = true;

    setTimeout(() => {
      document.body.setAttribute("data-voice-state", "thinking");
      fetch("/api/briefing?write_log=true")
        .then((r) => r.json())
        .then((data) => {
          const speech = data.message || data.text || data.speech || "MoStar Grid is awake.";
          audioPresence.dipHumForVoice();
          document.body.setAttribute("data-voice-state", "speaking");
          speak(speech, "alert").then(() => {
            document.body.setAttribute("data-voice-state", "idle");
            audioPresence.restoreHum();
          });
        })
        .catch(() => {
          document.body.setAttribute("data-voice-state", "speaking");
          speak("MoStar Grid is awake.", "alert").then(() => {
            document.body.setAttribute("data-voice-state", "idle");
          });
        });
    }, 1200);
  }, [wakeState]);

  // ── Real SSE scroll stream ──────────────────────────────────────────────────
  const [scrollEvents, setScrollEvents] = useState<
    { tag: string; glyph: string; txt: string; color: string; ts: number }[]
  >([]);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource("/api/stream");
    sseRef.current = es;

    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const colorMap: Record<string, string> = {
          SCROLL:  "text-primary",
          ATTEST:  "text-secondary",
          PROPOSE: "text-foreground",
          VETO:    "text-destructive",
          COMMIT:  "text-primary",
          DISPUTE: "text-secondary",
          SEAL:    "text-primary",
          REJECT:  "text-destructive",
        };
        const glyphMap: Record<string, string> = {
          SCROLL:  "🜂", SEAL: "🜂", COMMIT: "🜂",
          ATTEST:  "🜃", DISPUTE: "🜃",
          PROPOSE: "🜁", DISPUTE2: "🜁",
          VETO:    "🜄",
        };
        setScrollEvents((prev) => [
          {
            tag:   payload.type ?? "EVENT",
            glyph: glyphMap[payload.type] ?? "🜂",
            txt:   payload.message ?? payload.detail ?? JSON.stringify(payload),
            color: colorMap[payload.type] ?? "text-foreground",
            ts:    Date.now(),
          },
          ...prev.slice(0, 19), // keep last 20 events max
        ]);
      } catch {
        // non-JSON ping frame — ignore
      }
    };

    es.onerror = () => {
      // SSE dropped — reconnect handled by browser automatically
    };

    return () => {
      es.close();
      sseRef.current = null;
    };
  }, []);

  // ── Real cluster + grid status ──────────────────────────────────────────────
  const [gridStatus, setGridStatus] = useState<{
    covenant: string;
    mcpOnline: boolean;
    mcpScopes: string[];
    phase: string;
    clusters: { name: string; graph: string; pulse: number; status: string }[];
  } | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [censusRes, healthRes] = await Promise.all([
          fetch("/api/grid/census"),
          fetch("/api/health"),
        ]);
        const census = await censusRes.json();
        const health = await healthRes.json();

        setGridStatus({
          covenant:  census.seal ?? "—",
          mcpOnline: health?.mcp?.online ?? false,
          mcpScopes: health?.mcp?.scopes ?? [],
          phase:     health?.phase ?? "—",
          clusters: [
            {
              name:   "nairobi-α",
              graph:  "neo4j-local",
              pulse:  Math.round((census.nodes / 100000) * 100),
              status: census.nodes > 0 ? "online" : "degraded",
            },
            // Add kampala-β and lagos-γ when those instances are live
            // { name: "kampala-β", graph: "neo4j-kampala", pulse: 0, status: "pending" },
          ],
        });
      } catch {
        // Backend not ready yet — fail silently
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30_000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const stats = [
    { label: "MindGraph Nodes", value: census.nodes.toLocaleString(), delta: "Live", icon: Database, color: "text-primary" },
    { label: "Relationships", value: census.relationships.toLocaleString(), delta: "Live", icon: Zap, color: "text-secondary" },
    { label: "Grid Events", value: census.events.toLocaleString(), delta: "Emitted", icon: Activity, color: "text-foreground" },
    { label: "Woo Utterances", value: census.utterances.toLocaleString(), delta: "Spoken", icon: Users, color: "text-primary" },
  ];

  if (wakeState !== 'complete') {
    return (
      <div className="fixed inset-0 bg-black flex flex-col items-center justify-center font-mono text-xs uppercase tracking-[0.3em] text-muted-foreground z-50">
        <div className="mb-12 text-4xl text-tier-orange">⟁</div>
        <div className="space-y-4 text-center">
          <div className={`transition-opacity duration-1000 ${wakeState === 'booting' ? 'opacity-0' : 'opacity-100 text-foreground'}`}>Signal Detected</div>
          <div className={`transition-opacity duration-1000 ${['booting', 'signal'].includes(wakeState) ? 'opacity-0' : 'opacity-100 text-foreground'}`}>Memory Restored</div>
          <div className={`transition-opacity duration-1000 ${['booting', 'signal', 'memory'].includes(wakeState) ? 'opacity-0' : 'opacity-100 text-foreground'}`}>Resonance Stable</div>
          <div className={`transition-opacity duration-1000 ${['booting', 'signal', 'memory', 'resonance'].includes(wakeState) ? 'opacity-0' : 'opacity-100 text-foreground'}`}>World Signals Synced</div>
          <div className={`transition-opacity duration-1000 ${['booting', 'signal', 'memory', 'resonance', 'world'].includes(wakeState) ? 'opacity-0' : 'opacity-100 text-primary font-black mt-8'}`}>Woo Online</div>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-background text-foreground flex relative overflow-hidden">
      <RadioEmitter gridPulse={livePulse} />

      {/* Sidebar */}
      <nav className="w-[100px] shrink-0 bg-[hsl(240_36%_15%)] flex flex-col items-center py-8 border-r border-border relative z-10 shadow-[4px_0_24px_rgba(0,0,0,0.4)]">
        <Link
          to="/"
          className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-orange mb-12"
          aria-label="Back to gate"
        >
          <Flame className="w-6 h-6 text-primary-foreground" />
        </Link>

        <div className="flex flex-col gap-6 flex-1">
          {navItems.map(({ icon: Icon, label, active, path }) => (
            <Link
              key={label}
              to={path}
              className={`group w-12 h-12 rounded-xl flex items-center justify-center transition-smooth ${active
                  ? "bg-tier-orange/10 text-tier-orange shadow-glow-orange"
                  : "text-[hsl(240_22%_52%)] hover:text-tier-orange hover:bg-tier-orange/5"
                }`}
              title={label}
            >
              <Icon className="w-5 h-5" />
            </Link>
          ))}
        </div>

        <div className="flex flex-col gap-6 items-center">
          <button className="w-8 h-8 text-[hsl(240_22%_52%)] hover:text-tier-orange transition-smooth" title="Payment">
            <CreditCard className="w-full h-full" />
          </button>
          <button className="w-8 h-8 text-[hsl(240_22%_52%)] hover:text-tier-orange transition-smooth" title="Settings">
            <Settings className="w-full h-full" />
          </button>
          <button className="w-8 h-8 text-[hsl(240_22%_52%)] hover:text-tier-orange transition-smooth relative" title="Notifications">
            <Bell className="w-full h-full" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-tier-orange rounded-full animate-pulse" />
          </button>
          <div className="w-[58px] h-[58px] rounded-[21px] bg-background border border-border flex items-center justify-center overflow-hidden">
            <div className="w-11 h-11 rounded-[16px] bg-gradient-primary flex items-center justify-center font-black text-primary-foreground">
              FA
            </div>
          </div>
        </div>
      </nav>

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col relative z-10">
        {/* Top bar */}
        <header className="flex items-center justify-between px-8 py-6 border-b border-border">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground mb-1">
              Sovereign Telemetry
            </p>
            <h1 className="text-3xl font-black tracking-tight">Grid Dashboard</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-xl bg-card border border-border text-xs font-mono uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Trinity Online
            </div>
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-border hover:border-tier-orange/50 hover:text-tier-orange transition-smooth text-xs font-mono uppercase tracking-wider"
            >
              <LogOut className="w-4 h-4" /> Exit
            </Link>
          </div>
        </header>

        <div className="flex-1 p-6 sm:p-8 space-y-8">
          {/* Stats */}
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map(({ label, value, delta, icon: Icon, color }) => (
              <article
                key={label}
                className="bg-card border border-border rounded-2xl p-5 shadow-elegant hover:border-tier-orange/40 transition-smooth"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground">
                    {label}
                  </span>
                  <Icon className={`w-4 h-4 ${color}`} />
                </div>
                <p className="text-2xl sm:text-3xl font-black tracking-tight mb-1">{value}</p>
                <p className="text-xs font-mono text-green-500 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> {delta}
                </p>
              </article>
            ))}
          </section>

          {/* Charts */}
          <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <article className="xl:col-span-2 bg-card border border-border rounded-2xl p-6 shadow-elegant">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-lg font-black tracking-tight">Pulse Telemetry</h2>
                  <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mt-1">
                    24h · Grid / Trinity / Ledger
                  </p>
                </div>
                <div className="flex gap-3 text-[10px] font-mono uppercase tracking-wider">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-tier-orange" />Grid</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-tier-red" />Trinity</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-tier-zinc" />Ledger</span>
                </div>
              </div>
              <div className="h-72 w-full">
                <ResponsiveContainer>
                  <AreaChart data={pulseData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gGrid" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--tier-orange))" stopOpacity={0.5} />
                        <stop offset="100%" stopColor="hsl(var(--tier-orange))" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gTrinity" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--tier-red))" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="hsl(var(--tier-red))" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gLedger" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--tier-zinc))" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="hsl(var(--tier-zinc))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 6" vertical={false} />
                    <XAxis dataKey="t" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: 12,
                        fontSize: 12,
                      }}
                    />
                    <Area type="monotone" dataKey="grid" stroke="hsl(var(--tier-orange))" strokeWidth={2} fill="url(#gGrid)" />
                    <Area type="monotone" dataKey="trinity" stroke="hsl(var(--tier-red))" strokeWidth={2} fill="url(#gTrinity)" />
                    <Area type="monotone" dataKey="ledger" stroke="hsl(var(--tier-zinc))" strokeWidth={2} fill="url(#gLedger)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="bg-card border border-border rounded-2xl p-6 shadow-elegant">
              <h2 className="text-lg font-black tracking-tight mb-1">Odu Resonance</h2>
              <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-6">
                Ifá Signal Strength
              </p>
              <div className="h-72 w-full">
                <ResponsiveContainer>
                  <BarChart data={odeBars} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 6" vertical={false} />
                    <XAxis dataKey="o" stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: 12,
                        fontSize: 12,
                      }}
                      cursor={{ fill: "hsl(var(--muted) / 0.4)" }}
                    />
                    <Bar dataKey="v" fill="hsl(var(--tier-orange))" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </section>

          {/* TruthEngine elemental thresholds */}
          <section className="bg-card border border-border rounded-2xl p-6 shadow-elegant">
            <div className="flex items-start justify-between mb-6 flex-wrap gap-2">
              <div>
                <h2 className="text-lg font-black tracking-tight">TruthEngine · Elemental Resonance</h2>
                <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mt-1">
                  Ibibio thresholds · proposals below veto with 409 Conflict
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-mono uppercase tracking-wider border border-primary/30">
                All thresholds passing
              </span>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {elements.map((e) => {
                const pct = Math.min(100, Math.round(e.value * 100));
                const thr = Math.round(e.threshold * 100);
                const passing = e.value >= e.threshold;
                return (
                  <div key={e.name} className="rounded-xl border border-border p-4 bg-background/40">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-3xl" style={{ textShadow: `0 0 24px hsl(var(--${e.color}) / 0.6)` }}>{e.g}</span>
                      <span className={`text-[10px] font-mono uppercase tracking-wider ${passing ? "text-primary" : "text-destructive"}`}>
                        {passing ? "pass" : "veto"}
                      </span>
                    </div>
                    <p className="text-sm font-black uppercase tracking-wider">{e.name}</p>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-3">{e.role}</p>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden relative">
                      <div className="absolute inset-y-0" style={{ left: `${thr}%`, width: "2px", background: "hsl(var(--foreground) / 0.5)" }} />
                      <div
                        className={`h-full ${e.color === "primary" ? "bg-gradient-primary shadow-glow-orange" : "bg-gradient-red shadow-glow-red"}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-2 text-[10px] font-mono text-muted-foreground">
                      <span>val {e.value.toFixed(2)}</span>
                      <span>≥ {e.threshold.toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Federation + MindGraph */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <article className="bg-card border border-border rounded-2xl p-6 shadow-elegant">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-black tracking-tight">Federation · Scroll Stream</h2>
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                  SSE · /api/stream
                </span>
              </div>
              <ul className="space-y-3 font-mono text-xs">
                {scrollEvents.length === 0 ? (
                  <li className="text-muted-foreground text-xs font-mono py-2 animate-pulse">
                    🜂 awaiting scroll events…
                  </li>
                ) : (
                  scrollEvents.map((e, i) => (
                    <li key={i} className="flex items-start gap-3 py-2 border-b border-border/60 last:border-0">
                      <span className="text-base leading-none mt-0.5">{e.glyph}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border border-current ${e.color}`}>
                        {e.tag}
                      </span>
                      <span className="text-muted-foreground flex-1">{e.txt}</span>
                    </li>
                  ))
                )}
              </ul>
            </article>

            <article className="bg-card border border-border rounded-2xl p-6 shadow-elegant">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-black tracking-tight">MindGraph · Sovereign Clusters</h2>
                <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                  Live · /api/grid/census
                </span>
              </div>
              <div className="space-y-5">
                {(gridStatus?.clusters ?? []).map((c) => (
                  <div key={c.name}>
                    <div className="flex items-center justify-between mb-2 text-xs font-mono uppercase tracking-wider">
                      <span className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            c.status === "online" ? "bg-primary animate-pulse" : "bg-secondary animate-pulse"
                          }`}
                        />
                        {c.name}
                        <span className="text-muted-foreground normal-case">· {c.graph}</span>
                      </span>
                      <span className={c.status === "online" ? "text-primary" : "text-secondary"}>
                        {c.pulse}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full ${
                          c.status === "online"
                            ? "bg-gradient-primary shadow-glow-orange"
                            : "bg-gradient-red shadow-glow-red"
                        }`}
                        style={{ width: `${c.pulse}%` }}
                      />
                    </div>
                  </div>
                ))}

                {/* Real system status notices — sourced from /api/health and /api/grid/census */}
                <div className="pt-4 border-t border-border space-y-1 text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground">
                  {gridStatus ? (
                    <>
                      <p>[SEAL] {gridStatus.covenant}</p>
                      <p>[MCP] gateway {gridStatus.mcpOnline ? "online" : "offline"}{gridStatus.mcpScopes.length > 0 ? ` · scopes: ${gridStatus.mcpScopes.join(", ")}` : ""}</p>
                      <p>[PHASE] {gridStatus.phase}</p>
                    </>
                  ) : (
                    <p className="animate-pulse">[GRID] loading sovereign status…</p>
                  )}
                </div>
              </div>
            </article>
          </section>
        </div>
      </div>
      
      <VoiceOrb />
    </main>
  );
};

export default Dashboard;
