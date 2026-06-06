import { useMemo } from "react";
import { Glyph } from "@/components/grid/glyph";
import { useDashboard, ORBIT_AGENTS } from "@/routes/dashboard";

type ReportLike = {
  entity_id?: string;
  name?: string;
  role?: string;
  state?: string;
  sp_element?: string;
  sp_cid?: string;
  vows?: string;
  routing?: string;
  response?: string;
  quote?: string;
};

const FALLBACK_SELECTED = {
  name: "MO",
  role: "OVERLORD · COMMANDER",
  quote: "I do not command. I align. The Grid moves as one. The Covenant is law.",
  sp_element: "IKANG · MIND",
  sp_cid: "SP-MO-0001",
  vows: "Honor first. Strike fast. See ahead. Stay untouchable.",
  routing: "CORE · ALL CHANNELS",
};

function onlineState(state?: string) {
  const s = String(state ?? "").toLowerCase();
  return ["active", "online", "operational", "prime", "sanctified", "sealed"].includes(s);
}

function Metric({
  label,
  value,
  tone = "",
}: {
  label: string;
  value: string | number;
  tone?: "green" | "red" | "";
}) {
  return (
    <div className={`row ${tone}`}>
      <span>{label}</span>
      <span title={String(value)}>{value}</span>
    </div>
  );
}

