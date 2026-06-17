import { useEffect, useState } from "react";
import { useDashboard } from "@/routes/dashboard";
import { TopBar, FooterBar, chromeCss } from "@/components/grid/ChromeNav";

type SoulPayload = {
  name?: string;
  architect?: string;
  cluster_id?: string;
  motto?: string;
  seal?: string;
  soul_language?: string;
  origin?: string;
};

type ProvenancePayload = {
  total?: number;
  scope?: string;
  recent?: Array<{ type: string; timestamp?: string; data?: Record<string, unknown> }>;
};

type BriefingPayload = {
  ok?: boolean;
  message?: string;
  text?: string;
  signals?: string;
  facts?: { current_nodes?: number; current_relationships?: number; current_events?: number };
  weather?: { live?: boolean; provider?: string };
  flights?: { live?: boolean };
};

export default function Settings() {
  const { apiBase } = useDashboard();
  const [soul, setSoul] = useState<SoulPayload | null>(null);
  const [provenance, setProvenance] = useState<ProvenancePayload | null>(null);
  const [briefing, setBriefing] = useState<BriefingPayload | null>(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);

  useEffect(() => {
    Promise.allSettled([
      fetch(`${apiBase}/api/soul`).then((r) => (r.ok ? r.json() : Promise.reject())),
      fetch(`${apiBase}/api/provenance?n=5`).then((r) => (r.ok ? r.json() : Promise.reject())),
    ]).then(([s, p]) => {
      if (s.status === "fulfilled") {
        const raw = s.value as { soul?: { identity?: Record<string, string> }; cluster_id?: string };
        const identity = raw?.soul?.identity ?? {};
        setSoul({
          name: identity.name,
          architect: identity.architect,
          cluster_id: raw?.cluster_id ?? identity.cluster_id,
          motto: identity.motto,
          seal: identity.seal,
          soul_language: identity.soul_language,
          origin: identity.origin,
        });
      }
      if (p.status === "fulfilled") setProvenance(p.value);
    });
  }, [apiBase]);

  function fetchBriefing() {
    setLoadingBriefing(true);
    fetch(`${apiBase}/api/briefing`)
      .then((r) => r.json())
      .then((d) => setBriefing(d))
      .catch(() => {})
      .finally(() => setLoadingBriefing(false));
  }

  return (
    <div className="settings-shell">
      <style>{chromeCss + settingsCss}</style>

      <TopBar active="settings" />

      <section className="main">
        <aside className="panel left">
          <div className="adinkra">◆</div>
          <h1>SETTINGS</h1>
          <div className="kicker">COMMAND PARAMETERS</div>
          <p className="sub">Connection keys, tokens, and live cluster identity for the Nairobi-α Command Center.</p>

          {soul && (
            <div className="box">
              <h3>CLUSTER SOUL</h3>
              {soul.name && <div className="row"><span>NAME</span><span style={{ color: "var(--gold)" }}>{soul.name}</span></div>}
              {soul.architect && <div className="row"><span>ARCHITECT</span><span>{soul.architect}</span></div>}
              {soul.cluster_id && <div className="row"><span>CLUSTER</span><span>{soul.cluster_id}</span></div>}
              {soul.origin && <div className="row"><span>ORIGIN</span><span style={{ fontSize: "10px" }}>{soul.origin}</span></div>}
              {soul.soul_language && <div className="row"><span>SOUL LANGUAGE</span><span style={{ color: "var(--cyan)" }}>{soul.soul_language}</span></div>}
              {soul.seal && <div className="row"><span>SEAL</span><span style={{ color: "var(--gold)" }}>{soul.seal}</span></div>}
              {soul.motto && <div className="motto">{soul.motto}</div>}
            </div>
          )}

          {provenance && (
            <div className="box">
              <h3>PROVENANCE</h3>
              <div className="row"><span>TOTAL CYCLES</span><span style={{ color: "var(--cyan)" }}>{provenance.total?.toLocaleString() ?? "—"}</span></div>
              <div className="row"><span>STORE</span><span style={{ fontSize: "10px" }}>{provenance.scope ?? "runtime"}</span></div>
            </div>
          )}

          <div className="proverb">"Observe what is real. Protect what matters."</div>
        </aside>

        <main className="panel config">
          <div className="kicker">SYSTEM CONFIGURATION</div>

          <div className="box">
            <div className="row"><span>CLUSTER ID</span><span>{soul?.cluster_id ?? "nairobi-alpha"}</span></div>
            <div className="row"><span>GRID API</span><span>{apiBase}</span></div>
            <div className="row"><span>PIPER TTS</span><span>http://localhost:41071</span></div>
            <div className="row"><span>OLLAMA PROXY</span><span>127.0.0.1:11434</span></div>
            <div className="row"><span>NEO4J BOLT</span><span>bolt://localhost:47687</span></div>
            <div className="row"><span>MCP GATE</span><span>http://localhost:41020</span></div>
          </div>

          <div className="box">
            <h3 style={{ color: "var(--gold)" }}>COVENANT THRESHOLDS</h3>
            <div className="row"><span>IKANG (MIND)</span><span>0.75</span></div>
            <div className="row"><span>MMỌNG (ESSENCE)</span><span>0.70</span></div>
            <div className="row"><span>AFIM (BODY)</span><span>0.65</span></div>
            <div className="row"><span>ISONG (SPIRIT)</span><span>0.80</span></div>
            <div className="row"><span>WOO THRESHOLD</span><span style={{ color: "var(--gold)" }}>0.97</span></div>
          </div>

          <div className="box">
            <div className="briefing-head">
              <h3 style={{ color: "var(--cyan)" }}>WORLD BRIEFING</h3>
              <button onClick={fetchBriefing} disabled={loadingBriefing}>
                {loadingBriefing ? "LOADING…" : "REQUEST BRIEFING"}
              </button>
            </div>
            {briefing?.message ? (
              <div className="briefing-body">
                <p>{briefing.message}</p>
                <div className="briefing-meta">
                  <span>WEATHER: <span style={{ color: briefing.weather?.live ? "var(--green)" : "var(--gold)" }}>{briefing.weather?.live ? `LIVE (${briefing.weather.provider ?? "?"})` : "OFFLINE"}</span></span>
                  <span>FLIGHTS: <span style={{ color: briefing.flights?.live ? "var(--green)" : "var(--gold)" }}>{briefing.flights?.live ? "LIVE" : "OFFLINE"}</span></span>
                </div>
                {briefing.signals && <div className="briefing-signals">{briefing.signals}</div>}
              </div>
            ) : (
              <p className="briefing-placeholder">Press REQUEST BRIEFING to generate a live AI briefing with weather, flights, and world signals.</p>
            )}
          </div>

          {provenance?.recent && provenance.recent.length > 0 && (
            <div className="box">
              <h3 style={{ color: "var(--purple)" }}>RECENT PROVENANCE</h3>
              {provenance.recent.map((ev, i) => (
                <div className="row" key={i}>
                  <span style={{ color: "var(--gold)" }}>{(ev.type ?? "event").toUpperCase()}</span>
                  <span style={{ fontSize: "10px" }}>{ev.timestamp?.slice(11, 19) ?? "—"}</span>
                </div>
              ))}
            </div>
          )}
        </main>
      </section>

      <FooterBar />
    </div>
  );
}

