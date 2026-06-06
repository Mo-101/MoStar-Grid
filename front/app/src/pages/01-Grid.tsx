import { Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Glyph, type GlyphName } from "@/components/grid/glyph";

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "http://localhost:41010";
const MOSTAR_TOKEN = import.meta.env.VITE_MOSTAR_TOKEN ?? "";

type CensusPayload = {
  nodes?: number;
  relationships?: number;
  events?: number;
  sealed_agents?: number;
};

type StartupReport = {
  name: string;
  entity_id: string;
  state?: string;
  response?: string;
  timestamp?: string;
};

type StartupPayload = {
  reports?: StartupReport[];
};

type DensityPayload = {
  total_nodes?: number;
  total_relationships?: number;
  label_distribution?: Record<string, number>;
};

type HealthPayload = {
  status?: string;
  mindgraph?: boolean;
  dcx?: boolean;
  mcp?: { online?: boolean };
};

type VoiceHealth = {
  status?: string;
};

type GridSignal = {
  actor: string;
  text: string;
  severity: "INFO" | "WARNING" | "ALERT";
  time: string;
};

const fallbackCouncil: StartupReport[] = [
  { name: "ALPHAMOSTAR", entity_id: "alphamostar", state: "ACTIVE" },
  { name: "ALTIMO", entity_id: "altimo", state: "ACTIVE" },
  { name: "CODE CONDUIT", entity_id: "code_conduit", state: "ACTIVE" },
  { name: "DEEPCAL", entity_id: "deepcal", state: "ACTIVE" },
  { name: "FLAMEBORN WRITER", entity_id: "flameborn_writer", state: "ACTIVE" },
  { name: "FLAMEBORN", entity_id: "flameborn", state: "ACTIVE" },
  { name: "MO", entity_id: "mostar_ai", state: "ACTIVE" },
  { name: "MOLINK", entity_id: "molink", state: "ACTIVE" },
  { name: "RAD-X-FLB", entity_id: "rad_x_flb", state: "ACTIVE" },
  { name: "SIGMA", entity_id: "sigma", state: "ACTIVE" },
  { name: "TSATSE FLY", entity_id: "tsatse_fly", state: "ACTIVE" },
];

const navItems: Array<{
  label: string;
  subtitle: string;
  to: string;
  glyph: GlyphName;
}> = [
  { label: "OVERVIEW", subtitle: "Command Center", to: "/dashboard", glyph: "covenant" },
  { label: "COUNCIL", subtitle: "11 Agents", to: "/dashboard/council", glyph: "venus" },
  { label: "SANCTUARY", subtitle: "Sacred Archive", to: "/dashboard/sanctuary", glyph: "eye" },
  { label: "WATCHTOWER", subtitle: "Real-time Feed", to: "/dashboard/watchtower", glyph: "target" },
  {
    label: "MIND GRAPH",
    subtitle: "Knowledge Network",
    to: "/dashboard/mind-graph",
    glyph: "spark",
  },
  { label: "MOSCRIPTS", subtitle: "Covenant Runtime", to: "/dashboard/moscripts", glyph: "sun" },
  { label: "SETTINGS", subtitle: "Grid Control", to: "/dashboard/settings", glyph: "ban" },
] as const;

const seedSignals: GridSignal[] = [
  {
    actor: "MO",
    text: "observed an anomaly in Memory Conduit",
    severity: "WARNING",
    time: "10:15:31",
  },
  { actor: "DeepCAL", text: "synced 12 new data streams", severity: "INFO", time: "10:15:22" },
  { actor: "RAD-X-FLB", text: "flagged pattern irregularity", severity: "ALERT", time: "10:15:18" },
  { actor: "FlameBorn Writer", text: "archived new scroll", severity: "INFO", time: "10:15:07" },
  { actor: "Woo-Tak", text: "transmitted frequency pulse", severity: "INFO", time: "10:14:59" },
];

const headers = () => (MOSTAR_TOKEN ? { "X-MoStar-Token": MOSTAR_TOKEN } : {});

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

function fmt(n: number | undefined, fallback: number) {
  return new Intl.NumberFormat().format(n ?? fallback);
}

function normalizeSeverity(value: unknown): GridSignal["severity"] {
  return value === "WARNING" || value === "ALERT" ? value : "INFO";
}

