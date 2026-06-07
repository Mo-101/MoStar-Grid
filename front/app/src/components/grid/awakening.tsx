import { useEffect, useMemo, useRef, useState } from "react";
import rawOrbSvg from "./loadord.svg?raw";
import sunVideoSrc from "@/assets/sun5.mp4?url";

export type RollCallState = "idle" | "awakening" | "ready";

// ── 8 Boot stages — one per orb node ────────────────────────────────────────
const BOOT_STAGES = [
  { label: "GRID CORE",        voice: "Grid Core initializing. The sovereign foundation rises.",      color: "#f6c453" },
  { label: "THE COUNCIL",      voice: "Council of Eleven assembling.",                                color: "#ff5a2e" },
  { label: "MINDGRAPH",        voice: "MindGraph connecting. Knowledge roots deepening.",             color: "#00d8ff" },
  { label: "SANCTUARY",        voice: "Sanctuary sealing. Sacred archives protected.",                color: "#b46cff" },
  { label: "CODE CONDUIT",     voice: "Code Conduit secured.",                                        color: "#00ff88" },
  { label: "WOO ACTIVATION",   voice: "Woo Activation online. The oracle listens.",                  color: "#168bff" },
  { label: "DCX TRINITY",      voice: "DCX Trinity awakening. Intelligence layers rising.",           color: "#ff3b6b" },
  { label: "MOSCRIPTS ENGINE", voice: "MoScripts Engine online. Grid boot complete.",                 color: "#9be15d" },
];

// SVG ellipse centers for the 8 nodes — clockwise from top
const NODES = BOOT_STAGES.map((s, i) => ({
  color: s.color,
  cx: ["195.722","316.995","358.52","316.066","198.309","79.0684","34.5241","70.0168"][i],
  cy: ["35.3291","92.7552","203.56","318.762","370.321","319.885","205.095","97.9253"][i],
}));

// Tag each node's ellipses with data-node / data-layer for live CSS theming
const TAGGED_SVG = (() => {
  let svg = rawOrbSvg;
  NODES.forEach((n, i) => {
    let layer = 0;
    const re = new RegExp(`<ellipse cx="${n.cx}" cy="${n.cy}"([^/]*?)/>`, "g");
    svg = svg.replace(re, (_m, attrs) => {
      const tag = `<ellipse cx="${n.cx}" cy="${n.cy}"${attrs} data-node="${i}" data-layer="${layer}"/>`;
      layer++;
      return tag;
    });
  });
  return svg;
})();

// ── Circular boot ring — 8 nodes, arc progress ──────────────────────────────
function BootRing({ activeStep, state }: { activeStep: number; state: RollCallState }) {
  const size = 780;
  const cx = size / 2;   // 390
  const cy = size / 2;   // 390
  const r  = 310;
  const circ = 2 * Math.PI * r;
  const n = BOOT_STAGES.length;
  const filled = state === "ready" ? n : activeStep;

  const dots = BOOT_STAGES.map((stage, i) => {
    const angle = -Math.PI / 2 + (i / n) * 2 * Math.PI;
    const dotX  = cx + r * Math.cos(angle);
    const dotY  = cy + r * Math.sin(angle);
    // Label sits 30px further out from center
    const lR    = r + 30;
    const lx    = cx + lR * Math.cos(angle);
    const ly    = cy + lR * Math.sin(angle);
    const anchor = Math.cos(angle) > 0.25 ? "start" : Math.cos(angle) < -0.25 ? "end" : "middle";
    const reached = i < activeStep || state === "ready";
    const active  = i === activeStep && state === "awakening";
    return { dotX, dotY, lx, ly, anchor, reached, active, color: stage.color, label: stage.label };
  });

  return (
    <svg
      width={size} height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="pointer-events-none absolute z-[6]"
      style={{ top: "50%", left: "50%", transform: "translate(-50%, -50%)" }}
    >
      <defs>
        {/* Arc gradient — gold at start, cyan at finish */}
        <linearGradient id="arc-grad" gradientUnits="userSpaceOnUse"
          x1={cx} y1={cy - r} x2={cx} y2={cy + r}>
          <stop offset="0%"   stopColor="#f6c453" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#00d8ff" stopOpacity="0.95" />
        </linearGradient>
        {/* Soft glow for the progress arc */}
        <filter id="arc-glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        {/* Glow for active dot */}
        <filter id="dot-glow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Faint track */}
      <circle cx={cx} cy={cy} r={r}
        fill="none" stroke="rgba(255,255,255,0.055)" strokeWidth={1} />

      {/* Progress arc — fills clockwise, 1/8 per stage */}
      <circle cx={cx} cy={cy} r={r}
        fill="none"
        stroke="url(#arc-grad)"
        strokeWidth={1.5}
        strokeDasharray={circ}
        strokeDashoffset={circ * (1 - filled / n)}
        strokeLinecap="butt"
        transform={`rotate(-90, ${cx}, ${cy})`}
        filter="url(#arc-glow)"
        style={{ transition: "stroke-dashoffset 0.9s cubic-bezier(0.4,0,0.2,1)" }}
      />

      {/* Stage dots */}
      {dots.map((d, i) => (
        <g key={i}>
          {/* Outer ring pulse on active dot */}
          {d.active && (
            <circle cx={d.dotX} cy={d.dotY} r={14}
              fill="none" stroke={d.color} strokeWidth={1} opacity={0.4}
            />
          )}

          {/* Inner tick circle */}
          <circle cx={d.dotX} cy={d.dotY}
            r={d.active ? 9 : d.reached ? 8 : 6}
            fill="none"
            stroke={d.reached || d.active ? d.color : "rgba(255,255,255,0.08)"}
            strokeWidth={d.active ? 1.5 : 1}
            style={{ transition: "all 0.45s ease" }}
          />

          {/* Filled center dot */}
          <circle cx={d.dotX} cy={d.dotY}
            r={d.active ? 5 : d.reached ? 4 : 2.5}
            fill={d.reached || d.active ? d.color : "rgba(255,255,255,0.1)"}
            filter={d.active ? "url(#dot-glow)" : undefined}
            style={{ transition: "all 0.45s ease" }}
          />

          {/* Label — appears only when reached or active */}
          {(d.reached || d.active) && (
            <text
              x={d.lx}
              y={d.ly + 4}
              textAnchor={d.anchor}
              fill={d.color}
              fontSize={7.5}
              fontFamily="'Courier New', monospace"
              letterSpacing="0.14em"
              opacity={d.active ? 1 : 0.6}
              style={{ transition: "opacity 0.4s ease" }}
            >
              {d.label}
            </text>
          )}
        </g>
      ))}
    </svg>
  );
}