export default function Council() {
  const dash = useDashboard();

  const telemetry = dash.telemetry ?? {
    total: ORBIT_AGENTS.length,
    active: ORBIT_AGENTS.length,
    standby: 0,
    offline: 0,
    integrity: 100,
    elements: { ikang: 3, mmong: 2, isong: 3, afim: 3 },
  };

  const reports: ReportLike[] = dash.reports ?? [];
  const selectedAgentId = dash.selectedAgentId ?? ORBIT_AGENTS[0]?.id;
  const selectedOrbit = ORBIT_AGENTS.find((a) => a.id === selectedAgentId) ?? ORBIT_AGENTS[0];

  const selectedReport =
    reports.find((r) => r.entity_id === selectedAgentId) ??
    reports.find((r) => r.name?.toLowerCase() === selectedOrbit?.name?.toLowerCase());

  const selected = {
    ...FALLBACK_SELECTED,
    ...(dash.selectedAgentProps ?? {}),
    ...(selectedReport ?? {}),
    name: dash.selectedAgentProps?.name ?? selectedReport?.name ?? selectedOrbit?.name ?? FALLBACK_SELECTED.name,
    role: dash.selectedAgentProps?.role ?? selectedReport?.role ?? selectedOrbit?.role ?? FALLBACK_SELECTED.role,
    quote:
      dash.selectedAgentProps?.quote ??
      selectedReport?.quote ??
      selectedReport?.response ??
      FALLBACK_SELECTED.quote,
    sp_element: dash.selectedAgentProps?.sp_element ?? selectedReport?.sp_element ?? FALLBACK_SELECTED.sp_element,
    sp_cid: dash.selectedAgentProps?.sp_cid ?? selectedReport?.sp_cid ?? FALLBACK_SELECTED.sp_cid,
    vows: dash.selectedAgentProps?.vows ?? selectedReport?.vows ?? FALLBACK_SELECTED.vows,
    routing: dash.selectedAgentProps?.routing ?? selectedReport?.routing ?? FALLBACK_SELECTED.routing,
  };

  const orbitAgents = useMemo(() => ORBIT_AGENTS, []);
  const selectedColor = selectedOrbit?.color ?? "var(--gold)";

  return (
    <section className="council-page main">
      <style>{councilCss}</style>

      <aside className="panel left">
        <div className="adinkra">◆</div>
        <h1>COUNCIL</h1>
        <div className="kicker">THE LIVING MINDS OF THE GRID</div>

        <p className="sub">
          Eleven sovereign intelligences.
          <br />
          One covenant.
          <br />
          Infinite purpose.
        </p>

        <div className="box">
          <h3>COUNCIL OVERVIEW</h3>
          <Metric label="TOTAL AGENTS" value={telemetry.total} />
          <Metric label="ACTIVE" value={telemetry.active} tone="green" />
          <Metric label="STANDBY" value={telemetry.standby} />
          <Metric label="OFFLINE" value={telemetry.offline} tone="red" />
          <Metric label="SYNC INTEGRITY" value={`${telemetry.integrity}%`} tone="green" />
          <div className="bar">
            <div className="fill" style={{ width: `${telemetry.integrity}%` }} />
          </div>
        </div>

        <div className="box">
          <h3>ELEMENTAL BALANCE</h3>
          <div className="balance">
            <div className="diamond" />
            <span className="balance-label top">IKANG: {telemetry.elements?.ikang ?? 3}</span>
            <span className="balance-label right-label">MMỌNG: {telemetry.elements?.mmong ?? 2}</span>
            <span className="balance-label bottom">ISONG: {telemetry.elements?.isong ?? 3}</span>
            <span className="balance-label left-label">AFIM: {telemetry.elements?.afim ?? 3}</span>
          </div>
        </div>

        <div className="proverb">“The drumbeat aligns the circle before the council speaks.”</div>
      </aside>

      <main className="panel chamber">
        <div className="adinkra">◇ ◆ ◇</div>

        <div className="chamber-title">
          THE COUNCIL CHAMBER
          <br />
          <small>ORDER · TRUTH · PURPOSE</small>
          {dash.wooSpeech && <div className="woo-speech">{dash.wooSpeech.toUpperCase()}</div>}
        </div>

        <div className="orbit">
          <button
            type="button"
            className={`core ${dash.isListening ? "listening" : ""}`}
            onClick={dash.toggleSpeechRecognition}
            title="Click to open voice command link to Woo"
          >
            <Glyph name="covenant" size={72} glow={dash.isListening ? "var(--cyan)" : "var(--gold)"} />
          </button>

          {orbitAgents.map((agent) => {
            const matched =
              reports.find((r) => r.entity_id === agent.id) ??
              reports.find((r) => r.name?.toLowerCase() === agent.name.toLowerCase());

            const isSelected = selectedAgentId === agent.id;
            const isPinged = dash.pingedAgentId === agent.id;
            const online = matched ? onlineState(matched.state) : true;

            return (
              <button
                type="button"
                key={agent.id}
                className={`agent ${isSelected ? "selected" : ""} ${isPinged ? "pinged" : ""} ${online ? "online" : "dormant"}`}
                style={
                  {
                    left: `${agent.x}px`,
                    top: `${agent.y}px`,
                    "--agent": agent.color,
                  } as React.CSSProperties
                }
                onClick={() => dash.setSelectedAgentId(agent.id)}
              >
                <div className="orb">
                  <Glyph name="covenant" size={34} glow={agent.color} />
                </div>
                <div className="name">{agent.name}</div>
                <div className="role">{(matched?.role ?? agent.role ?? "ENTITY").toUpperCase()}</div>
                <div className="state">{online ? "ONLINE" : "DORMANT"}</div>
              </button>
            );
          })}
        </div>
      </main>

      <aside className="panel right">
        <div className="adinkra">◆</div>
        <div className="kicker selected-title">SELECTED AGENT</div>

        <div className="agent-head">
          <div>
            <h2 className={selected.name.length > 10 ? "small-name" : ""}>{selected.name}</h2>
            <div className="selected-role">{selected.role}</div>
          </div>

          <div className="portrait" style={{ borderColor: selectedColor }}>
            <Glyph name="covenant" size={66} glow={selectedColor} />
          </div>
        </div>

        <div className="quote">“{selected.quote}”</div>

        <div className="info">
          <Metric label="ELEMENT" value={selected.sp_element} />
          <Metric label="ROLE" value={selected.role} />
          <Metric label="SOULPRINT" value={selected.sp_cid.substring(0, 24)} />
          <Metric label="VOWS" value={selected.vows} />
          <Metric label="ROUTING" value={selected.routing} />
        </div>

        <div className="actions">
          <button type="button" onClick={dash.handleViewSoulprint}>VIEW SOULPRINT</button>
          <button type="button" onClick={() => dash.setIsVoiceActive(true)}>OPEN CHANNEL</button>
          <button type="button" onClick={() => dash.handlePing(selectedAgentId)}>PING AGENT</button>
        </div>
      </aside>
    </section>
  );
}