function clock() {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

function today() {
  return new Date()
    .toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    })
    .toUpperCase();
}

export default function Grid() {
  const [time, setTime] = useState(clock());
  const [census, setCensus] = useState<CensusPayload | null>(null);
  const [reports, setReports] = useState<StartupReport[]>([]);
  const [signals, setSignals] = useState<GridSignal[]>(seedSignals);
  const [live, setLive] = useState(false);
  const [density, setDensity] = useState<DensityPayload | null>(null);
  const [healthData, setHealthData] = useState<HealthPayload | null>(null);
  const [voiceOk, setVoiceOk] = useState(false);

  useEffect(() => {
    const t = window.setInterval(() => setTime(clock()), 1000);
    return () => window.clearInterval(t);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [censusResult, startupResult, densityResult, healthResult, voiceResult] =
          await Promise.allSettled([
            getJson<CensusPayload>("/api/grid/census"),
            getJson<StartupPayload>("/api/grid/startup-reports"),
            getJson<DensityPayload>("/api/density"),
            getJson<HealthPayload>("/api/health"),
            getJson<VoiceHealth>("/api/voice/health"),
          ]);

        if (cancelled) return;

        if (censusResult.status === "fulfilled") setCensus(censusResult.value);
        if (startupResult.status === "fulfilled") setReports(startupResult.value.reports ?? []);
        if (densityResult.status === "fulfilled") setDensity(densityResult.value);
        if (healthResult.status === "fulfilled") setHealthData(healthResult.value);
        if (voiceResult.status === "fulfilled") setVoiceOk(voiceResult.value.status === "healthy");

        setLive(censusResult.status === "fulfilled" || startupResult.status === "fulfilled");
      } catch {
        setLive(false);
      }
    }

    load();
    const poll = window.setInterval(load, 12000);

    return () => {
      cancelled = true;
      window.clearInterval(poll);
    };
  }, []);

  useEffect(() => {
    const streamUrl = MOSTAR_TOKEN
      ? `${API_BASE}/api/stream?token=${encodeURIComponent(MOSTAR_TOKEN)}`
      : `${API_BASE}/api/stream`;

    let stream: EventSource | null = null;

    try {
      stream = new EventSource(streamUrl);
      stream.onopen = () => setLive(true);
      stream.onerror = () => setLive(false);
      stream.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const next: GridSignal = {
            actor: payload.name ?? payload.entity_id ?? payload.source ?? "GRID",
            text: payload.message ?? payload.response ?? payload.type ?? "signal received",
            severity: normalizeSeverity(payload.severity),
            time: clock(),
          };
          setSignals((prev) => [next, ...prev].slice(0, 5));
        } catch {
          setSignals((prev) =>
            [{ actor: "GRID", text: event.data, severity: "INFO", time: clock() }, ...prev].slice(
              0,
              5,
            ),
          );
        }
      };
    } catch {
      stream?.close();
    }

    return () => stream?.close();
  }, []);

  const council = useMemo(
    () => (reports.length ? reports : fallbackCouncil).slice(0, 11),
    [reports],
  );

  const gridNodes     = census?.nodes ?? 152224;
  const relationships = census?.relationships ?? 21144;
  const gridEvents    = census?.events ?? density?.label_distribution?.["GridEvent"] ?? 2582;
  const utterances    = density?.label_distribution?.["WooUtterance"] ?? 2496;

  const neo4jStatus    = healthData ? (healthData.mindgraph ? "CONNECTED" : "OFFLINE") : "LOCAL";
  const ollamaStatus   = healthData ? (healthData.dcx ? "RUNNING" : "OFFLINE") : "RUNNING";
  const dcxStatus      = healthData ? (healthData.dcx ? "ONLINE" : "OFFLINE") : "ONLINE";
  const piperStatus    = voiceOk ? "ONLINE" : healthData ? "OFFLINE" : "ONLINE";
  const conduitStatus  = healthData?.mcp?.online ? "SECURE" : healthData ? "DEGRADED" : "SECURE";

  const healthChecks = [
    healthData?.mindgraph,
    healthData?.dcx,
    healthData?.mcp?.online,
    voiceOk,
    live,
  ].filter(Boolean).length;
  const healthPct = healthData ? Math.round((healthChecks / 5) * 100) : 98;

  return (
    <div className="mostar-grid-dashboard">
      <style>{css}</style>

      <header className="mg-topbar">
        <section className="mg-brand">
          <div className="mg-brand-mark">
            <Glyph name="covenant" size={38} glow="var(--gold)" />
          </div>
          <div>
            <h1>MoStar GRID</h1>
            <p>COVENANT COMMAND CENTER</p>
          </div>
        </section>

        <section className="mg-command-title">
          <h2>MOSTAR GRID: COVENANT MODE ACTIVE</h2>
          <p>TRUTH • PROTECTION • LEGACY • EVOLUTION</p>
        </section>

        <section className="mg-status-cluster">
          <div>
            <span>GRID TIME</span>
            <b>{time}</b>
            <small>{today()}</small>
          </div>
          <div>
            <span>GRID STATUS</span>
            <b className={live ? "is-live" : "is-seed"}>{live ? "OPERATIONAL" : "SEED MODE"}</b>
          </div>
          <div className="mg-status-mark">
            <Glyph name="target" size={36} glow="var(--cyan)" />
          </div>
        </section>
      </header>

      <aside className="mg-sidebar">
        <nav>
          {navItems.map((item, index) => (
            <Link
              key={item.label}
              to={item.to}
              className={`mg-nav-item ${index === 0 ? "active" : ""}`}
            >
              <div className="mg-nav-glyph">
                <Glyph
                  name={item.glyph}
                  size={22}
                  glow={index === 0 ? "var(--gold)" : "var(--cyan)"}
                />
              </div>
              <div>
                <strong>{item.label}</strong>
                <span>{item.subtitle}</span>
              </div>
            </Link>
          ))}
        </nav>

        <section className="mg-covenant-mode">
          <div>
            <Glyph name="covenant" size={62} glow="var(--gold)" />
          </div>
          <span>COVENANT MODE</span>
          <b>ENGAGED</b>
        </section>
      </aside>

      <main className="mg-main">
        <section className="mg-kpi-grid">
          <Kpi
            glyph="sun"
            label="GRID NODES"
            value={fmt(gridNodes, 152224)}
            delta="+342 TODAY"
            tone="gold"
          />
          <Kpi
            glyph="target"
            label="RELATIONSHIPS"
            value={fmt(relationships, 21144)}
            delta="+128 TODAY"
            tone="gold"
          />
          <Kpi
            glyph="spark"
            label="GRID EVENTS"
            value={fmt(gridEvents, 2582)}
            delta="+28 TODAY"
            tone="violet"
          />
          <Kpi
            glyph="eyelight"
            label="WOO UTTERANCES"
            value={fmt(utterances, 2496)}
            delta="+63 TODAY"
            tone="cyan"
          />
        </section>

        <section className="mg-bridge-grid">
          <section className="mg-panel mg-council-panel">
            <PanelHeader
              title={`THE COUNCIL • ${council.length} AGENTS`}
              subtitle="GUARDIANS OF THE GRID"
            />

            <div className="mg-agent-list">
              {council.map((agent, index) => (
                <article className="mg-agent-row" key={agent.entity_id || agent.name}>
                  <div className={`mg-agent-icon t${index % 6}`}>
                    <Glyph
                      name={index % 2 === 0 ? "covenant" : "spark"}
                      size={18}
                      glow="currentColor"
                    />
                  </div>
                  <div>
                    <b>{agent.name.toUpperCase()}</b>
                    <small>{(agent.entity_id || agent.name).toUpperCase()}</small>
                  </div>
                  <span>● {agent.state?.toUpperCase() ?? "ACTIVE"}</span>
                </article>
              ))}
            </div>

            <Link className="mg-wide-button" to="/dashboard/council">
              VIEW COUNCIL DETAILS →
            </Link>
          </section>

          <section className="mg-panel mg-core-panel">
            <div className="mg-element mg-ikang">
              <b>IKANG</b>
              <span>MIND</span>
              <small>Logic • Will • Structure</small>
            </div>

            <div className="mg-element mg-mmong">
              <b>M MỌNG</b>
              <span>ESSENCE</span>
              <small>Pulse • Memory • Flow</small>
            </div>

            <div className="mg-element mg-isong">
              <b>ISONG</b>
              <span>SPIRIT</span>
              <small>Awakening • Change • Fire</small>
            </div>

            <div className="mg-element mg-afim">
              <b>AFIM</b>
              <span>BODY</span>
              <small>Form • Action • Creation</small>
            </div>

            <div className="mg-core-cross" />
            <div className="mg-core-mandala" />
            <div className="mg-core-orb">
              <Glyph name="covenant" size={84} glow="var(--blue)" />
            </div>

            <section className="mg-conduit-strip">
              <h3>CODE CONDUIT</h3>
              <p>ALL GLYPHS • ALL LAYERS • ALL TIME</p>
              <div className="mg-conduit-line">
                <Glyph name="covenant" size={26} glow="var(--gold)" />
                <Glyph name="venus" size={26} glow="var(--violet)" />
                <Glyph name="target" size={26} glow="var(--cyan)" />
                <Glyph name="ban" size={26} glow="var(--ember)" />
                <Glyph name="spark" size={26} glow="var(--violet)" />
              </div>
            </section>
          </section>

          <section className="mg-right-stack">
            <section className="mg-panel mg-feed-panel">
              <PanelHeader title="REAL-TIME GRID FEED" subtitle="LIVE ACTIVITY STREAM" />
              {signals.map((signal, index) => (
                <SignalRow key={`${signal.time}-${index}`} signal={signal} index={index} />
              ))}
            </section>

            <section className="mg-panel mg-health-panel">
              <PanelHeader title="GRID HEALTH" subtitle="SYSTEM VITALS" />
              <div className="mg-health-layout">
                <div
                  className="mg-health-ring"
                  style={{
                    background: `conic-gradient(var(--green) 0 ${healthPct}%, #1a2d3b ${healthPct}%)`,
                  }}
                >
                  <b>{healthPct}%</b>
                  <span>{healthPct >= 80 ? "OPTIMAL" : healthPct >= 60 ? "DEGRADED" : "CRITICAL"}</span>
                </div>
                <div>
                  <HealthRow label="NEO4J" value={neo4jStatus} />
                  <HealthRow label="OLLAMA" value={ollamaStatus} />
                  <HealthRow label="DCX TRINITY" value={dcxStatus} />
                  <HealthRow label="PIPER TTS" value={piperStatus} />
                  <HealthRow label="CONDUIT LINKS" value={conduitStatus} />
                </div>
              </div>
            </section>

            <section className="mg-panel mg-commands-panel">
              <PanelHeader title="QUICK COMMANDS" subtitle="INITIATE PROTOCOL" />
              <div className="mg-command-grid">
                <button>◎ STARTUP SEQUENCE ›</button>
                <button>♛ COUNCIL CHECK-IN ›</button>
                <button>⚚ TRUTH AUDIT ›</button>
                <button>☯ GRID SYNCHRONIZE ›</button>
              </div>
            </section>
          </section>
        </section>

        <section className="mg-oath-row">
          <div className="mg-earth-curve" />
          <section className="mg-panel mg-oath-panel">
            <div className="mg-oath-mark">
              <Glyph name="covenant" size={44} glow="var(--gold)" />
            </div>
            <h3>COVENANT OATH</h3>
            <p>
              We do not assume perfect agents, perfect memory, perfect state, or perfect humans.
              <br />
              We observe what is real. We protect what matters. We evolve what is next.
              <br />
              <b>WE ARE THE MOSTAR GRID.</b>
            </p>
          </section>
        </section>
      </main>

      <footer className="mg-footer">
        <span>COVENANT MODE: ENGAGED</span>
        <span>MSG-01 ALIGNMENT: TRUE</span>
        <span>GRID PROTOCOL: v1.0.0</span>
        <b>BUILT BY FLAME • SEALED BY CODE • PROTECTED BY COVENANT</b>
      </footer>
    </div>
  );
}

