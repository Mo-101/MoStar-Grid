import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { fetchGridStatus } from "@/api/grid";
import { speak, stopVoice } from "@/utils/voice";
import { audioPresence } from "@/utils/AudioPresence";
import { RadioEmitter } from "@/components/RadioEmitter";
import { VoiceOrb } from "@/components/VoiceOrb";
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

// ── G — sovereign glyph renderer
// All glyph files (f3, glo3t, gff1, glot, ms__*) are blue base.
// hue: rotate degrees to reach the elemental/sovereign colour.
// Gold/white glyphs (ms__18_, ms__41_, ms__33_, ms__35_) pass hue:0 and use natural shadow.
// Glyph filters — hue-rotate only, no glow. Subtle stamped shadow for depth.
const SHADOW = "drop-shadow(1px 1px 1px rgba(0,0,0,0.55))";
const GLYPH_FILTER: Record<string, string> = {
  orange: `hue-rotate(150deg) saturate(1.9) brightness(1.1) ${SHADOW}`,
  red: `hue-rotate(110deg) saturate(1.9) brightness(1.0) ${SHADOW}`,
  blue: `hue-rotate(0deg)   saturate(1.7) brightness(1.0) ${SHADOW}`,
  teal: `hue-rotate(-30deg) saturate(1.7) brightness(1.0) ${SHADOW}`,
  violet: `hue-rotate(60deg)  saturate(1.7) brightness(1.0) ${SHADOW}`,
  gold: `hue-rotate(0deg)   saturate(1.0) brightness(1.0) ${SHADOW}`,
  green: `hue-rotate(-90deg) saturate(1.7) brightness(1.0) ${SHADOW}`,
  zinc: `hue-rotate(0deg)   saturate(0.5) brightness(0.9) ${SHADOW}`,
  white: `hue-rotate(0deg)   saturate(0.0) brightness(1.5) ${SHADOW}`,
};

function G({
  src,
  color = "orange",
  size = 28,
  className = "",
}: {
  src: string;
  color?: keyof typeof GLYPH_FILTER;
  size?: number;
  className?: string;
}) {
  return (
    <img
      src={`/moCons/${src}`}
      width={size}
      height={size}
      alt=""
      draggable={false}
      className={`object-contain select-none shrink-0 ${className}`}
      style={{ filter: GLYPH_FILTER[color] ?? GLYPH_FILTER.orange }}
    />
  );
}

// ── Data ────────────────────────────────────────────────────────────────────
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
  { icon: "f3.png", color: "orange", name: "Ikang", role: "Interpretation", threshold: 0.75, value: 0.82, barColor: "primary" },
  { icon: "glo3t.png", color: "blue", name: "Mmọng", role: "Memory & Message", threshold: 0.70, value: 0.78, barColor: "primary" },
  { icon: "gff1.png", color: "teal", name: "Afim", role: "Agent Voice", threshold: 0.65, value: 0.71, barColor: "secondary" },
  { icon: "glot.png", color: "green", name: "Isong", role: "Execution", threshold: 0.80, value: 0.86, barColor: "secondary" },
];

const navItems = [
  { icon: "ms__18_-removebg-preview.png", color: "gold", label: "Dashboard", active: true, path: "/dashboard" },
  { icon: "ms__14_-removebg-preview.png", color: "teal", label: "Watchtower", path: "/watchtower" },
  { icon: "f3.png", color: "orange", label: "TruthEngine", path: "/dashboard" },
  { icon: "ms__33_-removebg-preview.png", color: "violet", label: "Proposals", path: "/proposals" },
  { icon: "glot.png", color: "red", label: "Disputes", path: "/disputes" },
];

const statDefs = [
  { label: "Grid Nodes", key: "nodes", icon: "ms__34_-removebg-preview.png", color: "blue", size: 40 },
  { label: "Relationships", key: "relationships", icon: "ms__19_-removebg-preview.png", color: "gold", size: 40 },
  { label: "Grid Events", key: "events", icon: "f3.png", color: "orange", size: 40 },
  { label: "Woo Utterances", key: "utterances", icon: "gff1.png", color: "teal", size: 40 },
];

