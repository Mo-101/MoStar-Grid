 import { useEffect, useRef, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { Glyph, type GlyphName } from "./glyph";
import logoImg from "../../assets/elements/MStarLg.png";
import {
  getGridStatus,
  getRecentMemory,
  getAdvisors,
  type GridStatus,
} from "@/services/gridApiClient";
import { voiceHealth } from "@/services/gridVoiceClient";
import { GRID_ELEMENTS } from "@/lib/gridElements";
import { GRID_REFRESH } from "@/lib/grid-refresh-policy";
import {
  worst,
  timeAgo,
  liveBadge,
  freshnessOf,
  SEVERITY_COLOR,
  SEVERITY_VERDICT,
  type Severity,
} from "@/lib/gridTruth";

const KPI_META = [
  { key: "nodes", label: "GRID NODES", color: "neon-blue", glyph: "target" as GlyphName },
  { key: "relationships", label: "RELATIONSHIPS", color: "neon-cyan", glyph: "spark" as GlyphName },
  { key: "events", label: "GRID EVENTS", color: "neon-purple", glyph: "eye" as GlyphName },
  { key: "utterances", label: "WOO UTTERANCES", color: "neon-green", glyph: "venus" as GlyphName },
] as const;

const COUNCIL_GLYPHS: GlyphName[] = ["covenant", "spark", "target", "eye", "sun", "venus"];
const COUNCIL_TINTS = [
  "neon-gold",
  "neon-blue",
  "neon-cyan",
  "neon-green",
  "neon-purple",
  "neon-orange",
];

type FeedItem = {
  agent: string;
  text: string;
  sev: "INFO" | "WARNING" | "ALERT";
  color: string;
  glyph: GlyphName;
  at: string;
  intensity: number;
};

const FEED_GLYPHS: GlyphName[] = ["target", "eye", "spark", "venus", "ban"];
const FEED_COLORS = ["neon-cyan", "neon-purple", "neon-blue", "neon-green", "neon-orange"];
const ALERT_PATTERN = /attack|killed|gunmen|crisis|outbreak|breach/i;

const SIDEBAR: { id: string; to: string; label: string; sub: string; glyph: GlyphName }[] = [
  { id: "overview", to: "/", label: "OVERVIEW", sub: "Command Center", glyph: "covenant" },
  {
    id: "continent-optics",
    to: "/continent-optics",
    label: "CONTINENT OPTICS",
    sub: "Africa Sensing",
    glyph: "eyeLight",
  },
  { id: "council", to: "/council", label: "COUNCIL", sub: "Live Agents", glyph: "sun" },
  {
    id: "mindgraph",
    to: "/mindgraph",
    label: "MIND GRAPH",
    sub: "Knowledge Network",
    glyph: "target",
  },
  { id: "events", to: "/events", label: "EVENTS", sub: "Real-time Feed", glyph: "spark" },
  { id: "voice", to: "/voice", label: "VOICE", sub: "Grid Voice Console", glyph: "venus" },
  { id: "conduit", to: "/conduit", label: "CONDUIT", sub: "System Comms", glyph: "eye" },
  { id: "memory", to: "/memory", label: "MEMORY", sub: "Sacred Archive", glyph: "eyeLight" },
  { id: "moscript", to: "/moscript", label: "MOSCRIPT", sub: "MS Parking Lot", glyph: "ban" },
];

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

/* ============================ LIVE GRID DATA ============================ */
export function useGridStatus() {
  return useQuery({
    queryKey: ["grid-status"],
    queryFn: getGridStatus,
    refetchInterval: GRID_REFRESH.CANONICAL_MS,
    staleTime: GRID_REFRESH.CANONICAL_STALE_MS,
    refetchOnWindowFocus: false,
  });
}

export function useAdvisors() {
  return useQuery({
    queryKey: ["grid-advisors"],
    queryFn: getAdvisors,
    refetchInterval: GRID_REFRESH.CANONICAL_MS,
    staleTime: GRID_REFRESH.CANONICAL_STALE_MS,
    refetchOnWindowFocus: false,
  });
}

export function useLiveFeed() {
  const { data } = useQuery({
    queryKey: ["grid-recent-memory"],
    queryFn: () => getRecentMemory(8),
    refetchInterval: GRID_REFRESH.SIGNAL_FEED_MS,
    staleTime: GRID_REFRESH.SIGNAL_STALE_MS,
  });

  const items: FeedItem[] = [];
  if (data) {
    const events = data.events.map((e) => ({
      agent: e.type.replace(/_/g, " ").toUpperCase(),
      text: e.content,
      created_at: e.created_at,
    }));
    const utterances = data.utterances.map((u) => ({
      agent: "WOO",
      text: u.content,
      created_at: u.created_at,
    }));
    [...events, ...utterances]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 6)
      .forEach((m, i) => {
        const alert = ALERT_PATTERN.test(m.text);
        items.push({
          agent: m.agent,
          text: m.text,
          sev: alert ? "ALERT" : "INFO",
          color: FEED_COLORS[i % FEED_COLORS.length],
          glyph: FEED_GLYPHS[i % FEED_GLYPHS.length],
          at: m.created_at,
          intensity: alert ? 1 : 0.5,
        });
      });
  }

  const pulse: Pulse | null = data?.retrieved_at
    ? {
        t: new Date(data.retrieved_at).getTime(),
        amp: items[0]?.intensity ?? 0.5,
        color: "var(--color-neon-cyan)",
      }
    : null;

  return {
    items,
    pulse,
    /** Reachable. NOT the same as current — see newestAt. */
    reachable: data != null,
    /** Age of the freshest item. This is what the header is allowed to claim. */
    newestAt: items[0]?.at ?? null,
    retrievedAt: data?.retrieved_at ?? null,
  };
}

