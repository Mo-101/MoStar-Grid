import { useEffect, useMemo, useState } from "react";
import rawOrbSvg from "./loadord.svg?raw";
import sunVideo from "@/assets/sun5.mp4.asset.json";

export type RollCallState = "idle" | "awakening" | "ready";

/* 8 nodes, clockwise from top, matched to the SVG ellipse centers. */
const NODES: { cx: string; cy: string; label: string; color: string }[] = [
  { cx: "195.722", cy: "35.3291", label: "COVENANT CORE",        color: "#f6c453" }, // gold
  { cx: "316.995", cy: "92.7552", label: "COUNCIL OF ELEVEN",    color: "#ff5a2e" }, // ember
  { cx: "358.52",  cy: "203.56",  label: "NEO4J SOULPRINT",      color: "#00d8ff" }, // cyan
  { cx: "316.066", cy: "318.762", label: "ELEMENTAL QUADRANTS",  color: "#b46cff" }, // violet
  { cx: "198.309", cy: "370.321", label: "CODE CONDUIT",         color: "#00ff88" }, // green
  { cx: "79.0684", cy: "319.885", label: "WOO ORACLE",           color: "#168bff" }, // blue
  { cx: "34.5241", cy: "205.095", label: "DCX TRINITY",          color: "#ff3b6b" }, // red
  { cx: "70.0168", cy: "97.9253", label: "GRID PERIMETER",       color: "#9be15d" }, // lime
];

/* Inject data-node / data-layer attributes onto each node's 3 ellipses
   so we can theme them individually with CSS variables. */
const TAGGED_SVG = (() => {
  let svg = rawOrbSvg;
  NODES.forEach((n, i) => {
    let layer = 0;
    const re = new RegExp(
      `<ellipse cx="${n.cx}" cy="${n.cy}"([^/]*?)/>`,
      "g",
    );
    svg = svg.replace(re, (_m, attrs) => {
      const tag = `<ellipse cx="${n.cx}" cy="${n.cy}"${attrs} data-node="${i}" data-layer="${layer}"/>`;
      layer++;
      return tag;
    });
  });
  return svg;
})();

export function AwakeningOrb({
  state,
  progress,
  activeStep = 0,
}: {
  state: RollCallState;
  progress: number;
  activeStep?: number;
}) {
  const glow =
    state === "ready" ? "#00d8ff" : state === "awakening" ? "#f6c453" : "#8a5f14";

  /* Per-node CSS that lights up reached / active nodes in their color. */
  const nodeStyle = useMemo(() => {
    const rules: string[] = [];
    NODES.forEach((n, i) => {
      const reached = i < activeStep || state === "ready";
      const active = i === activeStep && state === "awakening";
      if (!reached && !active) return;
      const c = n.color;
      // layer 0 = base fill (the darker plate)
      rules.push(`.orb-svg [data-node="${i}"][data-layer="0"]{fill:${c};fill-opacity:${active ? 0.55 : 0.35};}`);
      // layer 1 = radial gradient overlay — force a hot fill
      rules.push(`.orb-svg [data-node="${i}"][data-layer="1"]{fill:${c};fill-opacity:${active ? 0.85 : 0.55};}`);
      // layer 2 = stroke ring
      rules.push(
        `.orb-svg [data-node="${i}"][data-layer="2"]{stroke:${c};stroke-width:${active ? 2.5 : 1.5};filter:drop-shadow(0 0 ${active ? 14 : 6}px ${c});${active ? "animation:node-pulse 1.1s ease-out infinite;" : ""}}`,
      );
    });
    return rules.join("\n");
  }, [activeStep, state]);

  return (
    <div className="pointer-events-none absolute inset-x-0 top-0 bottom-40 z-[4] grid place-items-center">
      <style>{`
        @keyframes node-pulse {
          0%,100% { transform: scale(1); }
          50% { transform: scale(1.12); }
        }
        .orb-svg svg { overflow: visible; }
        .orb-svg ellipse[data-node] { transform-box: fill-box; transform-origin: center; transition: fill 300ms ease, stroke 300ms ease, fill-opacity 300ms ease; }
        ${nodeStyle}
      `}</style>

      <div
        className="relative h-[520px] w-[520px] transition-all duration-700"
        style={{
          transform:
            state === "awakening" ? `scale(${1 + progress / 2200})` : "scale(1)",
        }}
      >
        {/* Counter-rotating ambient halo */}
        <div
          className="absolute inset-[-40px] rounded-full opacity-60 animate-spin-reverse"
          style={{
            background:
              "conic-gradient(from 0deg, transparent 0deg, rgba(246,196,83,0.18) 60deg, transparent 120deg, rgba(0,216,255,0.22) 220deg, transparent 300deg)",
            filter: "blur(18px)",
          }}
        />

        {/* Inline SVG so node ellipses can be themed live */}
        <div
          className="orb-svg relative h-full w-full animate-spin-slow"
          style={{
            filter:
              state === "ready"
                ? "drop-shadow(0 0 40px #00d8ff)"
                : "drop-shadow(0 0 28px rgba(246,196,83,0.55))",
          }}
          dangerouslySetInnerHTML={{ __html: TAGGED_SVG }}
        />

        <div
          className="absolute left-1/2 top-[72%] -translate-x-1/2 font-mono text-[11px] tracking-[0.42em]"
          style={{ color: glow, textShadow: `0 0 12px ${glow}` }}
        >
          {state === "ready"
            ? "GRID ONLINE"
            : state === "awakening"
              ? `${progress}%`
              : "SEALED"}
        </div>
      </div>
    </div>
  );
}