const settingsCss = `
.settings-shell {
  --cyan: var(--color-neon-cyan, #00d8ff);
  --gold: var(--color-neon-gold, #f6c453);
  --green: var(--color-neon-green, #25ff8a);
  --purple: var(--color-neon-purple, #b46cff);
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
  background: radial-gradient(circle at 50% 18%, #102233 0, #050913 38%, #000 100%);
}
.settings-shell .main { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 10px; min-height: 0; }
.settings-shell .panel { position: relative; background: linear-gradient(180deg, rgba(5,16,29,.82), rgba(2,8,15,.92)); border: 1px solid rgba(0,216,255,.2); box-shadow: 0 0 32px rgba(0,216,255,.055), inset 0 0 34px rgba(0,216,255,.025); border-radius: 6px; overflow: hidden; }
.settings-shell .panel:before, .settings-shell .panel:after { content: ""; position: absolute; width: 22px; height: 22px; border-color: var(--cyan); opacity: .42; }
.settings-shell .panel:before { left: 7px; top: 7px; border-top: 1px solid; border-left: 1px solid; }
.settings-shell .panel:after { right: 7px; bottom: 7px; border-right: 1px solid; border-bottom: 1px solid; }
.settings-shell .left { padding: 22px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
.settings-shell .adinkra { position: absolute; right: 12px; top: 11px; color: var(--gold); opacity: .35; font-size: 21px; }
.settings-shell h1 { margin: 0 0 8px; color: var(--gold); font-size: 24px; font-weight: 500; letter-spacing: .2em; }
.settings-shell .kicker { color: var(--cyan); font-size: 12px; letter-spacing: .22em; }
.settings-shell .sub { color: #c8d0dc; font-size: 13px; line-height: 1.6; margin: 0; }
.settings-shell .box { padding: 15px; border: 1px solid rgba(0,216,255,.16); background: rgba(0,0,0,.22); }
.settings-shell .box h3 { margin: 0 0 12px; color: var(--cyan); font-size: 12px; font-weight: 500; letter-spacing: .2em; }
.settings-shell .row { display: flex; justify-content: space-between; gap: 10px; border-bottom: 1px solid rgba(255,255,255,.08); padding: 8px 0; color: #aeb8c8; font-size: 12px; }
.settings-shell .row span:last-child { color: #dbe8f6; max-width: 60%; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.settings-shell .motto { margin-top: 10px; padding-left: 10px; border-left: 2px solid var(--gold); font-size: 10px; line-height: 1.6; color: #d9c58c; font-style: italic; }
.settings-shell .proverb { margin-top: auto; padding: 12px; border-left: 2px solid var(--gold); background: rgba(246,196,83,.04); color: #d9c58c; font-size: 11px; line-height: 1.6; }
.settings-shell .config { padding: 18px 22px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.settings-shell .briefing-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.settings-shell .briefing-head h3 { margin: 0; }
.settings-shell .briefing-head button {
  font-size: 10px; padding: 6px 12px; border-radius: 4px; letter-spacing: .15em;
  background: rgba(2,12,20,.8); border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; font-family: inherit;
}
.settings-shell .briefing-head button:disabled { opacity: .6; cursor: wait; }
.settings-shell .briefing-body p { line-height: 1.7; color: #dbe8f6; opacity: .85; margin: 0 0 8px; font-size: 12px; }
.settings-shell .briefing-meta { display: flex; gap: 16px; font-size: 10px; color: var(--muted); margin-bottom: 6px; }
.settings-shell .briefing-signals { font-size: 10px; line-height: 1.6; color: #dbe8f6; opacity: .6; }
.settings-shell .briefing-placeholder { color: var(--muted); font-size: 12px; margin: 0; }
@media (max-width: 1200px) {
  .settings-shell { height: auto; min-height: 100vh; overflow: auto; }
  .settings-shell .main { grid-template-columns: 1fr; }
}
`;
