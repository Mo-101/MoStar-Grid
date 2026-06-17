import { useEffect, useMemo, useRef, useState } from "react";
import { useDashboard } from "@/routes/dashboard";
import { TopBar, FooterBar, chromeCss } from "@/components/grid/ChromeNav";

const API_BASE = import.meta.env.VITE_GRID_API_BASE ?? "http://localhost:41010";

type GraphStats = {
  nodes?: number;
  total_nodes?: number;
  relationships?: number;
  total_relationships?: number;
  labels?: Record<string, number>;
  label_counts?: Record<string, number>;
  connected?: boolean;
};

type DensityPayload = {
  total_nodes?: number;
  total_relationships?: number;
  label_distribution?: Record<string, number>;
  promotion_ready?: boolean;
  promotion_gaps?: string[];
};

const LABEL_COLORS: Record<string, string> = {
  Entity: "var(--gold)",
  GridEvent: "var(--cyan)",
  WooUtterance: "var(--purple)",
  BriefingLog: "var(--green)",
  StartupReport: "#f59e0b",
  FoundationalMemory: "#ec4899",
  Agent: "#168bff",
  ExecutorHeartbeat: "#21ff64",
};

function colorFor(label: string) {
  return LABEL_COLORS[label] ?? "var(--cyan)";
}

