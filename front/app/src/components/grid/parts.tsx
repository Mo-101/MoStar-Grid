import { useEffect, useRef, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { Glyph, type GlyphName } from "./glyph";
import {
  getGridStatus,
  getRecentMemory,
  getAdvisors,
  type GridStatus,
} from "@/services/gridApiClient";
import { voiceHealth } from "@/services/gridVoiceClient";

const KPI_META = [
  { key: "nodes",         label: "GRID NODES",     color: "neon-blue",   glyph: "target" as GlyphName },
  { key: "relationships", label: "RELATIONSHIPS",  color: "neon-cyan",   glyph: "spark"  as GlyphName },
  { key: "events",        label: "GRID EVENTS",    color: "neon-purple", glyph: "eye"    as GlyphName },
  { key: "utterances",    label: "WOO UTTERANCES", color: "neon-green",  glyph: "venus"  as GlyphName },
] as const;

const COUNCIL_GLYPHS: GlyphName[] = ["covenant", "spark", "target", "eye", "sun", "venus"];
const COUNCIL_TINTS = ["neon-gold", "neon-blue", "neon-cyan", "neon-green", "neon-purple", "neon-orange"];

type FeedItem = {
  agent: string; text: string; sev: "INFO" | "WARNING" | "ALERT";
  color: string; glyph: GlyphName; t: string; intensity: number;
};

const FEED_GLYPHS: GlyphName[] = ["target", "eye", "spark", "venus", "ban"];
const FEED_COLORS = ["neon-cyan", "neon-purple", "neon-blue", "neon-green", "neon-orange"];
const ALERT_PATTERN = /attack|killed|gunmen|crisis|outbreak|breach/i;

const SIDEBAR: { id: string; to: string; label: string; sub: string; glyph: GlyphName }[] = [
  { id: "overview",   to: "/",           label: "OVERVIEW",   sub: "Command Center",    glyph: "covenant" },
  { id: "council",    to: "/council",    label: "COUNCIL",    sub: "Live Agents",       glyph: "sun" },
  { id: "mindgraph",  to: "/mindgraph",  label: "MIND GRAPH", sub: "Knowledge Network", glyph: "target" },
  { id: "events",     to: "/events",     label: "EVENTS",     sub: "Real-time Feed",    glyph: "spark" },
  { id: "voice",      to: "/voice",      label: "VOICE",      sub: "Grid Voice Console",glyph: "venus" },
  { id: "conduit",    to: "/conduit",    label: "CONDUIT",    sub: "System Comms",      glyph: "eye" },
  { id: "memory",     to: "/memory",     label: "MEMORY",     sub: "Sacred Archive",    glyph: "eyeLight" },
  { id: "moscript",   to: "/moscript",   label: "MOSCRIPT",   sub: "MS Parking Lot",    glyph: "ban" },
];

function fmt(n: number) { return n.toLocaleString("en-US"); }

function timeAgo(iso: string): string {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  return `${hours}h ago`;
}

/* ============================ LIVE GRID DATA ============================ */
export function useGridStatus() {
  return useQuery({
    queryKey: ["grid-status"],
    queryFn: getGridStatus,
    refetchInterval: 20_000,
    staleTime: 10_000,
  });
}

export function useAdvisors() {
  return useQuery({
    queryKey: ["grid-advisors"],
    queryFn: getAdvisors,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

/** Live grid events + woo utterances, polled — drives the feed and the Code Conduit pulse. */
export function useLiveFeed() {
  const { data } = useQuery({
    queryKey: ["grid-recent-memory"],
    queryFn: () => getRecentMemory(8),
    refetchInterval: 15_000,
    staleTime: 5_000,
  });

  const items: FeedItem[] = [];
  if (data) {
    const events = data.events.map((e, i) => ({
      agent: e.type.replace(/_/g, " ").toUpperCase(),
      text: e.content,
      created_at: e.created_at,
      idx: i,
    }));
    const utterances = data.utterances.map((u, i) => ({
      agent: "WOO",
      text: u.content,
      created_at: u.created_at,
      idx: i,
    }));
    const merged = [...events, ...utterances]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 6);
    merged.forEach((m, i) => {
      items.push({
        agent: m.agent,
        text: m.text,
        sev: ALERT_PATTERN.test(m.text) ? "ALERT" : "INFO",
        color: FEED_COLORS[i % FEED_COLORS.length],
        glyph: FEED_GLYPHS[i % FEED_GLYPHS.length],
        t: timeAgo(m.created_at),
        intensity: ALERT_PATTERN.test(m.text) ? 1 : 0.5,
      });
    });
  }

  const latestTimestamp = data?.retrieved_at;
  const pulse: Pulse | null = latestTimestamp
    ? { t: new Date(latestTimestamp).getTime(), amp: items[0]?.intensity ?? 0.5, color: "var(--color-neon-cyan)" }
    : null;

  return { items, pulse, connected: data != null };
}

/* ============================ SIDEBAR ============================ */
export function Sidebar({ active }: { active: string }) {
  const { data: advisors } = useAdvisors();
  const advisorCount = advisors ? Object.keys(advisors).length : null;

  return (
    <aside className="panel flex h-full w-[220px] shrink-0 flex-col overflow-hidden px-3 py-4">
      <div className="flex flex-col gap-1">
        {SIDEBAR.map(({ id, to, label, sub, glyph }) => {
          const isActive = id === active;
          const subLabel = id === "council" && advisorCount != null ? `${advisorCount} Agents` : sub;
          return (
            <Link
              key={id}
              to={to}
              className={`group flex items-center gap-3 rounded-md px-3 py-2.5 text-left transition ${
                isActive
                  ? "bg-[oklch(0.25_0.08_260/0.6)] ring-1 ring-[var(--color-neon-gold)]/40"
                  : "hover:bg-white/5"
              }`}
            >
              <Glyph
                name={glyph}
                size={22}
                glow={isActive ? "var(--color-neon-gold)" : undefined}
              />
              <div className="leading-tight">
                <div className={`text-xs tracking-[0.18em] ${isActive ? "neon-text-gold" : "text-foreground/85"}`}>{label}</div>
                <div className="text-[10px] text-muted-foreground">{subLabel}</div>
              </div>
            </Link>
          );
        })}
      </div>

      <GridHealth compact />

      <div className="mt-auto flex flex-col items-center gap-2 pt-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full border border-[var(--color-neon-gold)]/40 bg-[oklch(0.22_0.08_80/0.25)] animate-pulse-ring">
          <Glyph name="covenant" size={32} glow="var(--color-neon-gold)" />
        </div>
        <div className="text-[10px] tracking-[0.25em] neon-text-gold">COVENANT MODE</div>
        <div className="text-[10px] tracking-[0.25em] text-[var(--color-neon-green)]">ENGAGED</div>
      </div>
    </aside>
  );
}

/* ============================ PAGE SHELL ============================ */
export function PageShell({ active, children }: { active: string; children: ReactNode }) {
  const { clock, dateLabel } = useClock();
  return (
    <div className="h-screen w-full overflow-hidden p-3">
      <div className="mx-auto flex h-full max-w-[1920px] items-stretch gap-3">
        <Sidebar active={active} />
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-3">
          <TopBar clock={clock} dateLabel={dateLabel} />
          <div className="flex min-h-0 flex-1 flex-col gap-3">{children}</div>
          <FooterBar />
        </div>
      </div>
    </div>
  );
}

/* ============================ TOPBAR ============================ */
export function TopBar({ clock, dateLabel }: { clock: string; dateLabel: string }) {
  return (
    <header className="panel flex items-center gap-6 px-5 py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-md border border-[var(--color-neon-gold)]/40">
          <Glyph name="covenant" size={28} glow="var(--color-neon-gold)" />
        </div>
        <div className="leading-tight">
          <div className="text-lg font-semibold tracking-wider neon-text-gold">MoStar GRID</div>
          <div className="text-[10px] tracking-[0.25em] text-muted-foreground">COVENANT COMMAND CENTER</div>
        </div>
      </div>

      <div className="mx-auto flex flex-col items-center">
        <div className="text-sm tracking-[0.35em] neon-text-cyan">
          MOSTAR GRID: <span className="neon-text-gold">COVENANT MODE ACTIVE</span>
        </div>
        <div className="mt-1 flex items-center gap-3 text-[10px] tracking-[0.25em] text-muted-foreground">
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
          <div className="text-[10px] tracking-[0.25em] text-muted-foreground">GRID TIME</div>
          <div className="text-2xl font-mono neon-text-cyan tabular-nums" suppressHydrationWarning>
            {clock || "--:--:--"}
          </div>
          <div className="text-[10px] tracking-[0.25em] text-muted-foreground" suppressHydrationWarning>
            {dateLabel}
          </div>
        </div>
        <div className="text-right leading-tight">
          <div className="text-[10px] tracking-[0.25em] text-muted-foreground">GRID STATUS</div>
          <div className="text-base tracking-[0.25em] neon-text-green">OPERATIONAL</div>
          <div className="mt-1 h-2 w-28 overflow-hidden rounded bg-white/5">
            <div className="h-full w-3/4 bg-[var(--color-neon-green)] animate-blink" />
          </div>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-md border border-[var(--color-neon-green)]/40">
          <Glyph name="target" size={28} glow="var(--color-neon-green)" />
        </div>
      </div>
    </header>
  );
}

/* ============================ KPI ============================ */
export function KpiCard({
  label, value, color, glyph, asOf,
}: { label: string; value: number | null; color: string; glyph: GlyphName; asOf: string | null }) {
  return (
    <div className="panel relative overflow-hidden p-4">
      <div className="flex items-start gap-4">
        <div
          className="flex h-14 w-14 items-center justify-center rounded-lg border"
          style={{
            borderColor: `color-mix(in oklab, var(--color-${color}) 50%, transparent)`,
            background: `color-mix(in oklab, var(--color-${color}) 14%, transparent)`,
          }}
        >
          <Glyph name={glyph} size={32} glow={`var(--color-${color})`} />
        </div>
        <div className="flex-1">
          <div className="text-[10px] tracking-[0.28em] text-muted-foreground">{label}</div>
          <div className="mt-1 text-3xl font-semibold tabular-nums" style={{ color: `var(--color-${color})` }}>
            {value == null ? "—" : fmt(value)}
          </div>
          <div className="text-[10px] tracking-[0.2em] neon-text-green">
            {asOf ? `LIVE · UPDATED ${asOf.toUpperCase()}` : "CONNECTING…"}
          </div>
        </div>
      </div>
    </div>
  );
}

/** Renders the four live KPI cards from the shared grid-status query. */
export function KpiRow() {
  const { data: status } = useGridStatus();
  const asOf = status ? timeAgo(status.density.timestamp) : null;
  const values: Record<(typeof KPI_META)[number]["key"], number | null> = {
    nodes: status?.mindgraph.nodes ?? null,
    relationships: status?.mindgraph.relationships ?? null,
    events: status?.density.label_distribution.GridEvent ?? null,
    utterances: status?.density.label_distribution.WooUtterance ?? null,
  };
  return (
    <>
      {KPI_META.map((k) => (
        <KpiCard key={k.key} label={k.label} value={values[k.key]} color={k.color} glyph={k.glyph} asOf={asOf} />
      ))}
    </>
  );
}

/* ============================ COUNCIL ============================ */
export function CouncilList() {
  const { data: advisors, isLoading } = useAdvisors();
  const entries = advisors ? Object.entries(advisors) : [];

  return (
    <div className="panel flex h-full flex-col p-4">
      <div className="mb-1 text-sm font-semibold tracking-[0.18em] neon-text-cyan">
        THE COUNCIL{entries.length ? ` · ${entries.length} AGENTS` : ""}
      </div>
      <div className="mb-3 text-[10px] tracking-[0.25em] text-muted-foreground">GUARDIANS OF THE GRID</div>
      <div className="flex-1 space-y-1.5 overflow-auto pr-1">
        {isLoading && (
          <div className="py-6 text-center text-[11px] tracking-[0.2em] text-muted-foreground">
            CONNECTING TO COUNCIL…
          </div>
        )}
        {!isLoading && entries.length === 0 && (
          <div className="py-6 text-center text-[11px] tracking-[0.2em] text-muted-foreground">
            COUNCIL OFFLINE — GRID API UNREACHABLE
          </div>
        )}
        {entries.map(([name, advisor], i) => {
          const glyph = COUNCIL_GLYPHS[i % COUNCIL_GLYPHS.length];
          const tint = COUNCIL_TINTS[i % COUNCIL_TINTS.length];
          return (
            <div key={name} className="flex items-center gap-3 rounded-md border border-white/5 bg-white/[0.02] px-3 py-2 hover:bg-white/5">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-md border"
                style={{
                  borderColor: `color-mix(in oklab, var(--color-${tint}) 50%, transparent)`,
                  background: `color-mix(in oklab, var(--color-${tint}) 14%, transparent)`,
                }}
              >
                <Glyph name={glyph} size={24} glow={`var(--color-${tint})`} />
              </div>
              <div className="flex-1 leading-tight">
                <div className="text-sm tracking-wider text-foreground">{name.toUpperCase()}</div>
                <div className="text-[10px] tracking-[0.2em] text-muted-foreground">
                  {advisor.specialty.slice(0, 3).join(" · ").toUpperCase()}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[var(--color-neon-green)] animate-blink" />
                <span className="text-[10px] tracking-[0.2em] neon-text-green">ACTIVE</span>
              </div>
            </div>
          );
        })}
      </div>
      <button className="mt-3 flex items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.03] py-2.5 text-xs tracking-[0.25em] text-muted-foreground hover:bg-white/5">
        VIEW COUNCIL DETAILS <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}

/* ============================ GLYPH PANEL ============================ */
function Quadrant({
  pos, color, title, kicker, words, glyph,
}: { pos: string; color: string; title: string; kicker: string; words: string; glyph: GlyphName }) {
  return (
    <div className={`absolute ${pos} flex w-44 flex-col items-start gap-1`}>
      <div className="flex items-center gap-2">
        <Glyph name={glyph} size={28} glow={`var(--color-${color})`} />
        <div className="text-lg font-semibold tracking-[0.2em]" style={{ color: `var(--color-${color})` }}>{title}</div>
      </div>
      <div className="text-[11px] tracking-[0.25em] text-muted-foreground">{kicker}</div>
      <div className="text-[10px] tracking-[0.2em] text-foreground/70">{words}</div>
    </div>
  );
}

export function GlyphPanel() {
  const ticks = Array.from({ length: 24 });
  return (
    <div className="panel relative h-full overflow-hidden p-4">
      <Quadrant pos="top-6 left-6"                       color="neon-gold"   title="IKANG"  kicker="MIND"    words="Logic · Will · Structure"  glyph="sun" />
      <Quadrant pos="top-6 right-6 items-end text-right" color="neon-cyan"   title="M MỌNG" kicker="ESSENCE" words="Pulse · Memory · Flow"     glyph="spark" />
      <Quadrant pos="bottom-6 left-6"                    color="neon-red"    title="ISONG"  kicker="SPIRIT"  words="Awakening · Change · Fire" glyph="ban" />
      <Quadrant pos="bottom-6 right-6 items-end text-right" color="neon-purple" title="AFIM"   kicker="BODY"    words="Form · Action · Creation"  glyph="eye" />

      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="relative aspect-square w-full max-w-[380px]" style={{ maxHeight: 380 }}>
          <div className="absolute inset-0 rounded-full border border-[var(--color-neon-blue)]/30 animate-spin-slow">
            {ticks.map((_, i) => {
              const angle = (i / ticks.length) * 360;
              return (
                <div
                  key={i}
                  className="absolute left-1/2 top-1/2 h-3 w-px bg-[var(--color-neon-cyan)]/50"
                  style={{ transform: `translate(-50%,-50%) rotate(${angle}deg) translateY(-185px)` }}
                />
              );
            })}
          </div>
          <div className="absolute inset-6 rounded-full border border-[var(--color-neon-gold)]/40 animate-spin-reverse" />
          <div className="absolute inset-12 rounded-full border border-[var(--color-neon-purple)]/40" />
          <div className="absolute inset-20 rounded-full border-2 border-[var(--color-neon-blue)]/70 shadow-[0_0_60px_oklch(0.72_0.20_245/0.5)] animate-pulse-ring" />
          <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-[var(--color-neon-cyan)]/30 to-transparent" />
          <div className="absolute top-1/2 left-0 h-px w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-[var(--color-neon-cyan)]/30 to-transparent" />
          <div className="absolute inset-0 grid place-items-center">
            <div className="flex h-28 w-28 items-center justify-center rounded-full border border-[var(--color-neon-gold)]/60 bg-[oklch(0.18_0.06_270/0.7)] shadow-[0_0_40px_oklch(0.82_0.16_85/0.35)]">
              <Glyph name="covenant" size={68} glow="var(--color-neon-blue)" />
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
          const age = (now - p.t) / 1000;          // seconds since pulse
          const speed = 38;                        // bars / second outward
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
          <div className="text-[10px] tracking-[0.3em] text-muted-foreground">
            ALL GLYPHS · ALL LAYERS · ALL TIME
          </div>
        </div>
        <div className="flex items-center gap-3">
          {(["sun","spark","target","eye","ban","venus"] as GlyphName[]).map((g, i) => (
            <div key={g} className="flex items-center gap-2">
              <Glyph name={g} size={22} glow={`var(--color-neon-${["gold","cyan","blue","purple","red","gold"][i]})`} />
              {i < 5 && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
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
            <div key={i} className="flex h-full flex-1 flex-col items-stretch justify-center gap-[1px]">
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

      <div className="mt-2 flex items-center justify-between text-[10px] tracking-[0.25em] text-muted-foreground">
        <span>LIVE FREQUENCY · {Math.round(heights.reduce((a, b) => a + b, 0) / heights.length)} Hz</span>
        <span className="neon-text-cyan">LISTENING</span>
      </div>
    </div>
  );
}

/* ============================ GRID FEED ============================ */
export function GridFeed({ items, connected }: { items: FeedItem[]; connected: boolean }) {
  return (
    <div className="panel flex h-full flex-col p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">REAL-TIME GRID FEED</div>
      <div className="text-[10px] tracking-[0.25em] text-muted-foreground">
        {connected ? "LIVE ACTIVITY STREAM" : "AWAITING GRID API CONNECTION"}
      </div>
      <div className="mt-3 flex-1 space-y-2.5 overflow-y-auto pr-1">
        {items.length === 0 && (
          <div className="py-6 text-center text-[11px] tracking-[0.2em] text-muted-foreground">
            {connected ? "NO RECENT ACTIVITY" : "FEED OFFLINE — GRID API UNREACHABLE"}
          </div>
        )}
        {items.map((f, i) => (
          <div key={i} className="flex items-start gap-3 rounded-md border border-white/5 bg-white/[0.02] px-3 py-2">
            <div
              className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-md border"
              style={{
                borderColor: `color-mix(in oklab, var(--color-${f.color}) 50%, transparent)`,
                background: `color-mix(in oklab, var(--color-${f.color}) 14%, transparent)`,
              }}
            >
              <Glyph name={f.glyph} size={22} glow={`var(--color-${f.color})`} />
            </div>
            <div className="flex-1 leading-tight">
              <div className="text-sm">
                <span className="font-semibold" style={{ color: `var(--color-${f.color})` }}>{f.agent}</span>{" "}
                <span className="text-foreground/85">{f.text}</span>
              </div>
              <div className="text-[10px] tracking-[0.2em] text-muted-foreground">
                SEVERITY: <span style={{ color: `var(--color-${f.color})` }}>{f.sev}</span>
              </div>
            </div>
            <div className="text-[10px] tabular-nums text-muted-foreground">{f.t}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================ GRID HEALTH ============================ */
type HealthCheck = { label: string; status: string; ok: boolean };

function useHealthChecks() {
  const { data: status } = useGridStatus();
  const { data: voice } = useQuery({
    queryKey: ["voice-health"],
    queryFn: voiceHealth,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const checks: HealthCheck[] = [
    { label: "NEO4J", ok: status?.mindgraph.status === "connected", status: status ? status.mindgraph.status.toUpperCase() : "—" },
    { label: "DCX TRINITY", ok: !!status?.dcx.connected, status: status ? (status.dcx.connected ? "ONLINE" : "OFFLINE") : "—" },
    { label: "OLLAMA MODELS", ok: !!status && Object.keys(status.dcx.models).length > 0, status: status ? `${Object.keys(status.dcx.models).length} LOADED` : "—" },
    { label: "PIPER TTS", ok: voice?.status === "healthy", status: voice ? voice.status.toUpperCase() : "—" },
    { label: "QUEUE", ok: status ? status.queue.pending === 0 : false, status: status ? (status.queue.pending === 0 ? "CLEAR" : `${status.queue.pending} PENDING`) : "—" },
  ];

  const known = checks.filter((c) => c.status !== "—");
  const pct = known.length ? Math.round((known.filter((c) => c.ok).length / known.length) * 100) : 0;
  return { checks, pct };
}

export function GridHealth({ compact = false }: { compact?: boolean }) {
  const { checks, pct } = useHealthChecks();
  const r = compact ? 34 : 46, c = 2 * Math.PI * r;

  if (compact) {
    return (
      <div className="border-t border-white/5 pt-3">
        <div className="text-[10px] tracking-[0.2em] neon-text-cyan">GRID HEALTH</div>
        <div className="text-[9px] tracking-[0.16em] text-muted-foreground">SYSTEM VITALS</div>
        <div className="relative mx-auto mt-2 h-20 w-20">
          <svg viewBox="0 0 88 88" className="h-full w-full -rotate-90">
            <circle cx="44" cy="44" r={r} stroke="oklch(1 0 0 / 0.08)" strokeWidth="6" fill="none" />
            <circle
              cx="44" cy="44" r={r}
              stroke="var(--color-neon-green)" strokeWidth="6" fill="none"
              strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
              strokeLinecap="round"
              style={{ filter: "drop-shadow(0 0 6px var(--color-neon-green))" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-sm font-semibold neon-text-green tabular-nums">{pct}%</div>
          </div>
        </div>
        <div className="mt-2 space-y-1 text-[9px]">
          {checks.map((h) => (
            <div key={h.label} className="flex items-center justify-between gap-2">
              <span className="truncate tracking-[0.08em] text-foreground/75">{h.label}</span>
              <span className={`shrink-0 tracking-[0.08em] ${h.ok ? "neon-text-green" : "text-muted-foreground"}`}>{h.status}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="panel p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">GRID HEALTH</div>
      <div className="text-[10px] tracking-[0.25em] text-muted-foreground">SYSTEM VITALS</div>
      <div className="mt-3 flex items-center gap-4">
        <div className="relative h-28 w-28 shrink-0">
          <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
            <circle cx="60" cy="60" r={r} stroke="oklch(1 0 0 / 0.08)" strokeWidth="8" fill="none" />
            <circle
              cx="60" cy="60" r={r}
              stroke="var(--color-neon-green)" strokeWidth="8" fill="none"
              strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
              strokeLinecap="round"
              style={{ filter: "drop-shadow(0 0 8px var(--color-neon-green))" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-2xl font-semibold neon-text-green tabular-nums">{pct}%</div>
            <div className="text-[10px] tracking-[0.25em] text-muted-foreground">{pct >= 80 ? "OPTIMAL" : pct > 0 ? "DEGRADED" : "OFFLINE"}</div>
          </div>
        </div>
        <div className="flex-1 space-y-1.5 text-xs">
          {checks.map((h) => (
            <div key={h.label} className="flex items-center justify-between">
              <span className="tracking-[0.18em] text-foreground/85">{h.label}</span>
              <span className={`tracking-[0.18em] ${h.ok ? "neon-text-green" : "text-muted-foreground"}`}>{h.status}</span>
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
    { label: "STARTUP SEQUENCE", glyph: "sun",      tint: "neon-gold" },
    { label: "COUNCIL CHECK-IN", glyph: "target",   tint: "neon-cyan" },
    { label: "TRUTH AUDIT",      glyph: "eye",      tint: "neon-purple" },
    { label: "GRID SYNCHRONIZE", glyph: "spark",    tint: "neon-blue" },
  ];
  return (
    <div className="panel p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">QUICK COMMANDS</div>
      <div className="text-[10px] tracking-[0.25em] text-muted-foreground">INITIATE PROTOCOL</div>
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
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </button>
        ))}
      </div>
    </div>
  );
}

/* ============================ FOOTER ============================ */
export function FooterBar() {
  return (
    <div className="panel flex shrink-0 flex-col gap-1.5 px-5 py-2.5">
      <p className="truncate text-xs leading-tight text-foreground/85">
        <span className="font-semibold tracking-[0.2em] neon-text-gold">COVENANT OATH · </span>
        We observe what is real. We protect what matters. We evolve what is next.{" "}
        <span className="font-semibold tracking-[0.18em] neon-text-cyan">WE ARE THE MOSTAR GRID.</span>
      </p>
      <div className="flex items-center justify-between text-[10px] tracking-[0.25em] text-muted-foreground">
        <div className="flex gap-6">
          <span>COVENANT MODE: <span className="neon-text-green">ENGAGED</span></span>
          <span>MSG-01 ALIGNMENT: <span className="neon-text-cyan">TRUE</span></span>
          <span>GRID PROTOCOL: <span className="neon-text-gold">v1.0.0</span></span>
        </div>
        <div>BUILT BY FLAME · SEALED BY CODE · PROTECTED BY COVENANT</div>
      </div>
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
      ? t.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }).toUpperCase()
      : "",
  };
}

export { KPI_META };
export type { FeedItem, Pulse, GridStatus };
