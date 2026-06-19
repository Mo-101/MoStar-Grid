import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/grid/parts";

const HTML = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>MoStar Grid — Council Influence Lattice</title>
<style>
:root{
  --bg:#02050a;--panel:rgba(4,13,24,.78);--line:rgba(0,216,255,.20);
  --cyan:#00d8ff;--gold:#f6c453;--green:#25ff8a;--red:#ff5a2e;--purple:#b46cff;
  --violet:#b46cff;--ember:#ff5a2e;
  --muted:#8190a3;--ink:#dbe8f6;--earth:#b56a2a;--leaf:#25d07d;
}
*{box-sizing:border-box}
body{
  margin:0;height:100vh;overflow:hidden;color:var(--ink);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  background:
    radial-gradient(circle at 50% 14%,#10253a 0,#050913 36%,#000 100%);
}
body:before{
  content:"";position:fixed;inset:0;pointer-events:none;opacity:.12;
  background-image:
    linear-gradient(135deg,transparent 42%,var(--gold) 43% 45%,transparent 46%),
    linear-gradient(45deg,transparent 42%,var(--cyan) 43% 45%,transparent 46%);
  background-size:54px 54px;
  mask-image:radial-gradient(circle at 50% 48%,#000 0 52%,transparent 82%);
}
.page{height:100vh;padding:14px;display:grid;grid-template-rows:64px minmax(0,1fr) 28px;gap:10px}
.top{display:grid;grid-template-columns:285px minmax(560px,1fr) 270px;align-items:center;border-bottom:1px solid rgba(0,216,255,.12)}
.brand{display:flex;gap:12px;align-items:center;color:var(--gold);letter-spacing:.38em;font-size:18px;font-weight:800}
.crest{
  width:38px;height:38px;border:1px solid var(--gold);
  clip-path:polygon(50% 0,62% 30%,94% 18%,73% 51%,91% 86%,55% 70%,50% 100%,45% 70%,9% 86%,27% 51%,6% 18%,38% 30%);
  box-shadow:0 0 20px #f6c45366;background:#f6c45322
}
.nav{height:50px;margin:auto;display:flex;border:1px solid rgba(0,216,255,.18);background:rgba(0,0,0,.38);clip-path:polygon(3% 0,97% 0,100% 50%,97% 100%,3% 100%,0 50%)}
.nav div{padding:15px 24px;border-right:1px solid rgba(0,216,255,.16);font-size:11px;letter-spacing:.20em;color:#b8c5d8;white-space:nowrap}
.nav .on{color:var(--gold);background:linear-gradient(180deg,#f6c4531f,transparent);box-shadow:inset 0 -2px var(--gold)}
.status{text-align:right;color:var(--green);letter-spacing:.24em;font-size:11px}
.main{display:grid;grid-template-columns:285px minmax(560px,1fr) 320px;gap:10px;min-height:0}
.panel{
  position:relative;background:linear-gradient(180deg,rgba(5,16,29,.82),rgba(2,8,15,.92));
  border:1px solid var(--line);box-shadow:0 0 32px rgba(0,216,255,.055),inset 0 0 34px rgba(0,216,255,.025);
  border-radius:6px;overflow:hidden
}
.panel:before,.panel:after{content:"";position:absolute;width:22px;height:22px;border-color:var(--cyan);opacity:.42}
.panel:before{left:7px;top:7px;border-top:1px solid;border-left:1px solid}
.panel:after{right:7px;bottom:7px;border-right:1px solid;border-bottom:1px solid}
.box{padding:17px 20px}
.box h3{margin:0 0 14px;color:var(--cyan);font-weight:500;font-size:12px;letter-spacing:.22em}
.metric{padding:9px 0;border-bottom:1px solid rgba(255,255,255,.08)}
.metric small{display:block;color:#91a1b6;letter-spacing:.14em;font-size:10px}
.metric b{display:block;margin-top:4px;color:var(--cyan);font-size:21px;font-weight:400;letter-spacing:.05em}
.row{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(255,255,255,.07);padding:8px 0;font-size:12px;color:#c2ccda}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:10px;box-shadow:0 0 12px currentColor}
.legend .row{font-size:11px}
.seed{margin-top:10px;font-size:10px;line-height:1.5;color:#7f8da0;border-top:1px solid rgba(255,255,255,.06);padding-top:10px}
.lattice{position:relative;overflow:hidden}
.title{position:absolute;top:10px;left:0;right:0;text-align:center;z-index:20;color:var(--gold);letter-spacing:.32em;font-size:19px;pointer-events:none}
.title small{display:block;color:#c4ccda;letter-spacing:.25em;font-size:12px;margin-top:6px}
.canvas{position:absolute;inset:0}
.ring{position:absolute;left:50%;top:50%;border-radius:50%;border:1px solid rgba(0,216,255,.16);transform:translate(-50%,-50%)}
.ring.r1{width:340px;height:340px}
.ring.r2{width:530px;height:530px;border-color:rgba(180,108,255,.14)}
.ring.r3{width:720px;height:720px;border-color:rgba(255,90,46,.10)}
#edges{position:absolute;inset:0;width:100%;height:100%;z-index:1}
#nodes{position:absolute;inset:0;z-index:5}
.node{position:absolute;transform:translate(-50%,-50%);text-align:center;cursor:pointer}
.node .orb{margin:auto;width:var(--s);height:var(--s);border-radius:50%;display:grid;place-items:center;border:1px solid var(--c);background:#000b;box-shadow:0 0 22px color-mix(in srgb,var(--c),transparent 35%);animation:pulse 2.8s infinite}
.node.selected .orb{box-shadow:0 0 40px var(--gold),0 0 22px var(--c)}
.node.dim{opacity:.22}
.node .glyph{width:38%;height:38%;border:1px solid currentColor;color:var(--c);transform:rotate(45deg);box-shadow:0 0 14px currentColor}
.node b{display:block;margin-top:7px;font-size:12px;letter-spacing:.13em;color:white;text-shadow:0 0 8px #000}
.node span{display:block;font-size:9px;letter-spacing:.14em;color:#aab2bf;margin-top:2px}
.footerline{position:absolute;bottom:10px;left:0;right:0;text-align:center;font-size:11px;color:#8aa0b8;letter-spacing:.1em}
.detail{padding:20px}
.head{display:grid;grid-template-columns:1fr 108px;gap:8px}
.head h2{margin:0;color:var(--gold);font-size:25px;letter-spacing:.17em}
.portrait{height:96px;border:1px solid #f6c45355;background:radial-gradient(circle,#f6c45344,transparent 62%);display:grid;place-items:center;border-radius:6px}
.desc{margin:14px 0;font-size:12px;line-height:1.6;color:#c8d0dc}
.info .row span:first-child{color:#aab2bf}.info .row span:last-child{color:var(--cyan);text-align:right}
.paths{padding:18px 20px}
.path{font-size:12px;letter-spacing:.07em;line-height:2;color:#d5dfeb}
.path b{color:var(--gold);font-weight:400}.path .c{color:var(--cyan)}.path .v{color:var(--violet)}.path .e{color:var(--ember)}.path .g{color:var(--green)}
.foot{display:flex;justify-content:space-between;color:#7b8492;letter-spacing:.22em;font-size:10px;align-items:center}
@keyframes pulse{50%{filter:brightness(1.32);transform:scale(1.035)}}
@keyframes dash{to{stroke-dashoffset:-36}}
@media(max-width:1200px){
  body{overflow:auto}
  .page{height:auto;min-height:100vh;grid-template-rows:auto auto auto}
  .top,.main{grid-template-columns:1fr}
  .nav{overflow:auto;width:100%}
  .lattice{height:680px}
}
</style>
</head>
<body>
<div class="page">
  <header class="top">
    <div class="brand">
      <div class="crest"></div>
      <div>MOSTAR GRID<br><small style="font-size:8px;letter-spacing:.16em;color:#d0a843">EXECUTOR OF THE COVENANT</small></div>
    </div>
    <nav class="nav">
      <div class="on">COUNCIL</div>
      <div>LATTICE</div>
      <div>EVENTS</div>
      <div>CONDUIT</div>
      <div>MEMORY</div>
      <div>ANALYTICS</div>
      <div>SETTINGS</div>
    </nav>
    <div class="status">GRID STATUS ● AWAKENED<br><span style="color:white;letter-spacing:.1em">05:42:18 UTC</span></div>
  </header>
  <section class="main">
    <aside class="left" style="display:flex;flex-direction:column;gap:10px">
      <div class="panel box">
        <h3>INFLUENCE MAP</h3>
        <div class="metric"><small>TOTAL NODES</small><b>28</b></div>
        <div class="row"><span>ORIGIN</span><span style="color:var(--gold)">MO</span></div>
        <div class="row"><span>RINGS</span><span style="color:var(--cyan)">3</span></div>
        <div class="row"><span>MODE</span><span style="color:var(--green)">SEED LATTICE</span></div>
      </div>
      <div class="panel box legend">
        <h3>NODE TYPES</h3>
        <div class="row"><span><i class="dot" style="background:var(--gold);color:var(--gold)"></i>ORIGIN</span><span>MO</span></div>
        <div class="row"><span><i class="dot" style="background:var(--cyan);color:var(--cyan)"></i>COUNCIL</span><span>10</span></div>
        <div class="row"><span><i class="dot" style="background:var(--violet);color:var(--violet)"></i>SYSTEMS</span><span>7</span></div>
        <div class="row"><span><i class="dot" style="background:var(--ember);color:var(--ember)"></i>MOMENTS</span><span>4</span></div>
        <div class="row"><span><i class="dot" style="background:var(--green);color:var(--green)"></i>TRUTH / SEAL</span><span>6</span></div>
        <div class="seed">Fallback mode: static seed lattice rendered because live API has not been connected in this preview.</div>
      </div>
      <div class="panel box">
        <h3>LATTICE CONTROLS</h3>
        <div class="row"><span>CONNECTED PATHS</span><span style="color:var(--green)">ACTIVE</span></div>
        <div class="row"><span>LINK PULSE</span><span style="color:var(--cyan)">ON</span></div>
        <div class="row"><span>RING MOTION</span><span style="color:var(--gold)">SLOW</span></div>
        <div class="row"><span>UNCONNECTED DIM</span><span style="color:var(--violet)">READY</span></div>
      </div>
    </aside>
    <main class="panel lattice">
      <div class="title">INFLUENCE LATTICE<small>RESONANCE ACROSS MEMORY · ACTION · PURPOSE</small></div>
      <div class="canvas">
        <div class="ring r3"></div>
        <div class="ring r2"></div>
        <div class="ring r1"></div>
        <svg id="edges"></svg>
        <div id="nodes"></div>
        <div class="footerline">Influence is not hierarchy. It is resonance across memory, action, and purpose.</div>
      </div>
    </main>
    <aside class="right" style="display:flex;flex-direction:column;gap:10px">
      <div class="panel detail">
        <h3 style="margin:0 0 14px;color:var(--cyan);letter-spacing:.22em;font-size:12px;font-weight:500">SELECTED NODE</h3>
        <div class="head">
          <div>
            <h2 id="selName">MO</h2>
            <div style="color:#aab7c7;letter-spacing:.14em;font-size:11px">OVERLORD · ORIGIN NODE</div>
          </div>
          <div class="portrait"><div class="crest" style="width:74px;height:74px"></div></div>
        </div>
        <div class="desc" id="selDesc">Origin node of the MoStar influence lattice. Commands nothing by force; aligns every ring by resonance.</div>
        <div class="info">
          <div class="row"><span>TYPE</span><span id="selType">ORIGIN</span></div>
          <div class="row"><span>RING</span><span id="selRing">0</span></div>
          <div class="row"><span>ELEMENT</span><span id="selElement">IKANG</span></div>
          <div class="row"><span>STATUS</span><span id="selStatus" style="color:var(--green)">ACTIVE</span></div>
          <div class="row"><span>CONNECTED NODES</span><span id="selConnections">27</span></div>
          <div class="row"><span>RELATED MOMENTS</span><span id="selMoments">12</span></div>
        </div>
      </div>
      <div class="panel paths">
        <h3 style="margin:0 0 14px;color:var(--cyan);letter-spacing:.22em;font-size:12px;font-weight:500">BRIGHTENED PATHS</h3>
        <div class="path">
          <b>MO</b> → <span class="c">DEEPCAL</span> → <span class="v">DEEPCAL ENGINE</span> → <span class="e">STARTUP REPORTS</span><br>
          <b>MO</b> → <span class="c">WOO-TAK</span> → <span class="v">WOO INTERPRETER</span> → <span class="g">SOULPRINT SEALS</span><br>
          <b>MO</b> → <span class="c">CODE CONDUIT</span> → <span class="v">THE GRID</span> → <span class="e">UTTERANCES</span>
        </div>
      </div>
    </aside>
  </section>
  <footer class="foot">
    <span>♛ MOSTAR COVENANT</span>
    <span>HONOR FIRST · STRIKE FAST · SEE AHEAD · STAY UNTOUCHABLE</span>
    <span>QSEAL:MO_SOULPRINT_V1</span>
  </footer>
</div>
<script>
const COLORS={origin:"#f6c453",council:"#00d8ff",system:"#b46cff",moment:"#ff5a2e",seal:"#00ff88"};
const nodes=[
{id:"mo",label:"MO",type:"origin",ring:0,element:"ikang",status:"active",description:"Origin node of the MoStar influence lattice. Commands nothing by force; aligns every ring by resonance.",moment:12},
...["DEEPCAL","WOO-TAK","SIGMA","CODE CONDUIT","RAD-X-FLB","TSATSE FLY","FLAMEBORN","MOLINK","ALPHAMOSTAR","THRONELOCK"].map((x,i)=>({id:x.toLowerCase().replaceAll(" ","_").replaceAll("-","_"),label:x,type:"council",ring:1,element:["ikang","mmong","isong","afim"][i%4],status:"active",description:x+" is a sovereign council influence node bound to the origin resonance.",moment:3+i})),
...["FlameBorn","The Grid","CRYPSIDE","DeepCAL Engine","Memory Vault","TruthEngine","Woo Interpreter"].map((x,i)=>({id:x.toLowerCase().replaceAll(" ","_"),label:x,type:i==5?"seal":"system",ring:2,element:["isong","mmong","afim","ikang"][i%4],status:i==5?"sealed":"genesis",description:x+" carries system-level resonance across the lattice.",moment:i+1})),
...["MSG-01 Megadisio","Startup Reports","SoulPrint Seals","Covenant Logs","Utterances"].map((x,i)=>({id:x.toLowerCase().replaceAll(" ","_").replaceAll("-","_"),label:x,type:i==2?"seal":"moment",ring:3,element:["ikang","mmong","isong","afim"][i%4],status:i==2?"sealed":"active",description:x+" is a sealed signal flowing through memory and purpose.",moment:i+2}))
];
const edges=[
["mo","deepcal"],["mo","woo_tak"],["mo","sigma"],["mo","code_conduit"],["mo","rad_x_flb"],["mo","tsatse_fly"],["mo","flameborn"],["mo","molink"],["mo","alphamostar"],["mo","thronelock"],
["deepcal","deepcal_engine"],["woo_tak","woo_interpreter"],["code_conduit","the_grid"],["flameborn","flameborn"],["sigma","truthengine"],["thronelock","memory_vault"],
["deepcal_engine","startup_reports"],["woo_interpreter","utterances"],["truthengine","soulprint_seals"],["memory_vault","covenant_logs"],["the_grid","msg_01_megadisio"],
["mo","the_grid"],["mo","truthengine"],["mo","soulprint_seals"]
];
const pos={};
const area=document.querySelector(".lattice");
const nodesEl=document.getElementById("nodes");
function layout(){
  const w=area.clientWidth,h=area.clientHeight,cx=w/2,cy=h/2+18;
  const radii={0:0,1:170,2:265,3:360};
  const ringGroups={0:nodes.filter(n=>n.ring==0),1:nodes.filter(n=>n.ring==1),2:nodes.filter(n=>n.ring==2),3:nodes.filter(n=>n.ring==3)};
  Object.keys(ringGroups).forEach(r=>{
    const list=ringGroups[r],rr=radii[r];
    list.forEach((n,i)=>{
      const offset=r==1?-90:r==2?-112:-126;
      const ang=(offset+(360/list.length)*i)*Math.PI/180;
      pos[n.id]={x:cx+Math.cos(ang)*rr,y:cy+Math.sin(ang)*rr};
    });
  });
}
function render(){
  layout();nodesEl.innerHTML="";
  nodes.forEach(n=>{
    const p=pos[n.id],s=n.type=="origin"?126:n.ring==1?70:n.ring==2?52:42,c=COLORS[n.type]||COLORS.system;
    const d=document.createElement("div");
    d.className="node "+n.type+(n.id==="mo"?" selected":"");
    d.style.left=p.x+"px";d.style.top=p.y+"px";d.style.setProperty("--c",c);d.style.setProperty("--s",s+"px");
    d.innerHTML='<div class="orb"><div class="glyph"></div></div><b>'+n.label+'</b><span>'+n.type+" · ring "+n.ring+'</span>';
    d.onclick=()=>selectNode(n.id);
    d.onmouseenter=()=>d.classList.add("selected");
    d.onmouseleave=()=>{if(n.id!==selected)d.classList.remove("selected")};
    nodesEl.appendChild(d);
  });
  drawEdges();
}
let selected="mo";
function drawEdges(){
  const svg=document.getElementById("edges");svg.innerHTML="";
  const w=area.clientWidth,h=area.clientHeight;svg.setAttribute("viewBox","0 0 "+w+" "+h);
  edges.forEach(([a,b])=>{
    const pa=pos[a],pb=pos[b]; if(!pa||!pb)return;
    const hot=a===selected||b===selected;
    const line=document.createElementNS("http://www.w3.org/2000/svg","line");
    line.setAttribute("x1",pa.x);line.setAttribute("y1",pa.y);line.setAttribute("x2",pb.x);line.setAttribute("y2",pb.y);
    line.setAttribute("stroke",hot?"#f6c453":"#00d8ff");
    line.setAttribute("stroke-width",hot?"1.8":"0.9");
    line.setAttribute("opacity",hot?".95":".28");
    line.setAttribute("stroke-dasharray","8 10");
    line.style.animation="dash 4s linear infinite";
    line.style.filter=hot?"drop-shadow(0 0 8px #f6c453)":"drop-shadow(0 0 5px #00d8ff)";
    svg.appendChild(line);
  });
}
function selectNode(id){
  selected=id;
  const n=nodes.find(x=>x.id===id);
  document.querySelectorAll(".node").forEach(el=>{
    const label=el.querySelector("b").textContent;
    const node=nodes.find(x=>x.label===label);
    const connected=id==="mo" || edges.some(([a,b])=>(a===id&&b===node.id)||(b===id&&a===node.id)) || node.id===id;
    el.classList.toggle("dim",!connected);
    el.classList.toggle("selected",node.id===id);
  });
  document.getElementById("selName").textContent=n.label;
  document.getElementById("selDesc").textContent=n.description;
  document.getElementById("selType").textContent=n.type.toUpperCase();
  document.getElementById("selRing").textContent=n.ring;
  document.getElementById("selElement").textContent=(n.element||"unknown").toUpperCase();
  document.getElementById("selStatus").textContent=(n.status||"genesis").toUpperCase();
  document.getElementById("selConnections").textContent=edges.filter(([a,b])=>a===id||b===id).length;
  document.getElementById("selMoments").textContent=n.moment||0;
  drawEdges();
}
render();addEventListener("resize",render);
</script>
</body>
</html>
`;

export const Route = createFileRoute("/council")({
  head: () => ({
    meta: [
      { title: "Council Chamber — MoStar Grid" },
      { name: "description", content: "MoStar Grid — Council Influence Lattice." },
    ],
  }),
  component: Page,
});

function Page() {
  return (
    <PageShell active="council">
      <div className="panel relative flex-1 overflow-hidden p-0">
        <iframe
          title="council"
          srcDoc={HTML}
          sandbox="allow-same-origin allow-scripts"
          className="absolute inset-0 h-full w-full border-0"
        />
      </div>
    </PageShell>
  );
}