// ── Orb — static, centered, no glow ─────────────────────────────────────────
export function AwakeningOrb({
  state,
  progress,
  activeStep = 0,
}: {
  state: RollCallState;
  progress: number;
  activeStep?: number;
}) {
  // Per-node CSS: lights up reached/active nodes in their color
  const nodeStyle = useMemo(() => {
    const rules: string[] = [];
    NODES.forEach((n, i) => {
      const reached = i < activeStep || state === "ready";
      const active  = i === activeStep && state === "awakening";
      if (!reached && !active) return;
      const c = n.color;
      rules.push(`.orb-svg [data-node="${i}"][data-layer="0"]{fill:${c};fill-opacity:${active ? 0.55 : 0.35};}`);
      rules.push(`.orb-svg [data-node="${i}"][data-layer="1"]{fill:${c};fill-opacity:${active ? 0.85 : 0.55};}`);
      rules.push(
        `.orb-svg [data-node="${i}"][data-layer="2"]{stroke:${c};stroke-width:${active ? 2.5 : 1.5};` +
        (active ? "animation:node-pulse 1.1s ease-out infinite;" : "") + `}`,
      );
    });
    return rules.join("\n");
  }, [activeStep, state]);

  return (
    <div className="pointer-events-none absolute inset-0 z-[4] grid place-items-center">
      <style>{`
        @keyframes node-pulse {
          0%,100% { transform: scale(1); }
          50%      { transform: scale(1.12); }
        }
        .orb-svg svg { overflow: visible; }
        .orb-svg ellipse[data-node] {
          transform-box: fill-box;
          transform-origin: center;
          transition: fill 350ms ease, stroke 350ms ease, fill-opacity 350ms ease;
        }
        ${nodeStyle}
      `}</style>

      <div
        className="relative h-[520px] w-[520px] transition-all duration-700"
        style={{
          transform: state === "awakening" ? `scale(${1 + progress / 250})` : "scale(1)",
        }}
      >
        {/* Raw SVG — no filter, no drop-shadow */}
        <div className="orb-svg h-full w-full" dangerouslySetInnerHTML={{ __html: TAGGED_SVG }} />

        {/* Center state label */}
        <div
          className="absolute left-1/2 top-[72%] -translate-x-1/2 font-mono text-[10px] tracking-[0.44em]"
          style={{ color: "rgba(246,196,83,0.55)", pointerEvents: "none" }}
        >
          {state === "ready" ? "GRID ONLINE" : state === "awakening" ? `${progress}%` : "SEALED"}
        </div>
      </div>
    </div>
  );
}

