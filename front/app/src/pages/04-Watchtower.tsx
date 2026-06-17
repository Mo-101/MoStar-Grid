import { useEffect, useState } from "react";
import { useDashboard } from "@/routes/dashboard";
import { TopBar, FooterBar, chromeCss } from "@/components/grid/ChromeNav";

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "http://localhost:41010";

type HealthPayload = {
  status?: string;
  mindgraph?: boolean;
  dcx?: boolean;
  mcp?: { online?: boolean };
  cycles?: number;
  phase?: string;
};

type WatchtowerStats = {
  total: number;
  by_status?: Record<string, number>;
  sanctioned?: number;
  pending?: number;
  flagged?: number;
};

type TelemetryPayload = {
  status?: string;
  cycles?: number;
  proposals_pending?: number;
  proposals_approved?: number;
};

type LiveEvent = {
  actor: string;
  text: string;
  severity: "INFO" | "WARNING" | "ALERT" | "HIGH" | "CRITICAL";
  time: string;
};

function clock() {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

function statusColor(ok: boolean | undefined) {
  return ok ? "var(--green)" : ok === false ? "var(--ember)" : "var(--muted)";
}

function statusLabel(ok: boolean | undefined, onLabel = "CONNECTED", offLabel = "OFFLINE") {
  return ok ? onLabel : ok === false ? offLabel : "CHECKING";
}

function severityColor(sev: LiveEvent["severity"]) {
  if (sev === "CRITICAL" || sev === "ALERT") return "var(--ember)";
  if (sev === "HIGH" || sev === "WARNING") return "var(--gold)";
  return "var(--cyan)";
}

export default function Watchtower() {
  const { reports, census } = useDashboard();
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [stats, setStats] = useState<WatchtowerStats | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [voiceOk, setVoiceOk] = useState<boolean | undefined>(undefined);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);

  useEffect(() => {
    async function load() {
      const [h, s, t, v] = await Promise.allSettled([
        fetch(`${API_BASE}/api/health`).then((r) => (r.ok ? r.json() : Promise.reject())),
        fetch(`${API_BASE}/watchtower/stats`).then((r) => (r.ok ? r.json() : Promise.reject())),
        fetch(`${API_BASE}/api/telemetry`).then((r) => (r.ok ? r.json() : Promise.reject())),
        fetch(`${API_BASE}/api/voice/health`).then((r) => (r.ok ? r.json() : Promise.reject())),
      ]);
      if (h.status === "fulfilled") setHealth(h.value);
      if (s.status === "fulfilled") setStats(s.value);
      if (t.status === "fulfilled") setTelemetry(t.value);
      if (v.status === "fulfilled") setVoiceOk(v.value?.status === "healthy");
    }
    load();
    const poll = setInterval(load, 15000);
    return () => clearInterval(poll);
  }, []);

  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${API_BASE}/api/stream`);
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "event" && data.event) {
            const ev = data.event;
            setLiveEvents((prev) =>
              [
                {
                  actor: ev.source || ev.created_by || "GRID",
                  text: ev.text || ev.type || "grid signal",
                  severity: (["WARNING", "ALERT", "HIGH", "CRITICAL"].includes((ev.severity || "").toUpperCase())
                    ? (ev.severity || "INFO").toUpperCase()
                    : "INFO") as LiveEvent["severity"],
                  time: clock(),
                },
                ...prev,
              ].slice(0, 30),
            );
          }
        } catch { /* skip malformed */ }
      };
    } catch { /* SSE not available */ }
    return () => es?.close();
  }, []);

  const feedEvents: LiveEvent[] =
    liveEvents.length > 0
      ? liveEvents
      : reports.map((r) => ({
          actor: r.name?.toUpperCase() || "ENTITY",
          text: r.response || "Reported startup parameters. Status loaded into MindGraph.",
          severity: "INFO" as const,
          time: r.timestamp?.slice(11, 19) || "--:--:--",
        }));

  const neo4jOk = health?.mindgraph;
  const ollamaOk = health?.dcx;
  const mcpOk = health?.mcp?.online;
  const cycles = telemetry?.cycles ?? health?.cycles;

  return (
    <div className="watch-shell">
      <style>{chromeCss + watchCss}</style>

      <TopBar active="watchtower" />

      <section className="main">
        <aside className="left">
          <div className="panel box">
            <h3>PIPELINE VITALS</h3>
            <div className="row"><span>NEO4J</span><span style={{ color: statusColor(neo4jOk) }}>{statusLabel(neo4jOk, "CONNECTED", "OFFLINE")}</span></div>
            <div className="row"><span>OLLAMA / DCX</span><span style={{ color: statusColor(ollamaOk) }}>{statusLabel(ollamaOk, "RUNNING", "OFFLINE")}</span></div>
            <div className="row"><span>PIPER TTS</span><span style={{ color: statusColor(voiceOk) }}>{statusLabel(voiceOk, "ONLINE", "OFFLINE")}</span></div>
            <div className="row"><span>MCP GATE</span><span style={{ color: statusColor(mcpOk) }}>{statusLabel(mcpOk, "SECURE", "DEGRADED")}</span></div>
            {cycles !== undefined && (
              <div className="row"><span>GRID CYCLES</span><span style={{ color: "var(--cyan)" }}>{cycles.toLocaleString()}</span></div>
            )}
          </div>

          <div className="panel box">
            <h3>GRID CENSUS</h3>
            <div className="row"><span>NODES</span><span>{census?.nodes?.toLocaleString() ?? "—"}</span></div>
            <div className="row"><span>RELATIONSHIPS</span><span>{census?.relationships?.toLocaleString() ?? "—"}</span></div>
            <div className="row"><span>EVENTS</span><span>{census?.events?.toLocaleString() ?? "—"}</span></div>
            {census?.sealed_agents !== undefined && (
              <div className="row"><span>SEALED AGENTS</span><span style={{ color: "var(--gold)" }}>{census.sealed_agents}</span></div>
            )}
          </div>

          {stats && (
            <div className="panel box">
              <h3>WATCHTOWER AGENTS</h3>
              <div className="row"><span>TOTAL</span><span>{stats.total}</span></div>
              <div className="row"><span>SANCTIONED</span><span style={{ color: "var(--green)" }}>{stats.sanctioned ?? 0}</span></div>
              <div className="row"><span>PENDING</span><span style={{ color: "var(--gold)" }}>{stats.pending ?? 0}</span></div>
              {(stats.flagged ?? 0) > 0 && (
                <div className="row"><span>FLAGGED</span><span style={{ color: "var(--ember)" }}>{stats.flagged}</span></div>
              )}
            </div>
          )}
        </aside>

        <main className="panel feed">
          <div className="feed-head">
            <div>
              <div className="title">WATCHTOWER<small>SURVEILLANCE &amp; ANALYTICS</small></div>
            </div>
            {liveEvents.length > 0 && <span className="live-badge">LIVE · {liveEvents.length}</span>}
          </div>
          <div className="feed-list">
            {feedEvents.map((ev, i) => (
              <div className="feed-row" key={i} style={{ borderColor: `${severityColor(ev.severity)}33` }}>
                <div>
                  <span style={{ color: severityColor(ev.severity), fontWeight: 700 }}>[{ev.actor.toUpperCase()}]</span>{" "}
                  <span style={{ opacity: 0.85 }}>{ev.text}</span>
                </div>
                <div className="feed-meta">
                  <span className="time">{ev.time}</span>
                  {ev.severity !== "INFO" && <span style={{ color: severityColor(ev.severity) }}>{ev.severity}</span>}
                </div>
              </div>
            ))}
            {feedEvents.length === 0 && <div className="empty">Awaiting grid signals…</div>}
          </div>
        </main>
      </section>

      <FooterBar />
    </div>
  );
}

const watchCss = `
.watch-shell {
  --cyan: var(--color-neon-cyan, #00d8ff);
  --gold: var(--color-neon-gold, #f6c453);
  --green: var(--color-neon-green, #25ff8a);
  --ember: var(--color-neon-red, #ff5a2e);
  --muted: #8190a3;
  position: relative;
  height: 100vh;
  overflow: hidden;
  padding: 14px;
  box-sizing: border-box;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 10px;
  color: #dbe8f6;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background: radial-gradient(circle at 50% 20%, #102233 0, #040910 40%, #000 100%);
}
.watch-shell .main { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 10px; min-height: 0; }
.watch-shell .panel { position: relative; background: linear-gradient(180deg, rgba(4,14,28,.80), rgba(2,8,16,.92)); border: 1px solid rgba(0,216,255,.24); box-shadow: 0 0 32px rgba(0,216,255,.05), inset 0 0 34px rgba(0,216,255,.022); border-radius: 6px; overflow: hidden; }
.watch-shell .panel:before, .watch-shell .panel:after { content: ""; position: absolute; width: 22px; height: 22px; border-color: var(--cyan); opacity: .42; }
.watch-shell .panel:before { left: 7px; top: 7px; border-top: 1px solid; border-left: 1px solid; }
.watch-shell .panel:after { right: 7px; bottom: 7px; border-right: 1px solid; border-bottom: 1px solid; }
.watch-shell .left { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; min-height: 0; }
.watch-shell .box { padding: 16px 18px; }
.watch-shell .box h3 { margin: 0 0 12px; color: var(--cyan); font-size: 12px; letter-spacing: .2em; font-weight: 500; }
.watch-shell .row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,.07); padding: 7px 0; font-size: 12px; color: #c2ccda; }
.watch-shell .feed { display: flex; flex-direction: column; padding: 18px 22px; min-height: 0; }
.watch-shell .feed-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.watch-shell .title { color: var(--gold); letter-spacing: .25em; font-size: 18px; }
.watch-shell .title small { display: block; color: var(--cyan); font-size: 10px; letter-spacing: .22em; margin-top: 6px; }
.watch-shell .live-badge { font-size: 9px; letter-spacing: .22em; padding: 3px 9px; border-radius: 4px; color: var(--green); border: 1px solid var(--green); background: rgba(37,255,138,.08); }
.watch-shell .feed-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; min-height: 0; }
.watch-shell .feed-row { display: flex; justify-content: space-between; gap: 16px; padding: 11px 14px; border: 1px solid rgba(255,255,255,.08); border-radius: 4px; background: rgba(2,10,18,.6); font-size: 12px; }
.watch-shell .feed-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 3px; flex-shrink: 0; font-size: 10px; }
.watch-shell .feed-meta .time { color: var(--muted); }
.watch-shell .empty { padding: 24px; text-align: center; color: var(--muted); border: 1px solid rgba(255,255,255,.06); border-radius: 4px; }
@media (max-width: 1200px) {
  .watch-shell { height: auto; min-height: 100vh; overflow: auto; }
  .watch-shell .main { grid-template-columns: 1fr; }
}
`;
