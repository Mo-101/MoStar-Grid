import { useEffect, useMemo, useState } from "react";
import { useDashboard } from "@/routes/dashboard";
import { TopBar, FooterBar, chromeCss } from "@/components/grid/ChromeNav";

type MemoryEvent = {
  type: string;
  cluster: string;
  content: string;
  created_at: string;
};

type MemoryRow = {
  id: string;
  type: string;
  title: string;
  source: string;
  timestamp: string;
  color: string;
};

const TYPE_COLOR: Record<string, string> = {
  utterance: "var(--gold)",
  moment: "var(--purple)",
  soulprint: "var(--cyan)",
  scroll: "var(--green)",
  covenant_log: "var(--ember)",
  startup_report: "var(--cyan)",
};

function colorForType(type: string) {
  return TYPE_COLOR[type.toLowerCase()] ?? "var(--cyan)";
}

function fmtTime(iso: string): string {
  try { return new Date(iso).toLocaleTimeString("en-GB", { hour12: false }); }
  catch { return iso.slice(11, 19) || "--:--:--"; }
}

function fmtDate(iso: string): string {
  try { return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "2-digit" }).toUpperCase(); }
  catch { return iso.slice(0, 10) || "—"; }
}

const RUNES = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖ".split("");

export default function Sanctuary() {
  const { reports, apiBase } = useDashboard();
  const [memoryEvents, setMemoryEvents] = useState<MemoryEvent[]>([]);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${apiBase}/api/memory/recent`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) => setMemoryEvents(d.events ?? []))
      .catch(() => {});
  }, [apiBase]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const evt of memoryEvents) {
      const key = evt.type || "unknown";
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return Object.entries(counts).sort(([, a], [, b]) => b - a);
  }, [memoryEvents]);

  const rows: MemoryRow[] = useMemo(() => {
    const fromEvents = memoryEvents.map((evt, i) => ({
      id: `evt-${i}`,
      type: evt.type.toUpperCase().replace(/_/g, " "),
      title: evt.content,
      source: evt.cluster.toUpperCase(),
      timestamp: `${fmtDate(evt.created_at)} · ${fmtTime(evt.created_at)}`,
      color: colorForType(evt.type),
    }));
    const fromReports = reports.map((r, i) => ({
      id: `rpt-${i}`,
      type: "STARTUP REPORT",
      title: r.response || `${r.name} reported startup parameters.`,
      source: r.name.toUpperCase(),
      timestamp: r.timestamp ? `${fmtDate(r.timestamp)} · ${fmtTime(r.timestamp)}` : "—",
      color: colorForType("startup_report"),
    }));
    const merged = [...fromEvents, ...fromReports];
    if (!search.trim()) return merged;
    const q = search.toLowerCase();
    return merged.filter((r) => r.title.toLowerCase().includes(q) || r.source.toLowerCase().includes(q));
  }, [memoryEvents, reports, search]);

  const selected = rows.find((r) => r.id === selectedId) ?? rows[0];

  const totalMemories = memoryEvents.length + reports.length;
  const sealed = memoryEvents.length;
  const active = reports.length;
  const covenantLogs = categoryCounts.find(([k]) => k === "covenant_log")?.[1] ?? 0;

  return (
    <div className="vault-shell">
      <style>{chromeCss + vaultCss}</style>

      <TopBar active="sanctuary" />

      <section className="main">
        <aside className="left">
          <div className="panel box">
            <h3>MEMORY OVERVIEW</h3>
            <div className="metric"><small>TOTAL MEMORIES</small><b>{totalMemories.toLocaleString()}</b></div>
            <div className="metric"><small>ARCHIVED EVENTS</small><b>{sealed.toLocaleString()}</b></div>
            <div className="metric"><small>ACTIVE AGENTS</small><b>{active.toLocaleString()}</b></div>
            <div className="metric"><small>COVENANT LOGS</small><b>{covenantLogs.toLocaleString()}</b></div>
            <div className="row"><span>VAULT INTEGRITY</span><span style={{ color: "var(--green)" }}>100%</span></div>
          </div>

          <div className="panel box">
            <h3>MEMORY CATEGORIES</h3>
            {categoryCounts.length === 0 && (
              <div className="row"><span>AWAITING DATA</span><span>—</span></div>
            )}
            {categoryCounts.map(([type, count]) => (
              <div className="row" key={type}>
                <span><i className="dot" style={{ background: colorForType(type), color: colorForType(type) }} />{type.toUpperCase().replace(/_/g, " ")}</span>
                <span>{count}</span>
              </div>
            ))}
          </div>

          <div className="panel box">
            <h3>VAULT CONTROLS</h3>
            <div className="row"><span>TOTAL ENTRIES</span><span>{rows.length}</span></div>
            <div className="row"><span>SOURCE</span><span>{apiBase.replace(/^https?:\/\//, "")}</span></div>
            <div className="row"><span>BRIEFING INDEX</span><span style={{ color: memoryEvents.length > 0 ? "var(--cyan)" : "var(--muted)" }}>{memoryEvents.length > 0 ? "LIVE" : "LOADING"}</span></div>
          </div>
        </aside>

        <main className="panel vault">
          <div className="title">MEMORY VAULT<small>THE SACRED ARCHIVE OF THE GRID</small></div>

          <div className="center">
            <div className="vault-status">
              <h3>VAULT STATUS</h3>
              <div className="lock" />
              <div className="lock-label">SEALED &amp; SECURE</div>
              <div className="row"><span>ENCRYPTION</span><span style={{ color: "var(--green)" }}>AES-256</span></div>
              <div className="row"><span>LAST VERIFIED</span><span>{fmtTime(new Date().toISOString())} UTC</span></div>
              <div className="row"><span>VAULT WARD</span><span style={{ color: "var(--green)" }}>ACTIVE ✓</span></div>
            </div>

            <div className="memory-core">
              <div className="runes">
                {RUNES.map((ch, i) => (
                  <span key={i} style={{ transform: `translate(-50%,-50%) rotate(${(i / RUNES.length) * 360}deg) translateY(-128px) rotate(90deg)` }}>{ch}</span>
                ))}
              </div>
              <div className="vault-crest">{totalMemories.toLocaleString()}</div>
            </div>

            <div className="depth">
              <h3>MEMORY DEPTH</h3>
              <div className="stack">
                {categoryCounts.slice(0, 6).map(([type]) => (
                  <div className="layer" key={type} style={{ color: colorForType(type) }} />
                ))}
              </div>
              <div className="depth-list">
                {categoryCounts.map(([type, count]) => (
                  <div className="row" key={type}><span>{type.toUpperCase().replace(/_/g, " ")}</span><span style={{ color: "var(--gold)" }}>{count}</span></div>
                ))}
                <div className="row"><span>TOTAL</span><span style={{ color: "var(--gold)" }}>{totalMemories}</span></div>
              </div>
            </div>
          </div>

          <div className="tablezone">
            <div className="searchbar">
              <input
                className="search"
                placeholder="Search memories…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <div />
              <div className="sort">{rows.length} ENTRIES</div>
            </div>
            <table className="memtable">
              <thead><tr><th>TYPE</th><th>TITLE / CONTENT</th><th>SOURCE</th><th>TIMESTAMP</th></tr></thead>
              <tbody>
                {rows.slice(0, 8).map((r) => (
                  <tr key={r.id} className={r.id === selected?.id ? "active" : ""} onClick={() => setSelectedId(r.id)}>
                    <td style={{ color: r.color }}>{r.type}</td>
                    <td>{r.title}</td>
                    <td>{r.source}</td>
                    <td>{r.timestamp}</td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr><td colSpan={4} style={{ color: "var(--muted)" }}>Awaiting memory signals…</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </main>

        <aside className="right">
          <div className="panel detail">
            <h3>SELECTED MEMORY</h3>
            {selected ? (
              <>
                <div className="head">
                  <div>
                    <span className="badge">{selected.type}</span>
                    <h2>{selected.source}</h2>
                  </div>
                </div>
                <div className="info">
                  <div className="row"><span>SOURCE</span><span>{selected.source}</span></div>
                  <div className="row"><span>TIMESTAMP</span><span>{selected.timestamp}</span></div>
                  <div className="row"><span>STATUS</span><span style={{ color: "var(--green)" }}>SEALED</span></div>
                  <div className="row"><span>ENCRYPTION</span><span>AES-256</span></div>
                </div>
                <p className="desc">{selected.title}</p>
              </>
            ) : (
              <p className="desc">No memories indexed yet.</p>
            )}
          </div>
          <div className="panel impact">
            <h3>COVENANT OATH ARCHIVE</h3>
            <p className="desc">
              We do not assume perfect agents, perfect memory, perfect state, or perfect humans.
              We observe what is real. We protect what matters. We evolve what is next.{" "}
              <b style={{ color: "var(--gold)" }}>WE ARE THE MOSTAR GRID.</b>
            </p>
          </div>
        </aside>
      </section>

      <FooterBar />
    </div>
  );
}

const vaultCss = `
.vault-shell {
  --cyan: var(--color-neon-cyan, #00d8ff);
  --gold: var(--color-neon-gold, #f6c453);
  --green: var(--color-neon-green, #00ff88);
  --purple: var(--color-neon-purple, #b46cff);
  --ember: var(--color-neon-red, #ff5a2e);
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
  background: radial-gradient(circle at 52% 30%, #0d2138 0, #030914 38%, #000 100%);
}
.vault-shell .main { display: grid; grid-template-columns: 285px minmax(0, 1fr) 320px; gap: 10px; min-height: 0; }
.vault-shell .panel { position: relative; background: linear-gradient(180deg, rgba(4,14,28,.80), rgba(2,8,16,.92)); border: 1px solid rgba(0,216,255,.24); box-shadow: 0 0 32px rgba(0,216,255,.05), inset 0 0 34px rgba(0,216,255,.022); border-radius: 6px; overflow: hidden; }
.vault-shell .panel:before, .vault-shell .panel:after { content: ""; position: absolute; width: 22px; height: 22px; border-color: var(--cyan); opacity: .42; }
.vault-shell .panel:before { left: 7px; top: 7px; border-top: 1px solid; border-left: 1px solid; }
.vault-shell .panel:after { right: 7px; bottom: 7px; border-right: 1px solid; border-bottom: 1px solid; }
.vault-shell .left, .vault-shell .right { display: flex; flex-direction: column; gap: 10px; min-height: 0; overflow-y: auto; }
.vault-shell .box { padding: 16px 18px; }
.vault-shell .box h3 { margin: 0 0 12px; color: var(--cyan); font-size: 12px; letter-spacing: .2em; font-weight: 500; }
.vault-shell .metric { padding: 5px 0; }
.vault-shell .metric small { display: block; color: #91a1b6; letter-spacing: .12em; font-size: 10px; }
.vault-shell .metric b { display: block; margin-top: 3px; color: var(--cyan); font-size: 19px; font-weight: 400; }
.vault-shell .row { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,.07); padding: 7px 0; font-size: 11px; color: #c2ccda; gap: 8px; }
.vault-shell .row span:first-child { display: flex; align-items: center; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vault-shell .dot { width: 9px; height: 9px; border-radius: 2px; display: inline-block; margin-right: 9px; box-shadow: 0 0 12px currentColor; transform: rotate(45deg); flex-shrink: 0; }
.vault-shell .vault { position: relative; display: grid; grid-template-rows: 56px minmax(260px, 1fr) minmax(0, 280px); min-height: 0; }
.vault-shell .title { text-align: center; padding-top: 10px; color: var(--gold); letter-spacing: .3em; font-size: 19px; }
.vault-shell .title small { display: block; color: #c4ccda; letter-spacing: .22em; font-size: 11px; margin-top: 5px; }
.vault-shell .center { position: relative; min-height: 0; }
.vault-shell .vault-status, .vault-shell .depth { position: absolute; top: 0; width: 220px; max-height: 100%; overflow-y: auto; padding: 16px; background: rgba(3,16,27,.8); border: 1px solid rgba(246,196,83,.32); z-index: 15; }
.vault-shell .vault-status { left: 0; }
.vault-shell .depth { right: 0; width: 250px; }
.vault-shell .vault-status h3, .vault-shell .depth h3 { margin: 0 0 14px; color: var(--gold); letter-spacing: .16em; font-size: 12px; font-weight: 500; }
.vault-shell .lock { margin: 14px auto 10px; width: 64px; height: 64px; border-radius: 50%; border: 1px solid rgba(246,196,83,.53); display: grid; place-items: center; box-shadow: 0 0 28px rgba(246,196,83,.33); }
.vault-shell .lock:before { content: "⏚"; color: var(--gold); font-size: 28px; }
.vault-shell .lock-label { text-align: center; color: var(--green); letter-spacing: .12em; font-size: 11px; margin-bottom: 10px; }
.vault-shell .memory-core { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: min(70%, 340px); height: min(90%, 340px); background: radial-gradient(circle at center, rgba(246,196,83,.18) 0, rgba(0,216,255,.08) 27%, transparent 60%); }
.vault-shell .memory-core:before { content: ""; position: absolute; inset: 0; border-radius: 50%; background: repeating-radial-gradient(circle at center, rgba(0,216,255,.38) 0 1px, transparent 1px 28px); mask-image: radial-gradient(circle at 50% 50%, #000 0 70%, transparent 82%); animation: vaultSpin 70s linear infinite; }
.vault-shell .runes { position: absolute; inset: 16%; animation: vaultSpin 120s linear infinite; }
.vault-shell .runes span { position: absolute; left: 50%; top: 50%; color: var(--gold); font-size: 11px; text-shadow: 0 0 8px var(--gold); }
.vault-shell .vault-crest { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 120px; height: 120px; border-radius: 50%; display: grid; place-items: center; border: 1px solid rgba(246,196,83,.67); background: #000b; box-shadow: 0 0 50px rgba(246,196,83,.53); color: var(--gold); font-size: 18px; letter-spacing: .04em; }
.vault-shell .stack { width: 90px; height: 110px; margin: 0 auto 12px; }
.vault-shell .layer { height: 14px; margin: 4px 0; border: 1px solid currentColor; background: currentColor; opacity: .55; box-shadow: 0 0 14px currentColor; }
.vault-shell .tablezone { padding: 10px 14px 14px; min-height: 0; overflow-y: auto; }
.vault-shell .searchbar { display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px; margin-bottom: 8px; align-items: center; }
.vault-shell .search { border: 1px solid rgba(0,216,255,.2); background: #020b13; color: #cfe8f7; padding: 9px 12px; font-size: 12px; font-family: inherit; }
.vault-shell .search::placeholder { color: #7fa1b8; }
.vault-shell .sort { border: 1px solid rgba(0,216,255,.2); background: #020b13; color: var(--cyan); padding: 9px 12px; font-size: 11px; letter-spacing: .1em; text-align: right; }
.vault-shell .memtable { width: 100%; border-collapse: collapse; font-size: 11px; }
.vault-shell .memtable th { text-align: left; color: var(--cyan); font-weight: 400; padding: 8px 10px; border: 1px solid rgba(0,216,255,.1); background: rgba(3,17,29,.8); }
.vault-shell .memtable td { padding: 9px 10px; border-bottom: 1px solid rgba(255,255,255,.06); color: #c6d2de; max-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vault-shell .memtable tr { cursor: pointer; }
.vault-shell .memtable tr.active td { background: rgba(0,216,255,.06); }
.vault-shell .memtable tr:hover td { background: rgba(0,216,255,.04); }
.vault-shell .detail { padding: 18px; overflow-y: auto; }
.vault-shell .detail h3 { margin: 0 0 14px; text-align: center; color: var(--cyan); letter-spacing: .2em; font-size: 12px; font-weight: 500; }
.vault-shell .badge { display: inline-block; border: 1px solid var(--gold); color: var(--gold); padding: 3px 7px; border-radius: 3px; font-size: 10px; margin-bottom: 8px; }
.vault-shell .head h2 { margin: 6px 0 0; color: var(--gold); font-size: 16px; letter-spacing: .07em; }
.vault-shell .info { margin-top: 12px; }
.vault-shell .info .row span:first-child { color: #8998aa; }
.vault-shell .info .row span:last-child { color: var(--cyan); text-align: right; }
.vault-shell .desc { font-size: 12px; line-height: 1.55; color: #c3cfde; margin-top: 12px; }
.vault-shell .impact { padding: 16px; }
.vault-shell .impact h3 { margin: 0 0 10px; color: var(--cyan); letter-spacing: .18em; font-size: 12px; font-weight: 500; }
@keyframes vaultSpin { to { transform: rotate(360deg); } }
@media (max-width: 1200px) {
  .vault-shell { height: auto; min-height: 100vh; overflow: auto; }
  .vault-shell .main { grid-template-columns: 1fr; }
  .vault-shell .vault { min-height: 900px; }
  .vault-shell .center { min-height: 560px; }
  .vault-shell .vault-status, .vault-shell .depth { position: relative; width: auto; margin-bottom: 10px; }
}
`;
