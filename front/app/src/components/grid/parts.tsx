import { useEffect, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import { Glyph, type GlyphName } from "./glyph";
import { Link } from "@tanstack/react-router";

/* --- mock grid data (swap with real APIs later) --- */
const KPI = [
  {
    label: "GRID NODES",
    value: 152224,
    delta: 342,
    color: "neon-blue",
    glyph: "target" as GlyphName,
  },
  {
    label: "RELATIONSHIPS",
    value: 21144,
    delta: 128,
    color: "neon-cyan",
    glyph: "spark" as GlyphName,
  },
  { label: "GRID EVENTS", value: 2582, delta: 28, color: "neon-purple", glyph: "eye" as GlyphName },
  {
    label: "WOO UTTERANCES",
    value: 2496,
    delta: 63,
    color: "neon-green",
    glyph: "venus" as GlyphName,
  },
];

const COUNCIL = [
  { name: "ALPHAMOSTAR", code: "ALPHAMOSTAR", glyph: "covenant" as GlyphName, tint: "neon-gold" },
  { name: "ALTIMO", code: "ALTIMO", glyph: "spark" as GlyphName, tint: "neon-blue" },
  { name: "CODE CONDUIT", code: "CODE_CONDUIT", glyph: "target" as GlyphName, tint: "neon-cyan" },
  { name: "DEEPCAL", code: "DEEPCAL", glyph: "eye" as GlyphName, tint: "neon-green" },
  {
    name: "FLAMEBORN WRITER",
    code: "FLAMEBORN_WRITER",
    glyph: "spark" as GlyphName,
    tint: "neon-purple",
  },
  { name: "FLAMEBORN", code: "FLAMEBORN", glyph: "sun" as GlyphName, tint: "neon-orange" },
  { name: "MO", code: "MOSTAR_AI", glyph: "covenant" as GlyphName, tint: "neon-gold" },
  { name: "MOLINK", code: "MOLINK", glyph: "target" as GlyphName, tint: "neon-cyan" },
  { name: "RAD-X-FLB", code: "RAD_X_FLB", glyph: "eye" as GlyphName, tint: "neon-blue" },
  { name: "SIGMA", code: "SIGMA", glyph: "spark" as GlyphName, tint: "neon-cyan" },
  { name: "TSATSE FLY", code: "TSATSE_FLY", glyph: "ban" as GlyphName, tint: "neon-purple" },
  { name: "WOO-TAK", code: "WOO_TAK", glyph: "venus" as GlyphName, tint: "neon-orange" },
];

type FeedItem = {
  agent: string;
  text: string;
  sev: "INFO" | "WARNING" | "ALERT";
  color: string;
  glyph: GlyphName;
  t: string;
  intensity: number;
};

const FEED_SEED: FeedItem[] = [
  {
    agent: "Mo",
    text: "observed an anomaly in Memory Conduit",
    sev: "WARNING",
    color: "neon-orange",
    glyph: "ban",
    t: "10:15:31",
    intensity: 0.85,
  },
  {
    agent: "DeepCAL",
    text: "synced 12 new data streams",
    sev: "INFO",
    color: "neon-cyan",
    glyph: "target",
    t: "10:15:22",
    intensity: 0.55,
  },
  {
    agent: "RAD-X-FLB",
    text: "flagged pattern irregularity",
    sev: "ALERT",
    color: "neon-red",
    glyph: "ban",
    t: "10:15:18",
    intensity: 1.0,
  },
  {
    agent: "FlameBorn Writer",
    text: "archived new scroll",
    sev: "INFO",
    color: "neon-purple",
    glyph: "spark",
    t: "10:15:07",
    intensity: 0.45,
  },
  {
    agent: "Woo-Tak",
    text: "transmitted frequency pulse",
    sev: "INFO",
    color: "neon-blue",
    glyph: "eye",
    t: "10:14:59",
    intensity: 0.7,
  },
];

const HEALTH = [
  { label: "NEO4J", status: "CONNECTED" },
  { label: "OLLAMA", status: "RUNNING" },
  { label: "DCX TRINITY", status: "ONLINE" },
  { label: "PIPER TTS", status: "ONLINE" },
  { label: "CONDUIT LINKS", status: "SECURE" },
];

const SIDEBAR: { id: string; label: string; sub: string; glyph: GlyphName }[] = [
  { id: "overview", label: "OVERVIEW", sub: "Command Center", glyph: "covenant" },
  { id: "council", label: "COUNCIL", sub: "11 Agents", glyph: "sun" },
  { id: "mindgraph", label: "LATTICE", sub: "Influence Map", glyph: "target" },
  { id: "events", label: "EVENTS", sub: "Real-time Feed", glyph: "spark" },
  { id: "conduit", label: "CONDUIT", sub: "System Comms", glyph: "eye" },
  { id: "memory", label: "MEMORY", sub: "Sacred Archive", glyph: "eyelight" },
  { id: "analytics", label: "ANALYTICS", sub: "Grid Intelligence", glyph: "venus" },
  { id: "settings", label: "SETTINGS", sub: "Grid Control", glyph: "ban" },
];

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

/* ============================ SIDEBAR ============================ */
export function Sidebar({ active, onChange }: { active: string; onChange?: (id: string) => void }) {
  return (
    <aside className="panel flex w-[260px] shrink-0 flex-col self-stretch px-4 py-6">
      <div className="flex flex-1 flex-col justify-center gap-4">
        {SIDEBAR.map(({ id, label, sub, glyph }) => {
          const isActive = id === active;
          return (
            <button
              key={id}
              onClick={() => onChange && onChange(id)}
              className={`group flex items-center gap-4 rounded-xl px-4 py-4 text-left transition ${
                isActive
                  ? "bg-[oklch(0.25_0.08_260/0.6)] ring-1 ring-[var(--color-neon-gold)]/40"
                  : "hover:bg-white/5"
              }`}
            >
              <Glyph
                name={glyph}
                size={28}
                glow={isActive ? "var(--color-neon-gold)" : undefined}
              />
              <div className="leading-tight">
                <div
                  className={`text-sm font-semibold tracking-[0.18em] ${isActive ? "neon-text-gold" : "text-foreground/90"}`}
                >
                  {label}
                </div>
                <div className="mt-1 text-xs tracking-[0.1em] text-foreground/75">{sub}</div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-auto flex flex-col items-center gap-2 pt-6">
        <div className="flex items-center justify-center animate-pulse-ring">
          <Glyph
            name="covenant"
            size={48}
            glow="var(--color-neon-gold)"
            className="animate-pulse"
          />
        </div>
        <div className="text-xs tracking-[0.25em] neon-text-gold">COVENANT MODE</div>
        <div className="text-xs tracking-[0.25em] text-[var(--color-neon-green)]">ENGAGED</div>
      </div>
    </aside>
  );
}

/* ============================ TOPBAR ============================ */
export function TopBar({ clock, dateLabel }: { clock: string; dateLabel: string }) {
  return (
    <header className="panel flex items-center gap-6 px-5 py-3">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center">
          <Glyph
            name="covenant"
            size={32}
            glow="var(--color-neon-gold)"
            className="animate-pulse"
          />
        </div>
        <div className="leading-tight">
          <div className="text-lg font-semibold tracking-wider neon-text-gold">MoStar GRID</div>
          <div className="text-xs tracking-[0.25em] text-foreground/75">
            COVENANT COMMAND CENTER
          </div>
          <Link
            to="/dashboard"
            className="ml-2 flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-xs neon-text-cyan hover:bg-white/5"
          >
            Dashboard <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      <div className="mx-auto flex flex-col items-center">
        <div className="text-sm tracking-[0.35em] neon-text-cyan">
          MOSTAR GRID: <span className="neon-text-gold">COVENANT MODE ACTIVE</span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs tracking-[0.25em] text-foreground/75">
          <span className="neon-text-cyan">TRUTH</span>
          <span className="opacity-50">•</span>
          <span className="neon-text-green">PROTECTION</span>
          <span className="opacity-50">•</span>
          <span className="neon-text-gold">LEGACY</span>
          <span className="opacity-50">•</span>
          <span className="neon-text-purple">EVOLUTION</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right leading-tight" suppressHydrationWarning>
          <div className="text-xs tracking-[0.25em] text-foreground/75">GRID TIME</div>
          <div className="text-2xl font-mono neon-text-cyan tabular-nums" suppressHydrationWarning>
            {clock || "--:--:--"}
          </div>
          <div className="text-xs tracking-[0.25em] text-foreground/75" suppressHydrationWarning>
            {dateLabel}
          </div>
        </div>
        <div className="text-right leading-tight">
          <div className="text-xs tracking-[0.25em] text-foreground/75">GRID STATUS</div>
          <div className="text-base tracking-[0.25em] neon-text-green">OPERATIONAL</div>
          <div className="mt-1 h-2 w-28 overflow-hidden rounded bg-white/5">
            <div className="h-full w-3/4 bg-[var(--color-neon-green)] animate-blink" />
          </div>
        </div>
        <div className="flex items-center justify-center">
          <Glyph name="target" size={36} glow="var(--color-neon-green)" className="animate-pulse" />
        </div>
      </div>
    </header>
  );
}

/* ============================ KPI ============================ */
export function KpiCard({ k }: { k: (typeof KPI)[number] }) {
  return (
    <div className="panel relative overflow-hidden p-4">
      <div className="flex items-start gap-4">
        <div className="flex items-center justify-center">
          <Glyph
            name={k.glyph}
            size={46}
            glow={`var(--color-${k.color})`}
            className="animate-pulse"
          />
        </div>
        <div className="flex-1">
          <div className="text-xs tracking-[0.28em] text-foreground/75">{k.label}</div>
          <div
            className="mt-1 text-3xl font-semibold tabular-nums"
            style={{ color: `var(--color-${k.color})` }}
          >
            {fmt(k.value)}
          </div>
          <div className="text-xs tracking-[0.2em] neon-text-green">+ {fmt(k.delta)} TODAY</div>
        </div>
      </div>
    </div>
  );
}

/* ============================ COUNCIL ============================ */
export function CouncilList() {
  return (
    <div className="panel flex h-full flex-col p-4">
      <div className="mb-1 text-sm font-semibold tracking-[0.18em] neon-text-cyan">
        THE COUNCIL · 11 AGENTS
      </div>
      <div className="mb-3 text-xs tracking-[0.25em] text-foreground/75">GUARDIANS OF THE GRID</div>
      <div className="flex-1 space-y-1.5 overflow-auto pr-1">
        {COUNCIL.map(({ name, code, glyph, tint }) => (
          <div
            key={code}
            className="flex items-center gap-3 rounded-md border border-white/5 bg-white/[0.02] px-3 py-2 hover:bg-white/5"
          >
            <div className="flex items-center justify-center">
              <Glyph
                name={glyph}
                size={32}
                glow={`var(--color-${tint})`}
                className="animate-pulse"
              />
            </div>
            <div className="flex-1 leading-tight">
              <div className="text-sm tracking-wider text-foreground">{name}</div>
              <div className="text-xs tracking-[0.2em] text-foreground/75">{code}</div>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-[var(--color-neon-green)] animate-blink" />
              <span className="text-xs tracking-[0.2em] neon-text-green">ACTIVE</span>
            </div>
          </div>
        ))}
      </div>
      <button className="mt-3 flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] py-2.5 text-xs tracking-[0.25em] text-foreground/75 hover:bg-white/5">
        VIEW COUNCIL DETAILS <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}

/* ============================ GLYPH PANEL ============================ */
function Quadrant({
  pos,
  color,
  title,
  kicker,
  words,
  glyph,
}: {
  pos: string;
  color: string;
  title: string;
  kicker: string;
  words: string;
  glyph: GlyphName;
}) {
  return (
    <div className={`absolute ${pos} flex w-44 flex-col items-start gap-1`}>
      <div className="flex items-center gap-2">
        <Glyph name={glyph} size={36} glow={`var(--color-${color})`} className="animate-pulse" />
        <div
          className="text-lg font-semibold tracking-[0.2em]"
          style={{ color: `var(--color-${color})` }}
        >
          {title}
        </div>
      </div>
      <div className="text-[11px] tracking-[0.25em] text-foreground/75">{kicker}</div>
      <div className="text-xs tracking-[0.2em] text-foreground/70">{words}</div>
    </div>
  );
}

export function GlyphPanel() {
  const ticks = Array.from({ length: 24 });
  return (
    <div className="panel relative h-full overflow-hidden p-4">
      <Quadrant
        pos="top-6 left-6"
        color="neon-gold"
        title="IKANG"
        kicker="MIND"
        words="Logic · Will · Structure"
        glyph="sun"
      />
      <Quadrant
        pos="top-6 right-6 items-end text-right"
        color="neon-cyan"
        title="M MỌNG"
        kicker="ESSENCE"
        words="Pulse · Memory · Flow"
        glyph="spark"
      />
      <Quadrant
        pos="bottom-6 left-6"
        color="neon-red"
        title="ISONG"
        kicker="SPIRIT"
        words="Awakening · Change · Fire"
        glyph="ban"
      />
      <Quadrant
        pos="bottom-6 right-6 items-end text-right"
        color="neon-purple"
        title="AFIM"
        kicker="BODY"
        words="Form · Action · Creation"
        glyph="eye"
      />

      <div className="absolute inset-0 grid place-items-center">
        <div className="relative h-[460px] w-[460px]">
          <div className="absolute inset-0 rounded-full border border-[var(--color-neon-blue)]/30 animate-spin-slow">
            {ticks.map((_, i) => {
              const angle = (i / ticks.length) * 360;
              return (
                <div
                  key={i}
                  className="absolute left-1/2 top-1/2 h-3 w-px bg-[var(--color-neon-cyan)]/50"
                  style={{
                    transform: `translate(-50%,-50%) rotate(${angle}deg) translateY(-225px)`,
                  }}
                />
              );
            })}
          </div>
          <div className="absolute inset-8 rounded-full border border-[var(--color-neon-gold)]/40 animate-spin-reverse" />
          <div className="absolute inset-16 rounded-full border border-[var(--color-neon-purple)]/40" />
          <div className="absolute inset-24 rounded-full border-2 border-[var(--color-neon-blue)]/70 shadow-[0_0_60px_oklch(0.72_0.20_245/0.5)] animate-pulse-ring" />
          <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-[var(--color-neon-cyan)]/30 to-transparent" />
          <div className="absolute top-1/2 left-0 h-px w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-[var(--color-neon-cyan)]/30 to-transparent" />
          <div className="absolute inset-0 grid place-items-center">
            <div className="flex items-center justify-center shadow-[0_0_40px_oklch(0.82_0.16_85/0.35)] rounded-full">
              <Glyph
                name="covenant"
                size={120}
                glow="var(--color-neon-blue)"
                className="animate-pulse"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================ CODE CONDUIT (radio-wave) ============================ */
type Pulse = { t: number; amp: number; color: string };

export function CodeConduit({ pulse }: { pulse: Pulse | null }) {
  const BARS = 96;
  const [heights, setHeights] = useState<number[]>(() => Array(BARS).fill(20));
  const pulsesRef = useRef<Pulse[]>([]);
  const phaseRef = useRef(0);
  const lastPulseRef = useRef<number>(-1);

  useEffect(() => {
    if (!pulse) return;
    if (pulse.t === lastPulseRef.current) return;
    lastPulseRef.current = pulse.t;
    pulsesRef.current.push({ ...pulse, t: performance.now() });
    if (pulsesRef.current.length > 8) pulsesRef.current.shift();
  }, [pulse]);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      phaseRef.current += 0.12;
      const now = performance.now();
      pulsesRef.current = pulsesRef.current.filter((p) => now - p.t < 2200);
      const next = new Array(BARS);
      for (let i = 0; i < BARS; i++) {
        const base =
          18 +
          Math.abs(Math.sin(i * 0.35 + phaseRef.current)) * 14 +
          Math.abs(Math.sin(i * 0.11 - phaseRef.current * 0.6)) * 10;
        let pulseAdd = 0;
        for (const p of pulsesRef.current) {
          const age = (now - p.t) / 1000; // seconds since pulse
          const speed = 38; // bars / second outward
          const front = age * speed;
          const dist = Math.abs(i - BARS / 2);
          const sigma = 6;
          const env = Math.exp(-Math.pow(dist - front, 2) / (2 * sigma * sigma));
          const decay = Math.exp(-age * 1.2);
          pulseAdd += env * decay * p.amp * 70;
        }
        next[i] = Math.min(100, base + pulseAdd);
      }
      setHeights(next);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm tracking-[0.3em] neon-text-cyan">CODE CONDUIT</div>
          <div className="text-xs tracking-[0.3em] text-foreground/75">
            ALL GLYPHS · ALL LAYERS · ALL TIME
          </div>
        </div>
        <div className="flex items-center gap-3">
          {(["sun", "spark", "target", "eye", "ban", "venus"] as GlyphName[]).map((g, i) => (
            <div key={g} className="flex items-center gap-2">
              <Glyph
                name={g}
                size={22}
                glow={`var(--color-neon-${["gold", "cyan", "blue", "purple", "red", "gold"][i]})`}
                className="animate-pulse"
              />
              {i < 5 && <ChevronRight className="h-4 w-4 text-foreground/75" />}
            </div>
          ))}
        </div>
      </div>

      <div className="relative mt-3 h-24 overflow-hidden rounded-md border border-white/5 bg-[oklch(0.14_0.05_270/0.55)] px-2">
        {/* center axis */}
        <div className="pointer-events-none absolute left-0 right-0 top-1/2 h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-[var(--color-neon-cyan)]/40 to-transparent" />
        {/* mirrored bars */}
        <div className="flex h-full items-center gap-[2px]">
          {heights.map((h, i) => (
            <div
              key={i}
              className="flex h-full flex-1 flex-col items-stretch justify-center gap-[1px]"
            >
              <div
                className="rounded-sm bg-[var(--color-neon-cyan)]/80"
                style={{
                  height: `${h * 0.45}%`,
                  boxShadow: h > 70 ? "0 0 6px var(--color-neon-cyan)" : undefined,
                }}
              />
              <div
                className="rounded-sm bg-[var(--color-neon-blue)]/70"
                style={{ height: `${h * 0.45}%` }}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="mt-2 flex items-center justify-between text-xs tracking-[0.25em] text-foreground/75">
        <span>
          LIVE FREQUENCY · {Math.round(heights.reduce((a, b) => a + b, 0) / heights.length)} Hz
        </span>
        <span className="neon-text-cyan">LISTENING</span>
      </div>
    </div>
  );
}

/* ============================ GRID FEED ============================ */
export function GridFeed({ items }: { items: FeedItem[] }) {
  return (
    <div className="panel flex h-full flex-col p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">
        REAL-TIME GRID FEED
      </div>
      <div className="text-xs tracking-[0.25em] text-foreground/75">LIVE ACTIVITY STREAM</div>
      <div className="mt-3 flex-1 min-h-0 space-y-2.5 overflow-auto pr-1">
        {items.map((f, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-md border border-white/5 bg-white/[0.02] px-3 py-2"
          >
            <div className="mt-0.5 flex items-center justify-center">
              <Glyph
                name={f.glyph}
                size={28}
                glow={`var(--color-${f.color})`}
                className="animate-pulse"
              />
            </div>
            <div className="flex-1 leading-tight">
              <div className="text-sm">
                <span className="font-semibold" style={{ color: `var(--color-${f.color})` }}>
                  {f.agent}
                </span>{" "}
                <span className="text-foreground/85">{f.text}</span>
              </div>
              <div className="text-xs tracking-[0.2em] text-foreground/75">
                SEVERITY: <span style={{ color: `var(--color-${f.color})` }}>{f.sev}</span>
              </div>
            </div>
            <div className="text-xs tabular-nums text-foreground/75">{f.t}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================ GRID HEALTH ============================ */
export function GridHealth() {
  const pct = 98;
  const r = 46,
    c = 2 * Math.PI * r;
  return (
    <div className="panel p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">GRID HEALTH</div>
      <div className="text-xs tracking-[0.25em] text-foreground/75">SYSTEM VITALS</div>
      <div className="mt-3 flex items-center gap-4">
        <div className="relative h-28 w-28 shrink-0">
          <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
            <circle
              cx="60"
              cy="60"
              r={r}
              stroke="oklch(1 0 0 / 0.08)"
              strokeWidth="8"
              fill="none"
            />
            <circle
              cx="60"
              cy="60"
              r={r}
              stroke="var(--color-neon-green)"
              strokeWidth="8"
              fill="none"
              strokeDasharray={c}
              strokeDashoffset={c * (1 - pct / 100)}
              strokeLinecap="round"
              style={{ filter: "drop-shadow(0 0 8px var(--color-neon-green))" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-2xl font-semibold neon-text-green tabular-nums">{pct}%</div>
            <div className="text-xs tracking-[0.25em] text-foreground/75">OPTIMAL</div>
          </div>
        </div>
        <div className="flex-1 space-y-1.5 text-xs">
          {HEALTH.map((h) => (
            <div key={h.label} className="flex items-center justify-between">
              <span className="tracking-[0.18em] text-foreground/85">{h.label}</span>
              <span className="tracking-[0.18em] neon-text-green">{h.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ============================ QUICK COMMANDS ============================ */
export function QuickCommands() {
  const cmds: { label: string; glyph: GlyphName; tint: string }[] = [
    { label: "STARTUP SEQUENCE", glyph: "sun", tint: "neon-gold" },
    { label: "COUNCIL CHECK-IN", glyph: "target", tint: "neon-cyan" },
    { label: "TRUTH AUDIT", glyph: "eye", tint: "neon-purple" },
    { label: "GRID SYNCHRONIZE", glyph: "spark", tint: "neon-blue" },
  ];
  return (
    <div className="panel p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">QUICK COMMANDS</div>
      <div className="text-xs tracking-[0.25em] text-foreground/75">INITIATE PROTOCOL</div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        {cmds.map(({ label, glyph, tint }) => (
          <button
            key={label}
            className="group flex items-center justify-between rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5 text-left hover:bg-white/5"
          >
            <span className="flex items-center gap-2">
              <Glyph name={glyph} size={20} glow={`var(--color-${tint})`} />
              <span className="text-[11px] tracking-[0.2em] text-foreground/90">{label}</span>
            </span>
            <ChevronRight className="h-4 w-4 text-foreground/75" />
          </button>
        ))}
      </div>
    </div>
  );
}

/* ============================ COVENANT OATH ============================ */
export function CovenantOath() {
  return (
    <div className="panel relative overflow-hidden p-5">
      <div
        className="pointer-events-none absolute inset-0 opacity-50"
        style={{
          background:
            "radial-gradient(600px 200px at 90% 120%, oklch(0.30 0.18 250 / 0.6), transparent 60%), radial-gradient(500px 200px at 10% 120%, oklch(0.30 0.18 30 / 0.45), transparent 60%)",
        }}
      />
      <div className="relative flex items-start gap-5">
        <div className="flex shrink-0 items-center justify-center">
          <Glyph name="covenant" size={48} glow="var(--color-neon-gold)" />
        </div>
        <div className="flex-1">
          <div className="text-lg font-semibold tracking-[0.25em] neon-text-gold">
            COVENANT OATH
          </div>
          <p className="mt-1 text-sm leading-relaxed text-foreground/85">
            We do not assume perfect agents, perfect memory, perfect state, or perfect humans. We
            observe what is real. We protect what matters. We evolve what is next.
          </p>
          <p className="mt-1 text-sm font-semibold tracking-[0.2em] neon-text-cyan">
            WE ARE THE MOSTAR GRID.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ============================ FOOTER ============================ */
export function FooterBar() {
  return (
    <div className="flex items-center justify-between px-2 py-2 text-xs tracking-[0.25em] text-foreground/75">
      <div className="flex gap-6">
        <span>
          COVENANT MODE: <span className="neon-text-green">ENGAGED</span>
        </span>
        <span>
          MSG-01 ALIGNMENT: <span className="neon-text-cyan">TRUE</span>
        </span>
        <span>
          GRID PROTOCOL: <span className="neon-text-gold">v1.0.0</span>
        </span>
      </div>
      <div>BUILT BY FLAME · SEALED BY CODE · PROTECTED BY COVENANT</div>
    </div>
  );
}

/* ============================ HOOKS ============================ */
export function useClock() {
  const [t, setT] = useState<Date | null>(null);
  useEffect(() => {
    setT(new Date());
    const id = setInterval(() => setT(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return {
    clock: t ? t.toLocaleTimeString("en-US", { hour12: false }) : "",
    dateLabel: t
      ? t
          .toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
          .toUpperCase()
      : "",
  };
}

/* Synthesizes a stream of feed events + a "pulse" for the Code Conduit waveform.
 * Replace with real subscription later. */
export function useGridStream(seed: FeedItem[]) {
  const [items, setItems] = useState<FeedItem[]>(seed);
  const [pulse, setPulse] = useState<Pulse | null>(null);

  useEffect(() => {
    const id = setInterval(() => {
      const pick = seed[Math.floor(Math.random() * seed.length)];
      const now = new Date();
      const t = now.toLocaleTimeString("en-US", { hour12: false });
      const next: FeedItem = { ...pick, t };
      setItems((prev) => [next, ...prev].slice(0, 6));
      setPulse({
        t: now.getTime(),
        amp: pick.intensity,
        color: `var(--color-${pick.color})`,
      });
    }, 2600);
    return () => clearInterval(id);
  }, [seed]);

  return { items, pulse };
}

export { KPI, FEED_SEED };
export type { FeedItem, Pulse };