export default function MindGraph() {
  const { census } = useDashboard();
  const [graphStats, setGraphStats] = useState<GraphStats | null>(null);
  const [density, setDensity] = useState<DensityPayload | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const nodesWrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    async function load() {
      const [gs, d] = await Promise.allSettled([
        fetch(`${API_BASE}/api/mindgraph/status`).then((r) => (r.ok ? r.json() : Promise.reject())),
        fetch(`${API_BASE}/api/density`).then((r) => (r.ok ? r.json() : Promise.reject())),
      ]);
      if (gs.status === "fulfilled") setGraphStats(gs.value);
      if (d.status === "fulfilled") setDensity(d.value);
    }
    load();
    const poll = setInterval(load, 20000);
    return () => clearInterval(poll);
  }, []);

  const nodes = census?.nodes ?? graphStats?.nodes ?? graphStats?.total_nodes;
  const rels = census?.relationships ?? graphStats?.relationships ?? graphStats?.total_relationships;
  const labels = graphStats?.labels ?? graphStats?.label_counts ?? density?.label_distribution ?? {};
  const labelEntries = useMemo(
    () => Object.entries(labels).sort(([, a], [, b]) => b - a).slice(0, 10),
    [labels],
  );
  const maxCount = labelEntries[0]?.[1] ?? 1;
  const promotionReady = density?.promotion_ready;

  // Position label bubbles in a ring around the central node, sized by relative weight.
  const bubbleNodes = useMemo(() => {
    return labelEntries.map(([label, count], i) => {
      const angle = (i / Math.max(labelEntries.length, 1)) * 2 * Math.PI - Math.PI / 2;
      const r = 38;
      const size = 16 + Math.round((count / maxCount) * 26);
      return {
        label,
        count,
        color: colorFor(label),
        leftPct: 50 + r * Math.cos(angle),
        topPct: 50 + r * Math.sin(angle),
        size,
      };
    });
  }, [labelEntries, maxCount]);

  // Draw connecting lines from the center to each bubble.
  useEffect(() => {
    const cv = canvasRef.current;
    const wrap = nodesWrapRef.current;
    if (!cv || !wrap) return;
    const draw = () => {
      const r = wrap.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      cv.width = r.width * dpr;
      cv.height = r.height * dpr;
      const ctx = cv.getContext("2d");
      if (!ctx) return;
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, r.width, r.height);
      const cx = r.width / 2;
      const cy = r.height / 2;
      ctx.lineCap = "round";
      for (const n of bubbleNodes) {
        const x = (n.leftPct / 100) * r.width;
        const y = (n.topPct / 100) * r.height;
        ctx.strokeStyle = `${n.color}aa`;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
    };
    draw();
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, [bubbleNodes]);

  return (
    <div className="graph-shell">
      <style>{chromeCss + graphCss}</style>

      <TopBar active="mindgraph" />

      <section className="main">
        <aside className="left">
          <div className="panel lbox">
            <h3>GRAPH OVERVIEW</h3>
            <div className="metric"><small>TOTAL NODES</small><b>{nodes?.toLocaleString() ?? "—"}</b></div>
            <div className="metric"><small>RELATIONSHIPS</small><b>{rels?.toLocaleString() ?? "—"}</b></div>
            {graphStats?.connected !== undefined && (
              <div className="row"><span>CONNECTION</span><span style={{ color: graphStats.connected ? "var(--green)" : "#ef4444" }}>{graphStats.connected ? "LIVE" : "OFFLINE"}</span></div>
            )}
            {promotionReady !== undefined && (
              <div className="row"><span>PROMOTION</span><span style={{ color: promotionReady ? "var(--green)" : "var(--muted)" }}>{promotionReady ? "READY" : "PENDING"}</span></div>
            )}
          </div>

          <div className="panel lbox">
            <h3>NODE CATEGORIES</h3>
            {labelEntries.length === 0 && <div className="row"><span>AWAITING DATA</span><span>—</span></div>}
            {labelEntries.map(([label, count]) => (
              <div className="row" key={label}>
                <span><i className="dot" style={{ background: colorFor(label), color: colorFor(label) }} />{label.toUpperCase()}</span>
                <span>{count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </aside>

        <main className="panel graph">
          <div className="graph-title">MIND GRAPH<small>THE LIVING KNOWLEDGE NETWORK</small></div>
          <div className="canvas">
            <canvas ref={canvasRef} />
            <div className="nodes" ref={nodesWrapRef}>
              <div className="node core">
                <div className="bubble">
                  <div className="percent">
                    {nodes !== undefined ? (nodes >= 1000 ? `${(nodes / 1000).toFixed(0)}K` : nodes) : "—"}
                    <small>NODES</small>
                  </div>
                </div>
              </div>
              {bubbleNodes.map((n) => (
                <div
                  className="node"
                  key={n.label}
                  style={{ left: `${n.leftPct}%`, top: `${n.topPct}%`, "--node-color": n.color } as React.CSSProperties}
                >
                  <div className="bubble" style={{ width: n.size + 40, height: n.size + 40 }} />
                  <b>{n.label.toUpperCase()}</b>
                  <span>{n.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </main>

        <aside className="right">
          <div className="panel rbox">
            <h3>SEMANTIC REGISTRY</h3>
            <p className="desc">
              Primary cognitive substrate of MoStar Grid. Semantic connections and entities
              synchronized in Nairobi-α.
            </p>
            <div className="row"><span>NODES</span><span style={{ color: "var(--gold)" }}>{nodes?.toLocaleString() ?? "—"}</span></div>
            <div className="row"><span>RELATIONSHIPS</span><span style={{ color: "var(--cyan)" }}>{rels?.toLocaleString() ?? "—"}</span></div>
          </div>
          <div className="panel rbox">
            <h3>NODE TYPE BREAKDOWN</h3>
            {labelEntries.map(([label, count]) => {
              const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
              return (
                <div key={label} className="bar-row">
                  <div className="bar-label"><span style={{ color: colorFor(label) }}>{label.toUpperCase()}</span><span>{count.toLocaleString()}</span></div>
                  <div className="bar"><div className="fill" style={{ width: `${pct}%`, background: colorFor(label), boxShadow: `0 0 8px ${colorFor(label)}` }} /></div>
                </div>
              );
            })}
          </div>
        </aside>
      </section>

      <FooterBar />
    </div>
  );
}

const graphCss = `
.graph-shell {
  --cyan: var(--color-neon-cyan, #00d8ff);
  --gold: var(--color-neon-gold, #f6c453);
  --green: var(--color-neon-green, #00ff88);
  --purple: var(--color-neon-purple, #b46cff);
  --muted: #8aa0b8;
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
  background: radial-gradient(circle at 52% 28%, #0e2440 0, #030914 38%, #000 100%);
}
.graph-shell .main { display: grid; grid-template-columns: 285px minmax(0, 1fr) 335px; gap: 10px; min-height: 0; }
.graph-shell .panel { position: relative; background: linear-gradient(180deg, rgba(4,14,28,.80), rgba(2,8,16,.92)); border: 1px solid rgba(0,216,255,.24); box-shadow: 0 0 32px rgba(0,216,255,.05), inset 0 0 34px rgba(0,216,255,.022); border-radius: 6px; overflow: hidden; }
.graph-shell .panel:before, .graph-shell .panel:after { content: ""; position: absolute; width: 22px; height: 22px; border-color: var(--cyan); opacity: .42; }
.graph-shell .panel:before { left: 7px; top: 7px; border-top: 1px solid; border-left: 1px solid; }
.graph-shell .panel:after { right: 7px; bottom: 7px; border-right: 1px solid; border-bottom: 1px solid; }
.graph-shell .left, .graph-shell .right { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; min-height: 0; }
.graph-shell .lbox, .graph-shell .rbox { padding: 17px 20px; }
.graph-shell .lbox h3, .graph-shell .rbox h3 { margin: 0 0 14px; color: var(--cyan); font-weight: 500; font-size: 12px; letter-spacing: .2em; }
.graph-shell .metric { padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,.08); }
.graph-shell .metric small { display: block; color: #91a1b6; letter-spacing: .12em; font-size: 10px; }
.graph-shell .metric b { display: block; margin-top: 4px; color: var(--cyan); font-size: 20px; font-weight: 400; }
.graph-shell .row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,.07); padding: 7px 0; font-size: 11px; color: #c2ccda; gap: 8px; }
.graph-shell .row span:first-child { display: flex; align-items: center; }
.graph-shell .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 9px; box-shadow: 0 0 12px currentColor; flex-shrink: 0; }
.graph-shell .desc { font-size: 12px; line-height: 1.6; color: #c8d0dc; margin: 0 0 14px; }
.graph-shell .graph { position: relative; overflow: hidden; }
.graph-shell .graph-title { position: absolute; top: 10px; left: 0; right: 0; text-align: center; z-index: 20; color: var(--gold); letter-spacing: .28em; font-size: 17px; pointer-events: none; }
.graph-shell .graph-title small { display: block; color: #c4ccda; letter-spacing: .2em; font-size: 11px; margin-top: 6px; }
.graph-shell .canvas { position: absolute; inset: 0; }
.graph-shell .canvas:before { content: ""; position: absolute; inset: 0; opacity: .14; background-image: radial-gradient(circle, #00d8ff 1px, transparent 1.4px); background-size: 28px 28px; mask-image: radial-gradient(circle at 50% 50%, #000 0 62%, transparent 92%); }
.graph-shell canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
.graph-shell .nodes { position: absolute; inset: 0; }
.graph-shell .node { position: absolute; transform: translate(-50%, -50%); text-align: center; z-index: 8; }
.graph-shell .node.core { left: 50%; top: 50%; z-index: 9; }
.graph-shell .node .bubble {
  margin: auto; border-radius: 50%; display: grid; place-items: center; position: relative;
  background: radial-gradient(circle at 67% 28%, var(--node-color, var(--cyan)) 0, transparent 60%), #191932;
  box-shadow: 0 0 26px color-mix(in srgb, var(--node-color, var(--cyan)), transparent 35%), inset 0 0 12px rgba(255,255,255,.25);
  border: 1px solid var(--node-color, var(--cyan));
  animation: graphBreathe 3.2s infinite;
  width: 44px; height: 44px;
}
.graph-shell .node.core .bubble {
  width: 130px; height: 130px;
  background: radial-gradient(circle at 70% 30%, rgba(246,196,83,.5) 0, transparent 45%), linear-gradient(269deg, rgba(227,35,255,.25), rgba(117,23,248,.45)), #191932;
  border: 2px solid var(--gold);
  box-shadow: 0 0 60px rgba(246,196,83,.5), 0 0 45px rgba(117,23,248,.33), inset 0 0 30px rgba(246,196,83,.2);
}
.graph-shell .percent { color: white; font-family: Arial, sans-serif; font-size: 24px; font-weight: 700; }
.graph-shell .percent small { display: block; font-size: 9px; color: var(--cyan); letter-spacing: .2em; font-weight: 400; margin-top: 2px; }
.graph-shell .node b { display: block; margin-top: 8px; font-size: 11px; letter-spacing: .12em; color: white; text-shadow: 0 0 8px #000; }
.graph-shell .node span { display: block; font-size: 9px; letter-spacing: .1em; color: var(--node-color, var(--cyan)); }
.graph-shell .right .bar-row { margin-bottom: 12px; }
.graph-shell .right .bar-label { display: flex; justify-content: space-between; font-size: 10px; margin-bottom: 5px; color: var(--muted); }
.graph-shell .right .bar { height: 4px; background: #0b1824; }
.graph-shell .right .fill { height: 100%; transition: width .4s ease; }
@keyframes graphBreathe { 50% { filter: brightness(1.3); transform: scale(1.04); } }
@media (max-width: 1200px) {
  .graph-shell { height: auto; min-height: 100vh; overflow: auto; }
  .graph-shell .main { grid-template-columns: 1fr; }
  .graph-shell .graph { min-height: 520px; }
}
`;
