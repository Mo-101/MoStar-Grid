import { useEffect, useState } from "react";
import { TopBar, FooterBar, chromeCss } from "@/components/grid/ChromeNav";

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "http://localhost:41010";

type MoScript = {
  id: string;
  name: string;
  trigger: string;
  status: string;
  resonance: string;
  description?: string;
  layer?: string;
};

const SEED_SCRIPTS: MoScript[] = [
  { id: "SCROLL-001", name: "covenant_check.msc", trigger: "on_agent_action", status: "ACTIVE", resonance: "1.00" },
  { id: "SCROLL-002", name: "truth_engine.msc", trigger: "on_query", status: "ACTIVE", resonance: "0.99" },
  { id: "SCROLL-003", name: "soul_layer_spiritual.msc", trigger: "on_awakening", status: "ACTIVE", resonance: "1.00" },
  { id: "SCROLL-004", name: "guardian_swarm_protocol.msc", trigger: "on_threat", status: "STANDBY", resonance: "0.89" },
  { id: "SCROLL-005", name: "zero_leakage_audit.msc", trigger: "on_fund_move", status: "ACTIVE", resonance: "1.00" },
  { id: "SCROLL-006", name: "flameborn_verdict.msc", trigger: "on_vote", status: "ACTIVE", resonance: "0.96" },
];

function normalizeScript(raw: unknown, index: number): MoScript {
  if (typeof raw === "string") {
    return { id: `SCROLL-${String(index + 1).padStart(3, "0")}`, name: raw, trigger: "on_event", status: "ACTIVE", resonance: "1.00" };
  }
  if (typeof raw === "object" && raw !== null) {
    const s = raw as Record<string, unknown>;
    return {
      id: String(s.id ?? s.script_id ?? `SCROLL-${String(index + 1).padStart(3, "0")}`),
      name: String(s.name ?? s.script_name ?? s.filename ?? "unknown.msc"),
      trigger: String(s.trigger ?? s.event ?? "on_event"),
      status: String(s.status ?? s.state ?? "ACTIVE").toUpperCase(),
      resonance: String(s.resonance ?? s.score ?? "1.00"),
      description: s.description ? String(s.description) : undefined,
      layer: s.layer ? String(s.layer) : undefined,
    };
  }
  return { id: `SCROLL-${String(index + 1).padStart(3, "0")}`, name: "script.msc", trigger: "on_event", status: "ACTIVE", resonance: "1.00" };
}