/* ============================ GRID HEALTH ============================ */
/**
 * A check reports a severity, not a boolean. Criticality decides whether it
 * can drag the whole verdict down. The old code averaged five booleans and
 * printed the mean in green — which is how DCX TRINITY: OFFLINE came to sit
 * under an 80% healthy ring.
 */
export type HealthCheck = {
  label: string;
  status: string;
  severity: Severity;
  critical: boolean;
  note?: string;
};

export function useHealthChecks() {
  const { data: status } = useGridStatus();
  const { data: voice } = useQuery({
    queryKey: ["voice-health"],
    queryFn: voiceHealth,
    refetchInterval: GRID_REFRESH.SERVICE_HEALTH_MS,
    staleTime: GRID_REFRESH.SERVICE_HEALTH_STALE_MS,
  });

  // Model counts must come from what the server actually FOUND, never from
  // how many are configured. `Object.keys(status.dcx.models).length` is
  // always 3 (the config), so it reported "3 models loaded" on a host that
  // held one. present_models is measured; models is declared.
  const expectedCount = status ? Object.keys(status.dcx.models).length : 0;
  const presentCount = status?.dcx.present_models?.length ?? 0;
  const missing = status?.dcx.missing_models ?? [];
  const shortName = (m: string) => m.split(":").pop() ?? m;

  // `connected` means Ollama is reachable — it never means the trinity is
  // sealed. Only the deep probe (/api/health) may report SEALED, so this
  // cheap path can reach at most LOADED. Collapsing PARTIAL into SEALED is
  // exactly the defect this replaces.
  const dcx: HealthCheck = ((): HealthCheck => {
    const label = "DCX TRINITY";
    if (!status) return { label, status: "—", severity: "UNKNOWN", critical: true };

    switch (status.dcx.state) {
      case "SEALED":
        return { label, status: "SEALED", severity: "SEALED", critical: true };
      case "LOADED":
        return {
          label,
          status: "LOADED",
          severity: "DEGRADED",
          critical: true,
          note: `${presentCount}/${expectedCount} present, live validation pending`,
        };
      case "PARTIAL":
        return {
          label,
          status: "PARTIAL",
          severity: "DEGRADED",
          critical: true,
          note: `${presentCount}/${expectedCount} present — missing ${missing.map(shortName).join(", ")}`,
        };
      case "DEGRADED":
        return {
          label,
          status: "DEGRADED",
          severity: "DEGRADED",
          critical: true,
          note: `${presentCount}/${expectedCount} present, validation failed`,
        };
      case "ABSENT":
        return {
          label,
          status: "ABSENT",
          severity: "DOWN",
          critical: true,
          note: "no trinity model pulled",
        };
      case "UNREACHABLE":
        return {
          label,
          status: "UNREACHABLE",
          severity: "DOWN",
          critical: true,
          note: "Ollama not reachable",
        };
      default:
        // Server predates the seal-state contract. Report the gap rather
        // than guessing a verdict from `connected`.
        return {
          label,
          status: "UNVERIFIED",
          severity: "UNKNOWN",
          critical: true,
          note: "server did not report a trinity seal state",
        };
    }
  })();

  const checks: HealthCheck[] = [
    {
      label: "NEO4J",
      status: status ? status.mindgraph.status.toUpperCase() : "—",
      severity: !status ? "UNKNOWN" : status.mindgraph.status === "connected" ? "SEALED" : "DOWN",
      critical: true,
    },
    dcx,
    {
      // Was `${modelCount} LOADED` where modelCount was the CONFIGURED
      // count — it printed "3 LOADED" on a host holding one model.
      //
      // Then it printed "0/3 PULLED" whenever Ollama was unreachable,
      // which is a different lie: an unanswered host was rendered as an
      // empty one. present_models is only evidence about what is pulled
      // when the transport was up long enough to ask. When it is down we
      // know nothing about the models, and NOT KNOWN is the honest word.
      label: "OLLAMA MODELS",
      status: !status
        ? "—"
        : !status.dcx.connected
          ? "NOT KNOWN"
          : `${presentCount}/${expectedCount} PULLED`,
      severity: !status
        ? "UNKNOWN"
        : !status.dcx.connected
          ? "UNKNOWN"
          : presentCount === expectedCount && expectedCount > 0
            ? "SEALED"
            : presentCount > 0
              ? "DEGRADED"
              : "DOWN",
      critical: false,
      note: status && !status.dcx.connected ? "Ollama unreachable — model presence unverified" : undefined,
    },
    {
      label: "PIPER TTS",
      status: voice ? voice.status.toUpperCase() : "—",
      severity: !voice
        ? "UNKNOWN"
        : voice.status === "healthy"
          ? "SEALED"
          : voice.status === "degraded"
            ? "DEGRADED"
            : "DOWN",
      critical: false,
    },
    {
      label: "QUEUE",
      status: status
        ? status.queue.pending === 0
          ? "CLEAR"
          : `${status.queue.pending} PENDING`
        : "—",
      severity: !status ? "UNKNOWN" : status.queue.pending === 0 ? "SEALED" : "DEGRADED",
      critical: false,
    },
  ];

  const verdict = worst(checks.filter((c) => c.critical).map((c) => c.severity));
  const sealed = checks.filter((c) => c.severity === "SEALED").length;
  const degradedLabels = checks.filter((c) => c.severity !== "SEALED").map((c) => c.label);

  return {
    checks,
    verdict,
    sealed,
    total: checks.length,
    degradedLabels,
    asOf: status?.density.timestamp ?? null,
  };
}