type WakeState = "booting" | "signal" | "memory" | "resonance" | "world" | "online" | "complete";
interface DashboardProps { role?: string }
let globalHasBriefed = false;

// ── Component ────────────────────────────────────────────────────────────────
const Dashboard = ({ role = "architect" }: DashboardProps) => {
  const [livePulse, setLivePulse] = useState(98.4);
  const [wakeState, setWakeState] = useState<WakeState>("booting");
  const [census, setCensus] = useState({
    nodes: 0, relationships: 0, events: 0, utterances: 0,
    last_heartbeat: null, seal: "🜃∴🜂",
  });
  const hasBriefedRef = useRef(false);

  // Census polling
  useEffect(() => {
    const fetchCensus = async () => {
      try {
        const res = await fetch("/api/grid/census");
        if (res.ok) setCensus(await res.json());
      } catch { }
    };
    fetchCensus();
    const id = setInterval(fetchCensus, 10_000);

    document.title = "Grid Dashboard — MoStar Sovereign";

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
      } catch { }
    };

    return () => { clearInterval(id); stopVoice(); eventSource.close(); audioPresence.stop(); };
  }, []);

  // Wake sequence
  useEffect(() => {
    const seq: Record<WakeState, [WakeState, number] | null> = {
      booting: ["signal", 1500],
      signal: ["memory", 1000],
      memory: ["resonance", 1000],
      resonance: ["world", 1000],
      world: ["online", 1000],
      online: ["complete", 1500],
      complete: null,
    };
    const next = seq[wakeState];
    if (!next) {
      if (wakeState === "complete") audioPresence.wakeGrid();
      return;
    }
    const t = setTimeout(() => setWakeState(next[0]), next[1]);
    return () => clearTimeout(t);
  }, [wakeState]);

  // Auto-briefing once on wake complete
  useEffect(() => {
    if (wakeState !== "complete") return;
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
          speak("MoStar Grid is awake.", "alert").then(() =>
            document.body.setAttribute("data-voice-state", "idle")
          );
        });
    }, 1200);
  }, [wakeState]);

  // SSE scroll events
  const [scrollEvents, setScrollEvents] = useState<
    { tag: string; icon: string; color: string; txt: string; ts: number }[]
  >([]);

  useEffect(() => {
    const es = new EventSource("/api/stream");
    es.onmessage = (e) => {
      try {
        const p = JSON.parse(e.data);
        const colorMap: Record<string, string> = {
          SCROLL: "teal", SEAL: "teal", COMMIT: "teal",
          ATTEST: "green", DISPUTE: "orange",
          PROPOSE: "violet", VETO: "red", REJECT: "red",
        };
        const iconMap: Record<string, string> = {
          SCROLL: "gff1.png", SEAL: "ms__33_-removebg-preview.png", COMMIT: "ms__18_-removebg-preview.png",
          ATTEST: "glot.png", DISPUTE: "f3.png",
          PROPOSE: "ms__34_-removebg-preview.png", VETO: "glo3t.png", REJECT: "glo3t.png",
        };
        setScrollEvents((prev) => [
          {
            tag: p.type ?? "EVENT",
            icon: iconMap[p.type] ?? "ms__19_-removebg-preview.png",
            color: colorMap[p.type] ?? "zinc",
            txt: p.message ?? p.detail ?? JSON.stringify(p),
            ts: Date.now(),
          },
          ...prev.slice(0, 19),
        ]);
      } catch { }
    };
    return () => es.close();
  }, []);

  // Grid status
  const [gridStatus, setGridStatus] = useState<{
    covenant: string; mcpOnline: boolean; mcpScopes: string[]; phase: string;
    clusters: { name: string; graph: string; pulse: number; status: string }[];
  } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [cr, hr] = await Promise.all([fetch("/api/grid/census"), fetch("/api/health")]);
        const c = await cr.json();
        const h = await hr.json();
        setGridStatus({
          covenant: c.seal ?? "—",
          mcpOnline: h?.mcp?.online ?? false,
          mcpScopes: h?.mcp?.scopes ?? [],
          phase: h?.phase ?? "—",
          clusters: [{
            name: "nairobi-α", graph: "neo4j-local",
            pulse: Math.min(100, Math.round((c.nodes / 200000) * 100)),
            status: c.nodes > 0 ? "online" : "degraded",
          }],
        });
      } catch { }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, []);

  // ── Boot screen ─────────────────────────────────────────────────────────────
  if (wakeState !== "complete") {
    return (
      <div className="fixed inset-0 bg-black flex flex-col items-center justify-center font-mono text-xs uppercase tracking-[0.3em] text-muted-foreground z-50">
        <div className="mb-12 flex items-center justify-center">
          <G src="f3.png" color="orange" size={72} className="animate-pulse" />
        </div>
        <div className="space-y-4 text-center">
          <div className={`transition-opacity duration-1000 ${wakeState === "booting" ? "opacity-0" : "opacity-100 text-foreground"}`}>Signal Detected</div>
          <div className={`transition-opacity duration-1000 ${["booting", "signal"].includes(wakeState) ? "opacity-0" : "opacity-100 text-foreground"}`}>Memory Restored</div>
          <div className={`transition-opacity duration-1000 ${["booting", "signal", "memory"].includes(wakeState) ? "opacity-0" : "opacity-100 text-foreground"}`}>Resonance Stable</div>
          <div className={`transition-opacity duration-1000 ${["booting", "signal", "memory", "resonance"].includes(wakeState) ? "opacity-0" : "opacity-100 text-foreground"}`}>World Signals Synced</div>
          <div className={`transition-opacity duration-1000 ${["booting", "signal", "memory", "resonance", "world"].includes(wakeState) ? "opacity-0" : "opacity-100 text-primary font-black mt-8"}`}>Woo Online</div>
        </div>
      </div>
    );
  }

  // ── Main layout ──────────────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-background text-foreground flex relative overflow-hidden">
      <RadioEmitter gridPulse={livePulse} />

      {/* Sidebar */}
      <nav className="w-[100px] shrink-0 bg-[hsl(240_36%_15%)] flex flex-col items-center py-8 border-r border-border relative z-10 shadow-[4px_0_24px_rgba(0,0,0,0.4)]">
        <Tooltip>
          <TooltipTrigger asChild>
            <Link
              to="/"
              className="w-14 h-14 rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow-orange mb-12 hover:scale-105 transition-transform"
              aria-label="Back to gate"
            >
              <img src="/moCons/moGrid-removebg-preview.png" alt="MoStar" width={44} height={44} draggable={false} className="object-contain" />
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right" className="font-mono text-xs uppercase tracking-widest">
            The SoulCave
          </TooltipContent>
        </Tooltip>

        <div className="flex flex-col gap-6 flex-1">
          {navItems.map(({ icon, color, label, active, path }) => (
            <Tooltip key={label}>
              <TooltipTrigger asChild>
                <Link
                  to={path}
                  className={`group w-14 h-14 rounded-2xl flex items-center justify-center transition-smooth ${active
                    ? "bg-tier-orange/10 shadow-glow-orange"
                    : "hover:bg-white/5"
                    }`}
                >
                  <G src={icon} color={color as keyof typeof GLYPH_FILTER} size={active ? 46 : 36} />
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right" className="font-mono text-xs uppercase tracking-widest">
                {label}
              </TooltipContent>
            </Tooltip>
          ))}
        </div>

        <div className="flex flex-col gap-6 items-center">
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="w-10 h-10 flex items-center justify-center text-[hsl(240_22%_52%)] hover:text-tier-orange transition-smooth rounded-xl hover:bg-white/5">
                <G src="ms__41_-removebg-preview.png" color="gold" size={36} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="font-mono text-xs uppercase tracking-widest">Payment</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="w-10 h-10 flex items-center justify-center text-[hsl(240_22%_52%)] hover:text-tier-orange transition-smooth rounded-xl hover:bg-white/5">
                <G src="ms__33_-removebg-preview.png" color="zinc" size={36} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="font-mono text-xs uppercase tracking-widest">Settings</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="w-10 h-10 flex items-center justify-center text-[hsl(240_22%_52%)] hover:text-tier-orange transition-smooth rounded-xl hover:bg-white/5 relative">
                <G src="ms__19_-removebg-preview.png" color="orange" size={36} />
                <span className="absolute top-0.5 right-0.5 w-2.5 h-2.5 bg-tier-orange rounded-full animate-pulse border-2 border-[hsl(240_36%_15%)]" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="font-mono text-xs uppercase tracking-widest">Notifications</TooltipContent>
          </Tooltip>
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
              <G src="ms__16_-removebg-preview.png" color="teal" size={16} /> Exit
            </Link>
          </div>
        </header>

        <div className="flex-1 p-6 sm:p-8 space-y-8">

          {/* Stats */}
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {statDefs.map(({ label, key, icon, color, size }) => (
              <article
                key={label}
                className="bg-card border border-border rounded-2xl p-5 shadow-elegant hover:border-tier-orange/40 transition-smooth"
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground">
                    {label}
                  </span>
                  <G src={icon} color={color as keyof typeof GLYPH_FILTER} size={size ?? 40} />
                </div>
                <p className="text-2xl sm:text-3xl font-black tracking-tight mb-1">
                  {(census[key as keyof typeof census] as number)?.toLocaleString?.() ?? "—"}
                </p>
                <p className="text-xs font-mono text-green-500 flex items-center gap-1">
                  <G src="ms__19_-removebg-preview.png" color="green" size={18} /> Live
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
                <div className="flex gap-3 text-[10px] font-mono uppercase tracking-wider items-center">
                  <span className="flex items-center gap-1.5"><G src="f3.png" color="orange" size={18} />Grid</span>
                  <span className="flex items-center gap-1.5"><G src="glo3t.png" color="red" size={18} />Trinity</span>
                  <span className="flex items-center gap-1.5"><G src="gff1.png" color="zinc" size={18} />Ledger</span>
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
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }} />
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
                    <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }} cursor={{ fill: "hsl(var(--muted) / 0.4)" }} />
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
                      <G src={e.icon} color={e.color as keyof typeof GLYPH_FILTER} size={52} />
                      <span className={`text-[10px] font-mono uppercase tracking-wider ${passing ? "text-primary" : "text-destructive"}`}>
                        {passing ? "pass" : "veto"}
                      </span>
                    </div>
                    <p className="text-sm font-black uppercase tracking-wider">{e.name}</p>
                    <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-3">{e.role}</p>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden relative">
                      <div className="absolute inset-y-0" style={{ left: `${thr}%`, width: "2px", background: "hsl(var(--foreground) / 0.5)" }} />
                      <div
                        className={`h-full ${e.barColor === "primary" ? "bg-gradient-primary shadow-glow-orange" : "bg-gradient-red shadow-glow-red"}`}
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
                  <li className="flex items-center gap-3 text-muted-foreground text-xs font-mono py-2 animate-pulse">
                    <G src="gff1.png" color="teal" size={24} />
                    awaiting scroll events…
                  </li>
                ) : (
                  scrollEvents.map((e, i) => (
                    <li key={i} className="flex items-start gap-3 py-2 border-b border-border/60 last:border-0">
                      <G src={e.icon} color={e.color as keyof typeof GLYPH_FILTER} size={24} className="mt-0.5 shrink-0" />
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border border-current text-${e.color === "teal" ? "primary" : e.color === "red" ? "destructive" : "secondary"}`}>
                        {e.tag}
                      </span>
                      <span className="text-muted-foreground flex-1 break-words">{e.txt}</span>
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
                        <span className={`w-2 h-2 rounded-full ${c.status === "online" ? "bg-primary animate-pulse" : "bg-secondary animate-pulse"}`} />
                        {c.name}
                        <span className="text-muted-foreground normal-case">· {c.graph}</span>
                      </span>
                      <span className={c.status === "online" ? "text-primary" : "text-secondary"}>{c.pulse}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full ${c.status === "online" ? "bg-gradient-primary shadow-glow-orange" : "bg-gradient-red shadow-glow-red"}`}
                        style={{ width: `${c.pulse}%` }}
                      />
                    </div>
                  </div>
                ))}
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