export default function MoScripts() {
  const [scripts, setScripts] = useState<MoScript[]>(SEED_SCRIPTS);
  const [live, setLive] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/moscripts`)
      .then((r) => r.json())
      .then((data) => {
        const raw: unknown[] = Array.isArray(data) ? data : Array.isArray(data?.moscripts) ? data.moscripts : [];
        if (raw.length > 0) {
          setScripts(raw.map(normalizeScript));
          setLive(true);
        }
      })
      .catch(() => {});
  }, []);

  const active = scripts.filter((s) => s.status === "ACTIVE").length;
  const standby = scripts.filter((s) => s.status !== "ACTIVE").length;
  const lastExec = scripts.find((s) => s.status === "ACTIVE")?.name?.replace(".msc", "") ?? "—";

  return (
    <div className="scroll-shell">
      <style>{chromeCss + scrollCss}</style>

      <TopBar active="moscripts" />

      <section className="main">
        <aside className="panel left">
          <div className="adinkra">◆</div>
          <h1>MOSCRIPTS</h1>
          <div className="kicker">COVENANT RUNTIME</div>
          <p className="sub">
            Active scrolls and executable covenant protocols that govern agent behavior, fund
            flows, and grid operations.
          </p>
          <div className="box">
            <h3>RUNTIME STATUS</h3>
            <div className="row"><span>ENGINE</span><span style={{ color: live ? "var(--green)" : "var(--gold)" }}>{live ? "LIVE" : "ONLINE"}</span></div>
            <div className="row"><span>ACTIVE SCRIPTS</span><span style={{ color: "var(--cyan)" }}>{active}</span></div>
            <div className="row"><span>STANDBY</span><span>{standby}</span></div>
            <div className="row"><span>LAST EXECUTED</span><span style={{ fontSize: "10px" }}>{lastExec}</span></div>
          </div>
          <div className="proverb">"Words are covenants. Scripts are oaths made executable."</div>
        </aside>

        <main className="panel scrolls">
          <div className="scrolls-head">
            <div className="kicker">SCROLL REGISTRY — ACTIVE PROTOCOLS</div>
            {live && <span className="live-badge">LIVE · {scripts.length} SCRIPTS</span>}
          </div>
          <div className="scrolls-list">
            {scripts.map((s) => (
              <div className="card" key={s.id} style={{ borderColor: s.status === "ACTIVE" ? "rgba(0,216,255,.25)" : "rgba(255,255,255,.1)" }}>
                <div className="card-head">
                  <span className="card-id">{s.id}</span>
                  <span
                    className="status-pill"
                    style={{
                      color: s.status === "ACTIVE" ? "var(--green)" : "var(--muted)",
                      borderColor: s.status === "ACTIVE" ? "rgba(37,255,138,.35)" : "rgba(255,255,255,.2)",
                      background: s.status === "ACTIVE" ? "rgba(37,255,138,.1)" : "rgba(255,255,255,.04)",
                    }}
                  >
                    {s.status}
                  </span>
                </div>
                <div className="card-name">{s.name}</div>
                <div className="card-meta">
                  <span>TRIGGER: <b>{s.trigger}</b></span>
                  <span>RESONANCE: <b style={{ color: "var(--gold)" }}>{s.resonance}</b></span>
                </div>
              </div>
            ))}
          </div>
        </main>
      </section>

      <FooterBar />
    </div>
  );
}

const scrollCss = `
.scroll-shell {
  --cyan: var(--color-neon-cyan, #00d8ff);
  --gold: var(--color-neon-gold, #f6c453);
  --green: var(--color-neon-green, #25ff8a);
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
  background: radial-gradient(circle at 50% 18%, #1a1530 0, #050913 38%, #000 100%);
}
.scroll-shell .main { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 10px; min-height: 0; }
.scroll-shell .panel { position: relative; background: linear-gradient(180deg, rgba(5,16,29,.82), rgba(2,8,15,.92)); border: 1px solid rgba(0,216,255,.2); box-shadow: 0 0 32px rgba(0,216,255,.055), inset 0 0 34px rgba(0,216,255,.025); border-radius: 6px; overflow: hidden; }
.scroll-shell .panel:before, .scroll-shell .panel:after { content: ""; position: absolute; width: 22px; height: 22px; border-color: var(--cyan); opacity: .42; }
.scroll-shell .panel:before { left: 7px; top: 7px; border-top: 1px solid; border-left: 1px solid; }
.scroll-shell .panel:after { right: 7px; bottom: 7px; border-right: 1px solid; border-bottom: 1px solid; }
.scroll-shell .left { padding: 22px; display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
.scroll-shell .adinkra { position: absolute; right: 12px; top: 11px; color: var(--gold); opacity: .35; font-size: 21px; }
.scroll-shell h1 { margin: 0 0 8px; color: var(--gold); font-size: 24px; font-weight: 500; letter-spacing: .2em; }
.scroll-shell .kicker { color: var(--cyan); font-size: 12px; letter-spacing: .22em; }
.scroll-shell .sub { color: #c8d0dc; font-size: 13px; line-height: 1.6; margin: 0; }
.scroll-shell .box { padding: 15px; border: 1px solid rgba(0,216,255,.16); background: rgba(0,0,0,.22); }
.scroll-shell .box h3 { margin: 0 0 12px; color: var(--cyan); font-size: 12px; font-weight: 500; letter-spacing: .2em; }
.scroll-shell .row { display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,.08); padding: 8px 0; color: #aeb8c8; font-size: 12px; }
.scroll-shell .proverb { padding: 12px; border-left: 2px solid var(--gold); background: rgba(246,196,83,.04); color: #d9c58c; font-size: 11px; line-height: 1.6; margin-top: auto; }
.scroll-shell .scrolls { display: flex; flex-direction: column; padding: 18px 22px; min-height: 0; }
.scroll-shell .scrolls-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.scroll-shell .live-badge { font-size: 9px; letter-spacing: .22em; padding: 3px 9px; border-radius: 4px; color: var(--green); border: 1px solid var(--green); background: rgba(37,255,138,.08); }
.scroll-shell .scrolls-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.scroll-shell .card { padding: 14px 16px; border: 1px solid; border-radius: 4px; background: rgba(2,10,18,.6); }
.scroll-shell .card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.scroll-shell .card-id { color: var(--gold); font-size: 12px; font-weight: 700; }
.scroll-shell .status-pill { font-size: 10px; padding: 2px 8px; border-radius: 4px; border: 1px solid; }
.scroll-shell .card-name { color: var(--cyan); font-size: 13px; }
.scroll-shell .card-meta { display: flex; justify-content: space-between; margin-top: 10px; font-size: 11px; color: var(--muted); }
.scroll-shell .card-meta b { color: #dbe8f6; font-weight: 400; }
@media (max-width: 1200px) {
  .scroll-shell { height: auto; min-height: 100vh; overflow: auto; }
  .scroll-shell .main { grid-template-columns: 1fr; }
}
`;