export function GridHealth({ compact = false }: { compact?: boolean }) {
  const { checks, verdict, sealed, total } = useHealthChecks();
  const r = compact ? 34 : 46;
  const c = 2 * Math.PI * r;
  const fill = total ? sealed / total : 0;
  const color = SEVERITY_COLOR[verdict];

  const ring = (
    <svg viewBox={compact ? "0 0 88 88" : "0 0 120 120"} className="h-full w-full -rotate-90">
      <circle
        cx={compact ? 44 : 60}
        cy={compact ? 44 : 60}
        r={r}
        stroke="oklch(1 0 0 / 0.08)"
        strokeWidth={compact ? 6 : 8}
        fill="none"
      />
      <circle
        cx={compact ? 44 : 60}
        cy={compact ? 44 : 60}
        r={r}
        stroke={color}
        strokeWidth={compact ? 6 : 8}
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - fill)}
        strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 ${compact ? 6 : 8}px ${color})` }}
      />
    </svg>
  );

  const rows = checks.map((h) => (
    <div key={h.label} className="flex items-baseline justify-between gap-2">
      <span className="truncate tracking-[0.08em] text-foreground/75">{h.label}</span>
      <span className="shrink-0 tracking-[0.08em]" style={{ color: SEVERITY_COLOR[h.severity] }}>
        {h.status}
      </span>
    </div>
  ));

  if (compact) {
    return (
      <div className="border-t border-white/5 pt-3">
        <div className="text-[10px] tracking-[0.2em] neon-text-cyan">GRID HEALTH</div>
        <div className="text-[9px] tracking-[0.16em] text-muted-foreground">SYSTEM VITALS</div>
        <div className="relative mx-auto mt-2 h-20 w-20">
          {ring}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-sm font-semibold tabular-nums" style={{ color }}>
              {sealed}/{total}
            </div>
            <div className="text-[8px] tracking-[0.12em]" style={{ color }}>
              {SEVERITY_VERDICT[verdict]}
            </div>
          </div>
        </div>
        <div className="mt-2 space-y-1 text-[9px]">{rows}</div>
      </div>
    );
  }

  return (
    <div className="panel p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">GRID HEALTH</div>
      <div className="text-[10px] tracking-[0.25em] text-muted-foreground">SYSTEM VITALS</div>
      <div className="mt-3 flex items-center gap-4">
        <div className="relative h-28 w-28 shrink-0">
          {ring}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-2xl font-semibold tabular-nums" style={{ color }}>
              {sealed}/{total}
            </div>
            <div className="text-[10px] tracking-[0.2em]" style={{ color }}>
              {SEVERITY_VERDICT[verdict]}
            </div>
          </div>
        </div>
        <div className="flex-1 space-y-1.5 text-xs">
          {checks.map((h) => (
            <div key={h.label}>
              <div className="flex items-center justify-between">
                <span className="tracking-[0.18em] text-foreground/85">{h.label}</span>
                <span className="tracking-[0.18em]" style={{ color: SEVERITY_COLOR[h.severity] }}>
                  {h.status}
                </span>
              </div>
              {h.note && <div className="text-[10px] text-muted-foreground">{h.note}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ============================ SIDEBAR ============================ */
export function Sidebar({ active }: { active: string }) {
  const { data: advisors } = useAdvisors();
  const advisorCount = advisors ? Object.keys(advisors).length : null;

  return (
    <aside className="panel flex h-full w-[220px] shrink-0 flex-col overflow-hidden rounded-none px-3 py-4">
      <div className="flex flex-col gap-1">
        {SIDEBAR.map(({ id, to, label, sub, glyph }) => {
          const isActive = id === active;
          const subLabel =
            id === "council" && advisorCount != null ? `${advisorCount} Agents` : sub;
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
                size={28}
              />
              <div className="leading-tight">
                <div
                  className={`text-xs tracking-[0.18em] ${isActive ? "neon-text-gold" : "text-foreground/85"}`}
                >
                  {label}
                </div>
                <div className="text-[10px] text-muted-foreground">{subLabel}</div>
              </div>
            </Link>
          );
        })}
      </div>

      <GridHealth compact />

      <div className="mt-auto flex flex-col items-center gap-2 pt-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-full border border-[var(--color-neon-gold)]/20 bg-[oklch(0.22_0.08_80/0.25)]">
          <Glyph name="covenant" size={36} />
        </div>
        <div className="text-[10px] tracking-[0.25em] neon-text-gold">COVENANT MODE</div>
        <div className="text-[10px] tracking-[0.25em] text-[var(--color-neon-green)]">ENGAGED</div>
      </div>
    </aside>
  );
}

/* ============================ PAGE SHELL ============================ */
export function PageShell({
  active,
  children,
  footerSlot,
}: {
  active: string;
  children: ReactNode;
  footerSlot?: ReactNode;
}) {
  const { clock, dateLabel } = useClock();
  return (
    <div className="h-screen w-full overflow-hidden">
      <div className="mx-auto flex h-full max-w-[1920px] items-stretch">
        <Sidebar active={active} />
        <div className="flex min-w-0 flex-1 flex-col gap-3 overflow-y-auto p-3">
          <TopBar clock={clock} dateLabel={dateLabel} />
          <div className="flex flex-1 flex-col gap-3">{children}</div>
          <FooterBar voiceSlot={footerSlot} />
        </div>
      </div>
    </div>
  );
}

/* ============================ TOPBAR ============================ */
export function TopBar({ clock, dateLabel }: { clock: string; dateLabel: string }) {
  const { verdict, sealed, total } = useHealthChecks();
  const color = SEVERITY_COLOR[verdict];

  return (
    <header className="panel flex shrink-0 items-center gap-6 px-5 py-3">
      <div className="flex items-center gap-3">
        <img
          src={logoImg}
          alt="MoStar"
          className="h-12 w-12 rounded-md border border-[var(--color-neon-gold)]/40 object-contain p-1"
        />
        <div className="leading-tight">
          <div className="text-lg font-semibold tracking-wider neon-text-gold">MoStar GRID</div>
          <div className="text-[10px] tracking-[0.25em] text-muted-foreground">
            COVENANT COMMAND CENTER
          </div>
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
          <div
            className="text-[10px] tracking-[0.25em] text-muted-foreground"
            suppressHydrationWarning
          >
            {dateLabel}
          </div>
        </div>
        <div className="text-right leading-tight">
          <div className="text-[10px] tracking-[0.25em] text-muted-foreground">GRID STATUS</div>
          <div className="text-base tracking-[0.25em]" style={{ color }}>
            {SEVERITY_VERDICT[verdict]}
          </div>
          <div className="mt-1 h-2 w-28 overflow-hidden rounded bg-white/5">
            <div
              className="h-full transition-[width]"
              style={{ width: `${(sealed / total) * 100}%`, background: color }}
            />
          </div>
        </div>
        <div
          className="flex h-12 w-12 items-center justify-center rounded-md border"
          style={{ borderColor: `color-mix(in oklab, ${color} 40%, transparent)` }}
        >
          <Glyph name="target" size={28} />
        </div>
      </div>
    </header>
  );
}

/* ============================ KPI ============================ */
export function KpiCard({
  label,
  value,
  color,
  glyph,
  asOf,
}: {
  label: string;
  value: number | null;
  color: string;
  glyph: GlyphName;
  asOf: string | null;
}) {
  const badge = liveBadge(asOf);
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
          <Glyph name={glyph} size={32} />
        </div>
        <div className="flex-1">
          <div className="text-[10px] tracking-[0.28em] text-muted-foreground">{label}</div>
          <div
            className="mt-1 text-3xl font-semibold tabular-nums"
            style={{ color: `var(--color-${color})` }}
          >
            {value == null ? "—" : fmt(value)}
          </div>
          {/* LIVE is earned by a timestamp, never printed by default. */}
          <div className="text-[10px] tracking-[0.2em]" style={{ color: badge.color }}>
            {badge.text}
          </div>
        </div>
      </div>
    </div>
  );
}

export function KpiRow() {
  const { data: status } = useGridStatus();
  const asOf = status?.density.timestamp ?? null;
  const values: Record<(typeof KPI_META)[number]["key"], number | null> = {
    nodes: status?.mindgraph.nodes ?? null,
    relationships: status?.mindgraph.relationships ?? null,
    events: status?.density.label_distribution.GridEvent ?? null,
    utterances: status?.density.label_distribution.WooUtterance ?? null,
  };
  return (
    <>
      {KPI_META.map((k) => (
        <KpiCard
          key={k.key}
          label={k.label}
          value={values[k.key]}
          color={k.color}
          glyph={k.glyph}
          asOf={asOf}
        />
      ))}
    </>
  );
}

/* ============================ COUNCIL ============================ */
export function CouncilList() {
  const { data: advisors, isLoading } = useAdvisors();
  const entries = advisors ? Object.entries(advisors) : [];

  return (
    <div className="panel flex h-195 flex-col p-4">
      <div className="mb-1 text-sm font-semibold tracking-[0.18em] neon-text-cyan">
        THE COUNCIL{entries.length ? ` · ${entries.length} AGENTS` : ""}
      </div>
      <div className="mb-3 text-[10px] tracking-[0.25em] text-muted-foreground">
        GUARDIANS OF THE GRID
      </div>
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

          // The old code hardcoded a green ACTIVE dot on every advisor.
          // That is self-attestation: the row asserting its own liveness.
          // An advisor is ACTIVE only if it reported in recently; otherwise
          // it is REGISTERED, which is all the API actually proves.
          const lastSeen = (advisor as { last_seen?: string }).last_seen ?? null;
          const fresh = freshnessOf(lastSeen);
          const live = fresh === "LIVE" || fresh === "RECENT";
          const stateLabel = lastSeen
            ? live
              ? "ACTIVE"
              : timeAgo(lastSeen).toUpperCase()
            : "REGISTERED";
          const stateColor = lastSeen
            ? live
              ? "var(--color-neon-green)"
              : "var(--color-neon-orange)"
            : "oklch(0.62 0.02 260)";

          return (
            <div
              key={name}
              className="flex items-center gap-3 rounded-md border border-white/5 bg-white/[0.02] px-3 py-2 hover:bg-white/5"
            >
              <div
                className="flex h-10 w-10 items-center justify-center rounded-md border"
                style={{
                  borderColor: `color-mix(in oklab, var(--color-${tint}) 50%, transparent)`,
                  background: `color-mix(in oklab, var(--color-${tint}) 14%, transparent)`,
                }}
              >
                <Glyph name={glyph} size={30} />
              </div>
              <div className="flex-1 leading-tight">
                <div className="text-sm tracking-wider text-foreground">{name.toUpperCase()}</div>
                <div className="text-[10px] tracking-[0.2em] text-muted-foreground">
                  {advisor.specialty.slice(0, 3).join(" · ").toUpperCase()}
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: stateColor }} />
                <span className="text-[10px] tracking-[0.2em]" style={{ color: stateColor }}>
                  {stateLabel}
                </span>
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

/* ============================ THE FOUR ============================ */
/**
 * Rendered from GRID_ELEMENTS. Name, element, aspect and triad travel
 * together as one object, so the rotation that put ISONG in the fire panel
 * cannot recur.
 */
function Quadrant({ pos, element }: { pos: string; element: (typeof GRID_ELEMENTS)[number] }) {
  return (
    <div className={`absolute ${pos} flex w-40 flex-col items-start gap-1`}>
      <div className="flex items-center gap-2">
        <Glyph name={element.glyph} size={68} />
        <div
          className="text-lg font-semibold tracking-[0.2em]"
          style={{ color: `var(--color-${element.tint})` }}
        >
          {element.name}
        </div>
      </div>
      <div className="text-[10px] tracking-[0.25em] text-muted-foreground">
        <span aria-hidden>{element.sigil}</span> {element.element} · {element.aspect}
      </div>
      <div className="text-[10px] tracking-[0.2em] text-foreground/70">
        {element.triad.join(" · ")}
      </div>
      {element.reverence && (
        <div className="text-[9px] tracking-[0.16em] text-muted-foreground/70">
          {element.reverence}
        </div>
      )}
    </div>
  );
}

export function GlyphPanel() {
  const ticks = Array.from({ length: 68 });
  const [ikang, mmong, afim, isong] = GRID_ELEMENTS;

  return (
    <div className="panel relative h-150 overflow-hidden p-4">
      <Quadrant pos="top-6 left-6 items-start" element={afim} />
      <Quadrant pos="top-6 right-6 items-end text-right" element={mmong} />
      <Quadrant pos="bottom-6 left-6" element={ikang} />
      <Quadrant pos="bottom-6 right-6 items-end text-right" element={isong} />

      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="relative aspect-square w-full max-w-[380px]" style={{ maxHeight: 380 }}>
          <div className="absolute inset-0 rounded-full border border-[var(--color-neon-blue)]/30 animate-spin-slow">
            {ticks.map((_, i) => (
              <div
                key={i}
                className="absolute left-1/2 top-1/2 h-3 w-px bg-[var(--color-neon-cyan)]/80"
                style={{
                  transform: `translate(-50%,-50%) rotate(${(i / ticks.length) * 360}deg) translateY(-185px)`,
                }}
              />
            ))}
          </div>
          <div className="absolute inset-6 rounded-full border border-[var(--color-neon-gold)]/40 animate-spin-reverse" />
          <div className="absolute inset-12 rounded-full border border-[var(--color-neon-purple)]/40" />
          <div className="absolute inset-20 rounded-full border-2 border-[var(--color-neon-blue)]/70 shadow-[0_0_60px_oklch(0.72_0.20_245/0.5)]" />
          <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-[var(--color-neon-cyan)]/30 to-transparent" />
          <div className="absolute top-1/2 left-0 h-px w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-[var(--color-neon-cyan)]/30 to-transparent" />
          <div className="absolute inset-0 grid place-items-center">
            <div className="flex h-40 w-40 items-center justify-center rounded-full border border-[var(--color-neon-gold)]/60 bg-[oklch(0.18_0.06_270/0.7)] shadow-[0_0_40px_oklch(0.82_0.16_85/0.35)]">
              <Glyph name="core" size={112} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================ CODE CONDUIT ============================ */
type Pulse = { t: number; amp: number; color: string };

export function CodeConduit({ pulse, connected }: { pulse: Pulse | null; connected: boolean }) {
  const BARS = 96;
  const [heights, setHeights] = useState<number[]>(() => Array(BARS).fill(20));
  const pulsesRef = useRef<Pulse[]>([]);
  const phaseRef = useRef(0);
  const lastPulseRef = useRef<number>(-1);

  useEffect(() => {
    if (!pulse || pulse.t === lastPulseRef.current) return;
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
          const age = (now - p.t) / 1000;
          const front = age * 38;
          const dist = Math.abs(i - BARS / 2);
          const env = Math.exp(-Math.pow(dist - front, 2) / 72);
          pulseAdd += env * Math.exp(-age * 1.2) * p.amp * 70;
        }
        next[i] = Math.min(100, base + pulseAdd);
      }
      setHeights(next);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const active = pulsesRef.current.length;

  return (
    <div className="panel h-40 p-2">
      <div className="flex items-center h-8 justify-between">
        <div>
          <div className="text-sm tracking-[0.3em] neon-text-cyan">CODE CONDUIT</div>
          <div className="text-[10px] tracking-[0.3em] text-muted-foreground">
            ALL GLYPHS · ALL LAYERS · ALL TIME
          </div>
        </div>
        <div className="flex items-center h-3 gap-3">
          {(["sun", "spark", "target", "eye", "ban", "venus"] as GlyphName[]).map((g, i) => (
            <div key={g} className="flex items-center gap-2">
              <Glyph
                name={g}
                size={22}
              />
              {i < 5 && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
            </div>
          ))}
        </div>
      </div>

      <div className="relative mt-4 h-18 overflow-hidden rounded-md border border-white/5 bg-[oklch(0.14_0.05_270/0.55)] px-2">
        <div className="pointer-events-none absolute left-0 right-0 top-1/2 h-px -translate-y-1/2 bg-gradient-to-r from-transparent via-[var(--color-neon-cyan)]/40 to-transparent" />
        <div className="flex h-full items-center gap-[2px]">
          {heights.map((h, i) => (
            <div
              key={i}
              className="flex h-full flex-1 flex-col items-stretch justify-center gap-[1px]"
            >
              <div
                className="rounded-sm bg-[var(--color-neon-green)]/90"
                style={{
                  height: `${h * 0.65}%`,
                  boxShadow: h > 70 ? "0 0 6px var(--color-neon-cyan)" : undefined,
                }}
              />
              <div
                className="rounded-sm bg-[var(--color-neon-blue)]/70"
                style={{ height: `${h * 0.65}%` }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* The old label read "LIVE FREQUENCY · N Hz". N was the mean bar
          height of a decorative waveform. It was not a frequency and it was
          not measured in hertz. A fabricated unit on a command center is
          worse than no unit. */}
      <div className="mt-2 flex items-center justify-between text-[10px] tracking-[0.25em] text-muted-foreground">
        <span>
          {active} SIGNAL{active === 1 ? "" : "S"} IN FLIGHT · AMBIENT CARRIER
        </span>
        <span style={{ color: connected ? "var(--color-neon-cyan)" : "var(--color-neon-orange)" }}>
          {connected ? "LISTENING" : "NO SOURCE"}
        </span>
      </div>
    </div>
  );
}

/* ============================ GRID FEED ============================ */
export function GridFeed({
  items,
  reachable,
  newestAt,
}: {
  items: FeedItem[];
  reachable: boolean;
  newestAt: string | null;
}) {
  const fresh = freshnessOf(newestAt);

  // "REAL-TIME GRID FEED" over seventeen-day-old items is a claim the data
  // cannot support. The title states what the stream IS; the subtitle states
  // what it currently HOLDS.
  const subtitle = !reachable
    ? "GRID API UNREACHABLE"
    : items.length === 0
      ? "CONNECTED · NO ACTIVITY RECORDED"
      : fresh === "LIVE" || fresh === "RECENT"
        ? `LIVE · NEWEST ${timeAgo(newestAt).toUpperCase()}`
        : `STALE · NEWEST SIGNAL ${timeAgo(newestAt).toUpperCase()}`;

  const subtitleColor = !reachable
    ? "var(--color-neon-red)"
    : fresh === "STALE"
      ? "var(--color-neon-orange)"
      : "oklch(0.62 0.02 260)";

  return (
    <div className="panel flex min-h-[280px] flex-1 flex-col p-4">
      <div className="text-sm font-semibold tracking-[0.18em] neon-text-cyan">GRID SIGNAL FEED</div>
      <div className="text-[10px] tracking-[0.25em]" style={{ color: subtitleColor }}>
        {subtitle}
      </div>
      <div className="mt-3 min-h-0 flex-1 space-y-2.5 overflow-y-auto pr-1">
        {items.length === 0 && (
          <div className="py-6 text-center text-[11px] tracking-[0.2em] text-muted-foreground">
            {reachable ? "NO RECENT ACTIVITY" : "FEED OFFLINE"}
          </div>
        )}
        {items.map((f, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-md border border-white/5 bg-white/[0.02] px-3 py-2"
          >
            <div
              className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-md border"
              style={{
                borderColor: `color-mix(in oklab, var(--color-${f.color}) 50%, transparent)`,
                background: `color-mix(in oklab, var(--color-${f.color}) 14%, transparent)`,
              }}
            >
              <Glyph name={f.glyph} size={22} />
            </div>
            <div className="min-w-0 flex-1 leading-tight">
              <div className="text-sm break-words">
                <span className="font-semibold" style={{ color: `var(--color-${f.color})` }}>
                  {f.agent}
                </span>{" "}
                <span className="text-foreground/85">{f.text}</span>
              </div>
              <div className="text-[10px] tracking-[0.2em] text-muted-foreground">
                SEVERITY: <span style={{ color: `var(--color-${f.color})` }}>{f.sev}</span>
              </div>
            </div>
            <div className="text-[10px] tabular-nums text-muted-foreground">{timeAgo(f.at)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ============================ FOOTER ============================ */
export function FooterBar({ voiceSlot }: { voiceSlot?: ReactNode }) {
  return (
    <div className="panel flex shrink-0 flex-col gap-1.5 px-5 py-2.5">
      {voiceSlot && (
        <div className="flex items-center border-b border-white/5 pb-1.5">{voiceSlot}</div>
      )}
      <div className="flex items-center gap-4 overflow-hidden whitespace-nowrap">
        <p className="min-w-0 flex-1 truncate text-xs leading-tight text-foreground/85">
          <span className="font-semibold tracking-[0.2em] neon-text-gold">COVENANT OATH · </span>
          We observe what is real. We protect what matters. We evolve what is next.{" "}
          <span className="font-semibold tracking-[0.18em] neon-text-cyan">
            WE ARE THE MOSTAR GRID.
          </span>
        </p>
        <div className="flex shrink-0 items-center gap-6 text-[10px] tracking-[0.25em] text-muted-foreground">
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
      ? t
          .toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
          .toUpperCase()
      : "",
  };
}

export { KPI_META };
export type { FeedItem, Pulse, GridStatus };