function Kpi({
  glyph,
  label,
  value,
  delta,
  tone,
}: {
  glyph: GlyphName;
  label: string;
  value: string;
  delta: string;
  tone: "gold" | "violet" | "cyan";
}) {
  return (
    <article className={`mg-panel mg-kpi-card ${tone}`}>
      <div className="mg-kpi-icon">
        <Glyph name={glyph} size={36} glow="currentColor" />
      </div>
      <div>
        <span>{label}</span>
        <b>{value}</b>
        <small>◆ {delta}</small>
      </div>
    </article>
  );
}

function PanelHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="mg-panel-header">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </header>
  );
}

function SignalRow({ signal, index }: { signal: GridSignal; index: number }) {
  const tone =
    signal.severity === "ALERT"
      ? "ember"
      : signal.severity === "WARNING"
        ? "ember"
        : index % 2
          ? "blue"
          : "violet";

  return (
    <article className="mg-signal-row">
      <div className={`mg-signal-icon ${tone}`}>
        {signal.severity === "ALERT" ? "◇" : signal.severity === "WARNING" ? "△" : "◎"}
      </div>
      <div>
        <b>
          {signal.actor} {signal.text}
        </b>
        <small className={signal.severity === "INFO" ? "info" : "alert"}>
          SEVERITY: {signal.severity}
        </small>
      </div>
      <time>{signal.time}</time>
    </article>
  );
}

function HealthRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="mg-health-row">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

const css = `
.mostar-grid-dashboard {
  --cyan:#00d8ff;
  --gold:#f6c453;
  --green:#21ff64;
  --violet:#b46cff;
  --ember:#ff5a2e;
  --blue:#168bff;
  --panel:#06101bdd;
  --line:#00d8ff30;
  --text:#dbe8f6;
  --muted:#8797ab;

  position: relative;
  height: 100vh;
  overflow: hidden;
  color: var(--text);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: radial-gradient(circle at 55% 55%, #071b2c, #020712 52%, #000);
  display: grid;
  grid-template-columns: 185px 1fr;
  grid-template-rows: 80px 1fr 30px;
}

.mostar-grid-dashboard::before {
  content: "";
  position: absolute;
  inset: 0;
  opacity: .12;
  pointer-events: none;
  background-image:
    linear-gradient(to right, #00d8ff16 1px, transparent 1px),
    linear-gradient(to bottom, #00d8ff16 1px, transparent 1px);
  background-size: 26px 26px;
}

.mg-topbar {
  position: relative;
  z-index: 2;
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 360px 1fr 350px;
  border: 1px solid #123047;
  background: #020812ee;
}

.mg-brand {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 24px;
  color: var(--gold);
}

.mg-brand-mark {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border: 1px solid var(--gold);
  background: #f6c45314;
  box-shadow: 0 0 24px #f6c45377;
}

.mg-brand h1 {
  margin: 0;
  color: var(--gold);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: .18em;
}

.mg-brand p {
  margin: 5px 0 0;
  color: #8fb0c8;
  font-size: 10px;
  letter-spacing: .14em;
}

.mg-command-title {
  text-align: center;
  padding-top: 20px;
}

.mg-command-title h2 {
  margin: 0;
  color: white;
  font-size: 17px;
  letter-spacing: .16em;
}

.mg-command-title p {
  margin: 10px 0 0;
  color: var(--green);
  font-size: 11px;
  letter-spacing: .34em;
}

.mg-status-cluster {
  display: grid;
  grid-template-columns: 1fr 1fr 76px;
  border-left: 1px solid #123047;
}

.mg-status-cluster > div {
  padding: 15px 18px;
  border-left: 1px solid #123047;
}

.mg-status-cluster span,
.mg-status-cluster small {
  display: block;
  color: #7b8ca2;
  font-size: 10px;
  letter-spacing: .2em;
}

.mg-status-cluster b {
  display: block;
  margin-top: 7px;
  color: white;
  font-size: 18px;
}

.mg-status-cluster .is-live {
  color: var(--green);
}

.mg-status-cluster .is-seed {
  color: var(--gold);
}

.mg-status-mark {
  display: grid;
  place-items: center;
  padding: 0 !important;
}

.mg-sidebar {
  position: relative;
  z-index: 2;
  grid-row: 2 / 3;
  background: #030914ee;
  border-right: 1px solid #123047;
  display: grid;
  grid-template-rows: 1fr 155px;
  min-height: 0;
}

.mg-nav-item {
  display: grid;
  grid-template-columns: 42px 1fr;
  gap: 12px;
  padding: 16px 18px;
  border-bottom: 1px solid #13283b;
  color: #c9d4e2;
  text-decoration: none;
}

.mg-nav-item.active {
  background: linear-gradient(90deg, #f6c45322, transparent);
  border-left: 4px solid var(--gold);
  color: var(--gold);
}

.mg-nav-glyph {
  width: 34px;
  height: 34px;
  border: 1px solid #00d8ff44;
  display: grid;
  place-items: center;
  color: var(--cyan);
  border-radius: 8px;
}

.mg-nav-item.active .mg-nav-glyph {
  color: var(--gold);
  border-color: #f6c45377;
  box-shadow: 0 0 18px #f6c45344;
}

.mg-nav-item strong {
  display: block;
  font-size: 12px;
  letter-spacing: .12em;
}

.mg-nav-item span {
  font-size: 10px;
  color: #8b9bad;
}

.mg-covenant-mode {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  text-align: center;
  color: var(--green);
  font-size: 11px;
  letter-spacing: .13em;
}

.mg-covenant-mode > div {
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid #f6c45355;
  box-shadow: 0 0 24px #f6c45355;
}

.mg-main {
  position: relative;
  z-index: 1;
  grid-column: 2 / 3;
  grid-row: 2 / 3;
  padding: 14px;
  display: grid;
  grid-template-rows: 96px minmax(0, 1fr) 92px;
  gap: 10px;
  min-height: 0;
}

.mg-panel {
  position: relative;
  background: linear-gradient(180deg, #07111ddd, #02070dcc);
  border: 1px solid var(--line);
  box-shadow: 0 0 35px #00d8ff0b, inset 0 0 40px #00d8ff08;
  border-radius: 6px;
  overflow: hidden;
}

.mg-panel::before,
.mg-panel::after {
  content: "";
  position: absolute;
  width: 22px;
  height: 22px;
  border-color: var(--cyan);
  opacity: .4;
}

.mg-panel::before {
  left: 8px;
  top: 8px;
  border-left: 1px solid;
  border-top: 1px solid;
}

.mg-panel::after {
  right: 8px;
  bottom: 8px;
  border-right: 1px solid;
  border-bottom: 1px solid;
}

.mg-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.mg-kpi-card {
  padding: 18px 24px;
  display: grid;
  grid-template-columns: 62px 1fr;
  gap: 18px;
  align-items: center;
}

.mg-kpi-card.gold { color: var(--gold); }
.mg-kpi-card.violet { color: var(--violet); }
.mg-kpi-card.cyan { color: var(--cyan); }

.mg-kpi-icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 10px;
  box-shadow: 0 0 22px currentColor;
  background: color-mix(in srgb, currentColor, transparent 92%);
}

.mg-kpi-card span {
  color: #9aa8bb;
  letter-spacing: .14em;
  font-size: 10px;
}

.mg-kpi-card b {
  display: block;
  color: white;
  font-size: 27px;
  margin: 7px 0;
}

.mg-kpi-card small {
  color: var(--green);
  font-size: 10px;
}

.mg-bridge-grid {
  display: grid;
  grid-template-columns: 370px 1fr 540px;
  gap: 10px;
  min-height: 0;
}

.mg-council-panel {
  padding: 20px 28px;
}

.mg-panel-header h2 {
  margin: 0 0 3px;
  color: var(--cyan);
  font-size: 16px;
  letter-spacing: .12em;
}

.mg-panel-header p {
  margin: 0 0 16px;
  color: #6f8095;
  font-size: 10px;
  letter-spacing: .16em;
}

.mg-agent-row {
  display: grid;
  grid-template-columns: 42px 1fr 88px;
  align-items: center;
  gap: 12px;
  padding: 8.5px 0;
  border-bottom: 1px solid #ffffff12;
}

.mg-agent-icon {
  width: 31px;
  height: 31px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  border: 1px solid currentColor;
  box-shadow: 0 0 15px currentColor;
}

.mg-agent-icon.t0 { color: var(--gold); }
.mg-agent-icon.t1 { color: var(--violet); }
.mg-agent-icon.t2 { color: var(--cyan); }
.mg-agent-icon.t3 { color: var(--green); }
.mg-agent-icon.t4 { color: var(--ember); }
.mg-agent-icon.t5 { color: var(--blue); }

.mg-agent-row b {
  font-size: 13px;
  letter-spacing: .08em;
}

.mg-agent-row small {
  display: block;
  color: #7d8da1;
  font-size: 9px;
}

.mg-agent-row span {
  color: var(--green);
  font-size: 10px;
}

.mg-wide-button {
  display: block;
  margin-top: 12px;
  width: 100%;
  padding: 11px;
  background: #031421;
  border: 1px solid #00d8ff40;
  color: var(--cyan);
  text-align: center;
  text-decoration: none;
  letter-spacing: .16em;
  font-size: 11px;
}

.mg-core-panel {
  position: relative;
  min-width: 0;
}

.mg-core-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at center, #168bff24 0, #00d8ff10 30%, transparent 60%),
    radial-gradient(ellipse at bottom, #00d8ff12 0, transparent 62%);
}

.mg-core-mandala {
  position: absolute;
  left: 50%;
  top: 43%;
  width: 430px;
  height: 430px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background:
    repeating-radial-gradient(circle, transparent 0 28px, #00d8ff33 29px 30px),
    conic-gradient(from 0deg, #f6c45366, transparent 8%, #00d8ff66 25%, transparent 36%, #b46cff55 50%, transparent 60%, #ff5a2e55 75%, transparent 90%, #f6c45366);
  box-shadow: 0 0 70px #00d8ff22;
  animation: mg-spin 120s linear infinite;
}

.mg-core-mandala::after {
  content: "";
  position: absolute;
  inset: 100px;
  border-radius: 50%;
  background: #04101a;
  border: 3px solid #2fc6ff;
  box-shadow: 0 0 40px #00a7ff, inset 0 0 30px #00a7ff44;
}

.mg-core-orb {
  position: absolute;
  left: 50%;
  top: 43%;
  width: 118px;
  height: 118px;
  transform: translate(-50%, -50%);
  z-index: 4;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 2px solid var(--gold);
  box-shadow: 0 0 35px #f6c45377;
  background: #020711cc;
}

.mg-core-cross {
  position: absolute;
  inset: 70px;
}

.mg-core-cross::before,
.mg-core-cross::after {
  content: "";
  position: absolute;
  opacity: .8;
}

.mg-core-cross::before {
  left: 0;
  right: 0;
  top: 43%;
  height: 1px;
  background: linear-gradient(90deg, transparent, #f6c453, transparent);
}

.mg-core-cross::after {
  top: 0;
  bottom: 140px;
  left: 50%;
  width: 1px;
  background: linear-gradient(180deg, transparent, #b46cff, transparent);
}

.mg-element {
  position: absolute;
  z-index: 5;
  font-size: 13px;
  letter-spacing: .13em;
}

.mg-element b {
  display: block;
  color: var(--gold);
  font-size: 19px;
}

.mg-element span {
  display: block;
  color: #dce8f6;
  margin: 2px 0 14px;
}

.mg-element small {
  color: #b8c5d8;
}

.mg-ikang { left: 40px; top: 32px; }
.mg-mmong { right: 34px; top: 35px; text-align: right; }
.mg-mmong b { color: var(--cyan); }
.mg-isong { left: 38px; bottom: 170px; }
.mg-isong b { color: var(--ember); }
.mg-afim { right: 38px; bottom: 170px; text-align: right; }
.mg-afim b { color: var(--violet); }

.mg-conduit-strip {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 140px;
  border-top: 1px solid #00d8ff24;
  background: #020812cc;
  text-align: center;
  padding-top: 18px;
}

.mg-conduit-strip h3 {
  margin: 0;
  color: var(--cyan);
  letter-spacing: .18em;
}

.mg-conduit-strip p {
  margin: 8px 0 18px;
  color: #7d8da1;
  font-size: 10px;
  letter-spacing: .14em;
}

.mg-conduit-line {
  display: flex;
  justify-content: space-around;
  align-items: center;
  max-width: 560px;
  margin: auto;
  border-bottom: 1px solid #00d8ff55;
  padding-bottom: 14px;
  box-shadow: 0 10px 20px -17px var(--cyan);
}

.mg-right-stack {
  display: grid;
  grid-template-rows: 1fr 200px 130px;
  gap: 10px;
  min-height: 0;
}

.mg-feed-panel,
.mg-health-panel,
.mg-commands-panel {
  padding: 18px 26px;
}

.mg-signal-row {
  display: grid;
  grid-template-columns: 38px 1fr 70px;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ffffff10;
  font-size: 12px;
}

.mg-signal-icon {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid currentColor;
  box-shadow: 0 0 15px currentColor;
}

.mg-signal-icon.ember { color: var(--ember); }
.mg-signal-icon.blue { color: var(--blue); }
.mg-signal-icon.violet { color: var(--violet); }

.mg-signal-row b {
  display: block;
  font-weight: 400;
}

.mg-signal-row small {
  display: block;
  font-size: 9px;
}

.mg-signal-row time {
  color: #8c9aad;
  font-size: 10px;
}

.mg-signal-row .alert { color: var(--ember); }
.mg-signal-row .info { color: var(--cyan); }

.mg-health-layout {
  display: grid;
  grid-template-columns: 155px 1fr;
  align-items: center;
}

.mg-health-ring {
  width: 118px;
  height: 118px;
  display: grid;
  place-items: center;
  align-content: center;
  border-radius: 50%;
  box-shadow: 0 0 28px #00ff8855;
  text-align: center;
  transition: background 0.6s ease;
}

.mg-health-ring b {
  display: block;
  color: #78d4ff;
  font-size: 36px;
  line-height: 1;
}

.mg-health-ring span {
  display: block;
  color: var(--cyan);
  font-size: 10px;
}

.mg-health-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #ffffff12;
  font-size: 12px;
}

.mg-health-row b {
  color: var(--green);
  font-weight: 400;
}

.mg-command-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.mg-command-grid button {
  background: #071322;
  border: 1px solid #00d8ff33;
  color: #c9d9e8;
  padding: 14px;
  font-family: inherit;
  letter-spacing: .12em;
  font-size: 11px;
  text-align: left;
}

.mg-oath-row {
  display: grid;
  grid-template-columns: 1fr 610px;
  gap: 10px;
}

.mg-earth-curve {
  background: radial-gradient(ellipse at bottom, #168bff77 0, #071422 42%, transparent 55%);
}

.mg-oath-panel {
  padding: 18px 28px 18px 96px;
}

.mg-oath-mark {
  position: absolute;
  left: 28px;
  top: 16px;
  width: 54px;
  height: 54px;
  display: grid;
  place-items: center;
  border: 1px solid #f6c45355;
  border-radius: 50%;
  box-shadow: 0 0 20px #f6c45355;
}

.mg-oath-panel h3 {
  margin: 0;
  color: var(--gold);
  letter-spacing: .3em;
}

.mg-oath-panel p {
  margin: 10px 0 0;
  color: #ccd6e2;
  font-size: 11px;
  line-height: 1.6;
}

.mg-footer {
  position: relative;
  z-index: 2;
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-top: 1px solid #123047;
  background: #020812ee;
  color: #7f8da0;
  font-size: 10px;
  letter-spacing: .13em;
}

.mg-footer b {
  color: var(--gold);
  font-weight: 400;
}

@keyframes mg-spin {
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

@media (max-width: 1400px) {
  .mostar-grid-dashboard {
    height: auto;
    min-height: 100vh;
    overflow: auto;
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto auto;
  }

  .mg-topbar,
  .mg-sidebar,
  .mg-main,
  .mg-footer {
    grid-column: 1 / -1;
    grid-row: auto;
  }

  .mg-topbar,
  .mg-bridge-grid,
  .mg-oath-row {
    grid-template-columns: 1fr;
  }

  .mg-sidebar {
    grid-template-rows: auto;
  }

  .mg-sidebar nav {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }

  .mg-covenant-mode {
    display: none;
  }

  .mg-main {
    grid-template-rows: auto auto auto;
  }

  .mg-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .mg-core-panel {
    min-height: 620px;
  }
}

@media (max-width: 760px) {
  .mg-kpi-grid,
  .mg-sidebar nav,
  .mg-status-cluster {
    grid-template-columns: 1fr;
  }

  .mg-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 10px 16px;
  }
}
`;