export function AwakeningScreen({
  onComplete,
  stepDuration = 750,
}: {
  onComplete?: () => void;
  stepDuration?: number;
}) {
  const [state, setState] = useState<RollCallState>("idle");
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const t = window.setTimeout(() => setState("awakening"), 400);
    return () => window.clearTimeout(t);
  }, []);

  useEffect(() => {
    if (state !== "awakening") return;
    const total = NODES.length;
    const start = performance.now();
    const totalDur = stepDuration * total;
    let raf = 0;
    const tick = (now: number) => {
      const elapsed = now - start;
      const pct = Math.min(100, Math.round((elapsed / totalDur) * 100));
      const step = Math.min(total, Math.floor(elapsed / stepDuration));
      setProgress(pct);
      setActiveStep(step);
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

  return (
    <div className="fixed inset-0 z-[100] overflow-hidden bg-background">
      {/* Living background — video loads as the system loads */}
      <video
        src={sunVideo.url}
        autoPlay
        muted
        loop
        playsInline
        className="absolute inset-0 h-full w-full object-cover opacity-60"
      />
      {/* Dim vignette to keep the orb legible over the video */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 55% at 50% 50%, transparent 0%, oklch(0.10 0.04 270 / 0.65) 70%, oklch(0.08 0.04 270 / 0.92) 100%)",
        }}
      />

      {/* Title */}
      <div className="absolute inset-x-0 top-10 z-[5] flex flex-col items-center gap-2">
        <div className="text-[10px] tracking-[0.5em] text-[var(--color-neon-cyan)]">
          MOSTAR · COVENANT BOOT SEQUENCE
        </div>
        <div className="text-2xl tracking-[0.4em] neon-text-gold">
          GRID AWAKENING
        </div>
      </div>

      <AwakeningOrb state={state} progress={progress} activeStep={activeStep} />

      {/* Step log + progress */}
      <div className="absolute inset-x-0 bottom-12 z-[5] mx-auto flex max-w-[640px] flex-col items-center gap-3 px-6">
        <div className="h-[3px] w-full overflow-hidden rounded-full border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.10_0.05_270/0.7)]">
          <div
            className="h-full rounded-full transition-[width] duration-150"
            style={{
              width: `${progress}%`,
              background:
                "linear-gradient(90deg, var(--color-neon-cyan), var(--color-neon-gold))",
              boxShadow: "0 0 18px var(--color-neon-gold)",
            }}
          />
        </div>
        <div className="flex w-full flex-col gap-1 font-mono text-[11px]">
          {NODES.map((n, i) => {
            const done = i < activeStep || state === "ready";
            const active = i === activeStep && state === "awakening";
            if (!done && !active) return null;
            return (
              <div key={n.label} className="flex items-center gap-3 animate-fade-in">
                <span
                  style={{ color: n.color, textShadow: `0 0 8px ${n.color}` }}
                  className={active ? "animate-blink" : ""}
                >
                  {done ? "●" : "◐"}
                </span>
                <span style={{ color: done ? "rgba(219,232,246,0.85)" : n.color }}>
                  LINK · {n.label}
                </span>
                <span className="ml-auto text-muted-foreground tracking-[0.2em]">
                  {done ? "SEALED" : "BINDING…"}
                </span>
              </div>
            );
          })}
        </div>
        <div className="text-[10px] tracking-[0.4em] text-muted-foreground">
          HONOR FIRST · STRIKE FAST · SEE AHEAD · STAY UNTOUCHABLE
        </div>
      </div>
    </div>
  );
}