// ── Voice helper ─────────────────────────────────────────────────────────────
async function speak(text: string) {
  try {
    const res = await fetch("/api/voice/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, mood: "ceremonial" }),
    });
    if (!res.ok) return;
    const { audio_url } = await res.json();
    const src = audio_url.startsWith("/audio/") ? `/api/voice${audio_url}` : audio_url;
    new Audio(src).play().catch(() => {});
  } catch { /* voice failure is never blocking */ }
}

// ── Awakening screen ─────────────────────────────────────────────────────────
export function AwakeningScreen({
  onComplete,
  stepDuration = 2500,
}: {
  onComplete?: () => void;
  stepDuration?: number;
}) {
  const [state, setState]         = useState<RollCallState>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress]   = useState(0);
  const spokenRef = useRef<Set<number>>(new Set());

  // Begin awakening after a short hold
  useEffect(() => {
    const t = window.setTimeout(() => setState("awakening"), 600);
    return () => window.clearTimeout(t);
  }, []);

  // Tick through 8 stages
  useEffect(() => {
    if (state !== "awakening") return;
    const total    = BOOT_STAGES.length;
    const totalDur = stepDuration * total;
    const start    = performance.now();
    let raf = 0;

    const tick = (now: number) => {
      const elapsed = now - start;
      const pct  = Math.min(100, Math.round((elapsed / totalDur) * 100));
      const step = Math.min(total, Math.floor(elapsed / stepDuration));
      setProgress(pct);
      setActiveStep(step < total ? step : total);
      if (elapsed < totalDur) {
        raf = requestAnimationFrame(tick);
      } else {
        setState("ready");
        window.setTimeout(() => onComplete?.(), 900);
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [state, stepDuration, onComplete]);

  // Speak each stage when it becomes active
  useEffect(() => {
    if (state !== "awakening") return;
    if (activeStep >= BOOT_STAGES.length) return;
    if (spokenRef.current.has(activeStep)) return;
    spokenRef.current.add(activeStep);
    speak(BOOT_STAGES[activeStep].voice);
  }, [activeStep, state]);

  const currentStage = activeStep < BOOT_STAGES.length ? BOOT_STAGES[activeStep] : null;

  return (
    <div className="fixed inset-0 z-[100] overflow-hidden" style={{ background: "#050608" }}>
      {/* Sun video — full bleed background */}
      <video
        src={sunVideoSrc}
        autoPlay muted loop playsInline
        className="absolute inset-0 h-full w-full object-cover"
        style={{ opacity: 0.52 }}
      />

      {/* Vignette — keeps orb readable */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(68% 62% at 50% 50%, transparent 0%, rgba(5,6,8,0.68) 72%, rgba(5,6,8,0.96) 100%)",
        }}
      />

      {/* Title — top */}
      <div className="absolute inset-x-0 top-10 z-[5] flex flex-col items-center gap-2 pointer-events-none">
        <div className="text-[10px] tracking-[0.52em]" style={{ color: "#00d8ff" }}>
          MOSTAR · SOVEREIGN BOOT SEQUENCE
        </div>
        <div
          className="text-2xl tracking-[0.4em] font-mono"
          style={{ color: "#f6c453", textShadow: "0 0 20px rgba(246,196,83,0.4)" }}
        >
          GRID AWAKENING
        </div>
      </div>

      {/* Orb — dead center */}
      <AwakeningOrb state={state} progress={progress} activeStep={activeStep} />

      {/* Boot ring — concentric with orb, slightly larger */}
      <BootRing activeStep={activeStep} state={state} />

      {/* Current stage label — below orb */}
      <div
        className="absolute inset-x-0 bottom-20 z-[7] flex flex-col items-center gap-1 pointer-events-none"
        style={{ minHeight: "2rem" }}
      >
        {state === "awakening" && currentStage && (
          <>
            <div className="font-mono text-[9px] tracking-[0.45em]" style={{ color: "rgba(255,255,255,0.3)" }}>
              NOW LOADING
            </div>
            <div
              className="font-mono text-[13px] tracking-[0.3em]"
              style={{
                color: currentStage.color,
                textShadow: `0 0 14px ${currentStage.color}66`,
              }}
            >
              {currentStage.label}
            </div>
          </>
        )}
        {state === "ready" && (
          <div
            className="font-mono text-[13px] tracking-[0.3em]"
            style={{ color: "#00d8ff", textShadow: "0 0 14px rgba(0,216,255,0.5)" }}
          >
            GRID ONLINE
          </div>
        )}
      </div>

      {/* Motto — bottom */}
      <div
        className="absolute inset-x-0 bottom-6 z-[5] text-center font-mono text-[9px] tracking-[0.42em] pointer-events-none"
        style={{ color: "rgba(255,255,255,0.18)" }}
      >
        HONOR FIRST · STRIKE FAST · SEE AHEAD · STAY UNTOUCHABLE
      </div>
    </div>
  );
}
