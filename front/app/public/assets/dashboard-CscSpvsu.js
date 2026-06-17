import{r as o,O as N,j as t,a as B}from"./index-Dr3i6FjB.js";const u="",G="mostar_secret_session_2026",C=o.createContext(null);function W(){const n=o.useContext(C);if(!n)throw new Error("useDashboard must be used inside DashboardLayout");return n}const R=()=>({"X-MoStar-Token":G});async function E(n){const a=await fetch(`${u}${n}`,{headers:R()});if(!a.ok)throw new Error(`${n} → ${a.status}`);return a.json()}function F(n){const a=n.length||11,c=n.filter(h=>["Operational","active","Prime","Sanctified"].includes(h.state??"")).length||Math.floor(a*.8);return{total:a,active:c,standby:Math.max(0,a-c-1),offline:1,integrity:Math.min(100,Math.round(c/a*100)),elements:{ikang:3,mmong:2,isong:3,afim:3}}}function X(){const[n,a]=o.useState([]),[c,h]=o.useState(null),[f,T]=o.useState("mo"),[_,v]=o.useState(null),[z,y]=o.useState(!1),[O,A]=o.useState(!1),[I,L]=o.useState(""),[P,m]=o.useState([]),[M,w]=o.useState(""),[D,b]=o.useState(!1),k=o.useRef(null);o.useEffect(()=>{let e=!1;async function r(){try{const[x,d]=await Promise.allSettled([E("/api/grid/census"),E("/api/grid/startup-reports")]);if(e)return;x.status==="fulfilled"&&h(x.value),d.status==="fulfilled"&&a(d.value.reports??[])}catch{}}r();const s=setInterval(r,15e3);return()=>{e=!0,clearInterval(s)}},[]),o.useEffect(()=>{const e=new EventSource(`${u}/api/stream`);return k.current=e,e.addEventListener("agent_update",r=>{try{const s=JSON.parse(r.data);s.woo_speech&&L(s.woo_speech)}catch{}}),()=>{e.close(),k.current=null}},[]);const i=N.find(e=>e.id===f)??N[0],p=n.find(e=>e.entity_id===f),l={name:i.name,role:p?.role??i.role,quote:i.quote,sp_element:p?.sp_element??i.sp_element,sp_cid:p?.sp_cid??i.sp_cid,vows:i.vows,routing:p?.routing??i.routing};function V(e){v(e),setTimeout(()=>v(null),2e3)}function $(){b(!0)}function U(){A(e=>!e),y(!0)}async function q(e){if(e.trim()){m(r=>[...r,{sender:"user",text:e}]),w("");try{let r=e;try{const g=await fetch(`${u}/api/voice-command`,{method:"POST",headers:{"Content-Type":"application/json",...R()},body:JSON.stringify({text:e})});if(g.ok){const S=await g.json();S.speech&&(r=S.speech)}}catch{}m(g=>[...g,{sender:"woo",text:r}]);const s=await fetch("http://localhost:41071/speak",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:r,mood:"ceremonial"})});if(!s.ok)throw new Error(`Voice error: ${s.status}`);const x=await s.blob(),d=URL.createObjectURL(x),j=new Audio(d);j.onended=()=>URL.revokeObjectURL(d),await j.play()}catch{m(r=>[...r,{sender:"woo",text:"Signal lost. Try again."}])}}}const J={apiBase:u,reports:n,census:c,telemetry:F(n),selectedAgentId:f,setSelectedAgentId:T,selectedAgentProps:l,pingedAgentId:_,handlePing:V,handleViewSoulprint:$,isVoiceActive:z,setIsVoiceActive:y,toggleSpeechRecognition:U,isListening:O,wooSpeech:I,voiceLog:P,voiceCommandInput:M,setVoiceCommandInput:w,handleVoiceCommand:q};return t.jsxs(C.Provider,{value:J,children:[t.jsx("style",{children:H}),t.jsx(B,{}),D&&t.jsx("div",{className:"fixed inset-0 z-50 flex items-center justify-center bg-black/70",onClick:()=>b(!1),children:t.jsxs("div",{className:"bg-[#060f1a] border border-[#00d8ff40] rounded-xl p-8 max-w-md w-full font-mono text-xs",onClick:e=>e.stopPropagation(),children:[t.jsx("div",{className:"text-[var(--color-neon-gold)] text-sm tracking-widest mb-4",children:"SOULPRINT RECORD"}),t.jsxs("div",{className:"space-y-2 text-[var(--color-foreground)]/80",children:[t.jsxs("div",{className:"flex justify-between",children:[t.jsx("span",{children:"AGENT"}),t.jsx("span",{children:l.name})]}),t.jsxs("div",{className:"flex justify-between",children:[t.jsx("span",{children:"ELEMENT"}),t.jsx("span",{children:l.sp_element})]}),t.jsxs("div",{className:"flex justify-between",children:[t.jsx("span",{children:"CID"}),t.jsx("span",{className:"text-[9px]",children:l.sp_cid})]}),t.jsxs("div",{className:"flex justify-between",children:[t.jsx("span",{children:"ROUTING"}),t.jsx("span",{children:l.routing})]})]}),t.jsxs("div",{className:"mt-4 italic text-[var(--color-neon-cyan)]/70 text-[10px]",children:['"',l.quote,'"']}),t.jsx("button",{className:"mt-6 w-full border border-[#00d8ff40] py-2 text-[var(--color-neon-cyan)] tracking-widest",onClick:()=>b(!1),children:"CLOSE"})]})})]})}const H=`
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
`;export{X as component,W as useDashboard};