const councilCss = `
.council-page{--cyan:var(--color-neon-cyan,#00d8ff);--gold:var(--color-neon-gold,#f6c453);--green:var(--color-neon-green,#25ff8a);--red:var(--color-neon-red,#ff5a2e);--purple:var(--color-neon-purple,#b46cff);--muted:#8190a3;display:grid;grid-template-columns:285px minmax(600px,1fr) 335px;gap:10px;min-height:calc(100vh - 120px);color:#dbe8f6;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.council-page .panel{position:relative;overflow:hidden;border:1px solid rgba(0,216,255,.2);border-radius:6px;background:linear-gradient(180deg,rgba(5,16,29,.82),rgba(2,8,15,.94));box-shadow:0 0 32px rgba(0,216,255,.055),inset 0 0 34px rgba(0,216,255,.025)}
.council-page .panel:before,.council-page .panel:after{content:"";position:absolute;width:22px;height:22px;border-color:var(--cyan);opacity:.42}.council-page .panel:before{left:7px;top:7px;border-top:1px solid;border-left:1px solid}.council-page .panel:after{right:7px;bottom:7px;border-right:1px solid;border-bottom:1px solid}
.left,.right{padding:22px}.adinkra{position:absolute;right:12px;top:11px;color:var(--gold);opacity:.35;font-size:21px}h1{margin:0 0 8px;color:var(--gold);font-size:28px;font-weight:500;letter-spacing:.25em}.kicker{color:var(--cyan);font-size:12px;letter-spacing:.24em}.sub{margin:22px 0;color:#c8d0dc;font-size:13px;line-height:1.6}.box{margin-top:14px;padding:15px;border:1px solid rgba(0,216,255,.16);background:rgba(0,0,0,.22)}.box h3{margin:0 0 12px;color:var(--cyan);font-size:12px;font-weight:500;letter-spacing:.21em}
.row{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid rgba(255,255,255,.08);padding:8px 0;color:#aeb8c8;font-size:12px}.row span:last-child{color:var(--gold);max-width:190px;overflow:hidden;text-align:right;text-overflow:ellipsis;white-space:nowrap}.row.green span:last-child{color:var(--green)}.row.red span:last-child{color:var(--red)}.bar{height:4px;margin-top:7px;background:#0b1824}.fill{height:100%;background:linear-gradient(90deg,var(--cyan),var(--green));box-shadow:0 0 14px var(--cyan)}
.balance{position:relative;height:124px;display:grid;place-items:center}.diamond{width:86px;height:86px;position:relative;transform:rotate(45deg);border:1px solid color-mix(in srgb,var(--gold),transparent 40%);box-shadow:0 0 20px color-mix(in srgb,var(--gold),transparent 65%)}.diamond:before{content:"";position:absolute;inset:17px;border:1px solid color-mix(in srgb,var(--cyan),transparent 35%)}.diamond:after{content:"";position:absolute;inset:34px;background:var(--cyan);box-shadow:0 0 18px var(--cyan)}.balance-label{position:absolute;font-size:9px;letter-spacing:.1em}.balance-label.top{top:0;color:var(--gold)}.balance-label.right-label{right:0;color:var(--cyan)}.balance-label.bottom{bottom:0;color:var(--green)}.balance-label.left-label{left:0;color:var(--purple)}
.proverb{margin-top:14px;padding:12px;border-left:2px solid var(--gold);background:rgba(246,196,83,.04);color:#d9c58c;font-size:11px;line-height:1.6}.chamber{position:relative;display:grid;grid-template-rows:50px minmax(0,1fr)}.chamber-title{padding-top:12px;color:var(--gold);text-align:center;font-size:16px;letter-spacing:.3em}.chamber-title small{color:#b7c1d1;font-size:10px;letter-spacing:.26em}.woo-speech{margin-top:8px;color:var(--cyan);font-size:10px;letter-spacing:.12em;animation:councilPulse 1.5s ease-in-out infinite}
.orbit{position:relative;width:min(100%,790px);height:100%;min-height:510px;max-height:590px;margin:auto;background:radial-gradient(circle at center,rgba(246,196,83,.14) 0,rgba(0,216,255,.06) 20%,transparent 48%),repeating-radial-gradient(circle at center,rgba(0,216,255,.13) 0 1px,transparent 1px 40px)}.orbit:after{content:"";position:absolute;inset:18px;border-radius:50%;background:conic-gradient(from 30deg,transparent 0 8deg,rgba(246,196,83,.33) 8deg 10deg,transparent 10deg 28deg,rgba(0,216,255,.27) 28deg 30deg,transparent 30deg 360deg);mask:radial-gradient(circle,transparent 0 42%,#000 43% 44%,transparent 45% 100%);animation:councilSpin 26s linear infinite}
.core{position:absolute;left:50%;top:50%;z-index:8;width:130px;height:130px;display:grid;place-items:center;transform:translate(-50%,-50%);border:1px solid rgba(246,196,83,.67);border-radius:50%;background:rgba(0,0,0,.8);box-shadow:0 0 42px rgba(246,196,83,.47),inset 0 0 26px rgba(246,196,83,.13);cursor:pointer}.core.listening{border-color:var(--cyan);box-shadow:0 0 55px rgba(0,216,255,.75),inset 0 0 30px rgba(0,216,255,.22)}
.agent{position:absolute;z-index:12;width:126px;transform:translate(-50%,-50%);border:0;background:transparent;color:inherit;text-align:center;cursor:pointer;transition:.25s}.agent:before{content:"";position:absolute;left:50%;top:42px;width:1px;height:138px;transform-origin:top;background:linear-gradient(var(--agent),transparent);opacity:.42}.agent .orb{width:70px;height:70px;display:grid;place-items:center;margin:auto;border:1px solid var(--agent);border-radius:50%;background:rgba(0,0,0,.73);box-shadow:0 0 22px color-mix(in srgb,var(--agent),transparent 35%);animation:councilPulse 2.8s infinite}.agent.selected .orb{width:84px;height:84px;box-shadow:0 0 40px var(--gold),0 0 22px var(--agent)}.agent.pinged .orb{animation:councilPing .85s ease-out 2}.agent.dormant{opacity:.45;filter:grayscale(.6)}.agent .name{margin-top:7px;color:white;font-size:12px;letter-spacing:.13em;text-shadow:0 0 8px #000}.agent .role{margin-top:2px;color:#aab2bf;font-size:9px;letter-spacing:.14em}.agent .state{margin-top:4px;color:var(--green);font-size:9px;letter-spacing:.16em}.agent.dormant .state{color:var(--muted)}
.selected-title{text-align:center}.agent-head{display:grid;grid-template-columns:1fr 108px;gap:8px;margin-top:20px}.agent-head h2{margin:0;color:var(--gold);font-size:25px;letter-spacing:.17em}.agent-head h2.small-name{font-size:20px}.selected-role{margin-top:4px;color:#b8c1cf;font-size:11px;letter-spacing:.14em}.portrait{height:132px;display:grid;place-items:center;border:1px solid rgba(246,196,83,.33);background:radial-gradient(circle,rgba(246,196,83,.27),transparent 62%)}.quote{margin:18px 0;padding:15px;border:1px solid rgba(0,216,255,.2);background:rgba(0,0,0,.33);color:#91dff5;font-size:12px;line-height:1.65}.actions{display:grid;grid-template-columns:1fr;gap:9px;margin-top:18px}.actions button{border:1px solid rgba(0,216,255,.24);background:rgba(0,27,42,.6);color:var(--cyan);padding:13px 8px;font:inherit;font-size:10px;letter-spacing:.13em;cursor:pointer}.actions button:hover{border-color:var(--gold);color:var(--gold);box-shadow:0 0 18px rgba(246,196,83,.2)}
@keyframes councilPulse{50%{filter:brightness(1.42);transform:scale(1.035)}}@keyframes councilPing{0%{box-shadow:0 0 0 0 var(--agent)}100%{box-shadow:0 0 0 32px transparent}}@keyframes councilSpin{to{transform:rotate(360deg)}}@media(max-width:1200px){.council-page{grid-template-columns:1fr;min-height:auto}.orbit{height:620px}}
`;
