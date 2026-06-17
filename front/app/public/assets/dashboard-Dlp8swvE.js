import{r as o,O as k,j as e,a as $}from"./index-Ce_bq-kJ.js";const m="",q="mostar_secret_session_2026",S=o.createContext(null);function H(){const n=o.useContext(S);if(!n)throw new Error("useDashboard must be used inside DashboardLayout");return n}const B=()=>({"X-MoStar-Token":q});async function j(n){const a=await fetch(`${m}${n}`,{headers:B()});if(!a.ok)throw new Error(`${n} → ${a.status}`);return a.json()}function G(n){const a=n.length||11,c=n.filter(g=>["Operational","active","Prime","Sanctified"].includes(g.state??"")).length||Math.floor(a*.8);return{total:a,active:c,standby:Math.max(0,a-c-1),offline:1,integrity:Math.min(100,Math.round(c/a*100)),elements:{ikang:3,mmong:2,isong:3,afim:3}}}function K(){const[n,a]=o.useState([]),[c,g]=o.useState(null),[u,E]=o.useState("mo"),[N,b]=o.useState(null),[_,v]=o.useState(!1),[z,C]=o.useState(!1),[R,A]=o.useState(""),[I,h]=o.useState([]),[O,y]=o.useState(""),[T,f]=o.useState(!1),w=o.useRef(null);o.useEffect(()=>{let t=!1;async function r(){try{const[d,p]=await Promise.allSettled([j("/api/grid/census"),j("/api/grid/startup-reports")]);if(t)return;d.status==="fulfilled"&&g(d.value),p.status==="fulfilled"&&a(p.value.reports??[])}catch{}}r();const l=setInterval(r,15e3);return()=>{t=!0,clearInterval(l)}},[]),o.useEffect(()=>{const t=new EventSource(`${m}/api/stream`);return w.current=t,t.addEventListener("agent_update",r=>{try{const l=JSON.parse(r.data);l.woo_speech&&A(l.woo_speech)}catch{}}),()=>{t.close(),w.current=null}},[]);const s=k.find(t=>t.id===u)??k[0],x=n.find(t=>t.entity_id===u),i={name:s.name,role:x?.role??s.role,quote:s.quote,sp_element:x?.sp_element??s.sp_element,sp_cid:x?.sp_cid??s.sp_cid,vows:s.vows,routing:x?.routing??s.routing};function L(t){b(t),setTimeout(()=>b(null),2e3)}function P(){f(!0)}function M(){C(t=>!t),v(!0)}async function D(t){if(t.trim()){h(r=>[...r,{sender:"user",text:t}]),y("");try{const r=await fetch("http://localhost:41071/speak",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:t,mood:"ceremonial"})});if(!r.ok)throw new Error(`Voice error: ${r.status}`);const l=await r.blob(),d=URL.createObjectURL(l),p=new Audio(d);p.onended=()=>URL.revokeObjectURL(d),await p.play(),h(U=>[...U,{sender:"woo",text:"Speaking."}])}catch{h(r=>[...r,{sender:"woo",text:"Signal lost. Try again."}])}}}const V={apiBase:m,reports:n,census:c,telemetry:G(n),selectedAgentId:u,setSelectedAgentId:E,selectedAgentProps:i,pingedAgentId:N,handlePing:L,handleViewSoulprint:P,isVoiceActive:_,setIsVoiceActive:v,toggleSpeechRecognition:M,isListening:z,wooSpeech:R,voiceLog:I,voiceCommandInput:O,setVoiceCommandInput:y,handleVoiceCommand:D};return e.jsxs(S.Provider,{value:V,children:[e.jsx("style",{children:J}),e.jsx($,{}),T&&e.jsx("div",{className:"fixed inset-0 z-50 flex items-center justify-center bg-black/70",onClick:()=>f(!1),children:e.jsxs("div",{className:"bg-[#060f1a] border border-[#00d8ff40] rounded-xl p-8 max-w-md w-full font-mono text-xs",onClick:t=>t.stopPropagation(),children:[e.jsx("div",{className:"text-[var(--color-neon-gold)] text-sm tracking-widest mb-4",children:"SOULPRINT RECORD"}),e.jsxs("div",{className:"space-y-2 text-[var(--color-foreground)]/80",children:[e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"AGENT"}),e.jsx("span",{children:i.name})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"ELEMENT"}),e.jsx("span",{children:i.sp_element})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"CID"}),e.jsx("span",{className:"text-[9px]",children:i.sp_cid})]}),e.jsxs("div",{className:"flex justify-between",children:[e.jsx("span",{children:"ROUTING"}),e.jsx("span",{children:i.routing})]})]}),e.jsxs("div",{className:"mt-4 italic text-[var(--color-neon-cyan)]/70 text-[10px]",children:['"',i.quote,'"']}),e.jsx("button",{className:"mt-6 w-full border border-[#00d8ff40] py-2 text-[var(--color-neon-cyan)] tracking-widest",onClick:()=>f(!1),children:"CLOSE"})]})})]})}const J=`
:root {
  --gold: var(--color-neon-gold);
  --cyan: var(--color-neon-cyan);
  --green: var(--color-neon-green);
  --purple: var(--color-neon-purple);
  --red: var(--color-neon-red);
  --muted: var(--color-muted-foreground);
}

/* Page grid */
section.main {
  display: grid;
  grid-template-columns: 280px 1fr 1fr;
  gap: 12px;
  height: 100vh;
  padding: 12px;
  box-sizing: border-box;
  background: var(--color-background);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

/* Panel shared */
.panel {
  background: linear-gradient(180deg,oklch(0.22 0.05 270 / 0.75),oklch(0.18 0.05 270 / 0.6));
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}
.panel::before, .panel::after {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: var(--cyan);
  opacity: 0.3;
  pointer-events: none;
}
.panel::before { left:8px; top:8px; border-left:1px solid; border-top:1px solid; }
.panel::after  { right:8px; bottom:8px; border-right:1px solid; border-bottom:1px solid; }

/* Panel type modifiers */
.panel.left { grid-column: 1; display: flex; flex-direction: column; gap: 16px; padding: 20px 18px; }
.panel.right { grid-column: 3; display: flex; flex-direction: column; gap: 14px; padding: 20px 18px; }
.panel.chamber { grid-column: 2; }

/* Typography */
.kicker {
  font-size: 9px;
  letter-spacing: 0.22em;
  color: var(--muted);
  text-transform: uppercase;
}
.adinkra {
  font-size: 18px;
  text-align: center;
  color: var(--gold);
  letter-spacing: 0.3em;
  opacity: 0.7;
}
.sub {
  font-size: 12px;
  color: oklch(0.7 0.04 250);
  line-height: 1.7;
  letter-spacing: 0.05em;
}
.proverb {
  font-size: 10px;
  font-style: italic;
  color: var(--gold);
  opacity: 0.75;
  border-left: 2px solid var(--gold);
  padding: 8px 12px;
  background: oklch(0.82 0.16 85 / 0.05);
  line-height: 1.5;
}

/* Data box */
.box {
  background: oklch(0.14 0.04 270 / 0.5);
  border: 1px solid oklch(0.35 0.08 250 / 0.3);
  border-radius: 6px;
  padding: 12px 14px;
}
.box h3 {
  font-size: 9px;
  letter-spacing: 0.2em;
  color: var(--cyan);
  margin: 0 0 10px;
  text-transform: uppercase;
}
.row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid oklch(1 0 0 / 0.05);
  font-size: 11px;
  letter-spacing: 0.06em;
}
.row span:first-child { color: oklch(0.6 0.04 250); }
.row span:last-child  { color: var(--color-foreground); }
.row.green span:last-child { color: var(--green); }
.row.red   span:last-child { color: var(--red); }

.bar {
  height: 4px;
  background: oklch(0.25 0.05 270);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 8px;
}
.fill {
  height: 100%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
  transition: width 0.4s ease;
}

/* Elemental balance */
.balance {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.diamond {
  width: 40px;
  height: 40px;
  transform: rotate(45deg);
  border: 1px solid var(--gold);
  background: oklch(0.82 0.16 85 / 0.1);
}

/* Agent actions */
.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}
.actions button {
  background: oklch(0.14 0.04 270 / 0.8);
  border: 1px solid oklch(0.50 0.10 250 / 0.4);
  color: var(--cyan);
  font-size: 10px;
  letter-spacing: 0.14em;
  padding: 9px;
  border-radius: 4px;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.actions button:hover {
  border-color: var(--cyan);
  box-shadow: 0 0 12px oklch(0.85 0.16 210 / 0.3);
}

/* Agent head in right panel */
.agent-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.agent-head h2 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--gold);
  margin: 0;
}
.portrait {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--gold);
  background: oklch(0.82 0.16 85 / 0.08);
  box-shadow: 0 0 18px oklch(0.82 0.16 85 / 0.3);
}
.crest {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 1px solid var(--gold);
  background: oklch(0.82 0.16 85 / 0.1);
}
.quote {
  font-size: 11px;
  font-style: italic;
  color: oklch(0.70 0.04 250);
  line-height: 1.5;
  border-left: 2px solid var(--gold);
  padding-left: 10px;
}
.info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Council orbit */
.chamber-title {
  text-align: center;
  font-size: 13px;
  letter-spacing: 0.2em;
  color: var(--gold);
  padding: 18px 0 8px;
  text-transform: uppercase;
}
.orbit {
  position: relative;
  width: 440px;
  height: 440px;
  margin: 0 auto;
}
.core {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px solid var(--gold);
  background: oklch(0.15 0.05 270 / 0.8);
  box-shadow: 0 0 30px oklch(0.82 0.16 85 / 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
}
.agent {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  transition: opacity 0.2s;
  z-index: 1;
}
.agent.selected .orb { box-shadow: 0 0 20px var(--agent, var(--gold)); transform: scale(1.2); }
.agent.pinged .orb   { animation: ping-flash 0.4s ease 3; }
.orb {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--agent, var(--gold));
  background: oklch(0.15 0.05 270 / 0.9);
  box-shadow: 0 0 10px var(--agent, var(--gold));
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
}
.glyph {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--agent, var(--gold));
  box-shadow: 0 0 8px var(--agent, var(--gold));
}
.name  { font-size: 8px;  letter-spacing: 0.12em; color: var(--gold); }
.role  { font-size: 7px;  letter-spacing: 0.08em; color: var(--muted); }
.state { font-size: 7px;  letter-spacing: 0.08em; }

@keyframes ping-flash {
  0%, 100% { box-shadow: 0 0 10px var(--agent, var(--gold)); }
  50%       { box-shadow: 0 0 30px var(--agent, var(--gold)), 0 0 60px var(--agent, var(--gold)); }
}
`;export{K as component,H as useDashboard};
