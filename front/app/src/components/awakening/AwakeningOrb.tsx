import { Glyph, type GlyphName } from "@/components/grid/glyph";

type RollCallState = "idle" | "awakening" | "ready";

const AWAKENING_STEPS: Array<{ label: string; glyph: GlyphName }> = [
  { label: "CORE", glyph: "grid" },
  { label: "VOICE", glyph: "utterances" },
  { label: "MIND", glyph: "mind" },
  { label: "COUNCIL", glyph: "council" },
  { label: "MEMORY", glyph: "memory" },
  { label: "GATE", glyph: "seal" },
  { label: "SIGNAL", glyph: "eyelight" },
  { label: "READY", glyph: "covenant" },
];

const SVG_SIZE = 600;
const C = SVG_SIZE / 2;
const NODE_R = 195;

export function AwakeningOrb({
  state,
  progress = 0,
  activeStep = -1,
}: {
  state: RollCallState;
  progress?: number;
  activeStep?: number;
}) {
  const total = AWAKENING_STEPS.length;

  const glowColor = state === "ready" ? "#00d8ff" : state === "awakening" ? "#f6c453" : "#c28a17";

  const nodes = AWAKENING_STEPS.map((step, i) => {
    const angle = (i / total) * Math.PI * 2 - Math.PI / 2;
    return {
      ...step,
      x: C + Math.cos(angle) * NODE_R,
      y: C + Math.sin(angle) * NODE_R,
    };
  });

  return (
    <div
      className="pointer-events-none absolute z-[3]"
      style={{
        top: 0,
        left: 0,
        right: 0,
        bottom: 180,
        display: "grid",
        placeItems: "center",
      }}
    >
      <div className="relative" style={{ width: SVG_SIZE, height: SVG_SIZE }}>
        <svg className="absolute inset-0" width={SVG_SIZE} height={SVG_SIZE}>
          <defs>
            <filter id="gold-glow" x="-80%" y="-80%" width="260%" height="260%">
              <feGaussianBlur stdDeviation="7" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <circle
            cx={C}
            cy={C}
            r={NODE_R}
            fill="none"
            stroke="rgba(246,196,83,0.28)"
            strokeWidth="2"
          />

          <circle
            cx={C}
            cy={C}
            r={NODE_R - 40}
            fill="none"
            stroke="rgba(246,196,83,0.10)"
            strokeWidth="1"
          />

          {AWAKENING_STEPS.map((_, i) => {
            const from = nodes[i];
            const to = nodes[(i + 1) % total];
            const lit = i < activeStep || state === "ready";
            const active = i === activeStep && state === "awakening";

            return (
              <path
                key={i}
                d={`M ${from.x} ${from.y} A ${NODE_R} ${NODE_R} 0 0 1 ${to.x} ${to.y}`}
                fill="none"
                stroke={lit || active ? "#f6c453" : "rgba(255,255,255,0.07)"}
                strokeWidth={lit ? 3 : active ? 2 : 1}
                filter={lit || active ? "url(#gold-glow)" : undefined}
                opacity={lit ? 0.85 : active ? 0.65 : 0.55}
              />
            );
          })}

          {nodes.map((node, i) => {
            const lit = i < activeStep || state === "ready";
            const active = i === activeStep && state === "awakening";

            return (
              <circle
                key={node.label}
                cx={node.x}
                cy={node.y}
                r={lit || active ? 7 : 4}
                fill={lit ? "#21ff64" : active ? "#f6c453" : "rgba(255,255,255,0.18)"}
                filter={lit || active ? "url(#gold-glow)" : undefined}
              />
            );
          })}
        </svg>

        <div
          className="absolute rounded-full transition-all duration-700"
          style={{
            width: 240,
            height: 240,
            left: C - 120,
            top: C - 120,
            background: "linear-gradient(145deg, rgba(8,9,10,0.96), rgba(0,0,0,1))",
            border: `1px solid ${glowColor}88`,
            boxShadow: `
              0 0 ${70 + progress}px ${glowColor}66,
              0 0 ${150 + progress}px ${glowColor}22,
              inset 0 0 70px rgba(0,0,0,0.96),
              inset 0 0 32px ${glowColor}22,
              32px 32px 75px rgba(0,0,0,0.88),
              -18px -18px 55px rgba(246,196,83,0.05)
            `,
          }}
        >
          <div
            className="absolute rounded-full"
            style={{
              inset: 16,
              border: `1px solid ${glowColor}77`,
              boxShadow: `0 0 30px ${glowColor}55, inset 0 0 18px ${glowColor}22`,
              animation: "spin-slow 90s linear infinite",
            }}
          />

          <div
            className="absolute rounded-full"
            style={{
              inset: 42,
              border: `1px solid ${glowColor}aa`,
              boxShadow: `0 0 36px ${glowColor}77, inset 0 0 20px ${glowColor}33`,
              animation: "spin-reverse 70s linear infinite",
            }}
          />

          <div
            className="absolute rounded-full"
            style={{
              inset: 90,
              border: `4px solid ${glowColor}cc`,
              boxShadow: `0 0 42px ${glowColor}99, inset 0 0 22px ${glowColor}44`,
            }}
          />

          <div className="absolute inset-0 flex items-center justify-center">
            <Glyph
              name="covenant"
              size={96}
              glow={glowColor}
              className={state === "awakening" ? "animate-pulse" : ""}
            />
          </div>
        </div>

        {nodes.map((node, i) => {
          const done = i < activeStep || state === "ready";
          const active = i === activeStep && state === "awakening";
          const lit = done || active;

          return (
            <div
              key={node.label}
              className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-2"
              style={{ left: node.x, top: node.y }}
            >
              <div
                className="flex items-center justify-center rounded-full transition-all duration-500"
                style={{
                  width: 84,
                  height: 84,
                  border: lit
                    ? "1px solid rgba(246,196,83,0.95)"
                    : "1px solid rgba(255,255,255,0.18)",
                  background: "linear-gradient(145deg, rgba(6,12,22,0.92), rgba(0,0,0,0.96))",
                  boxShadow: lit
                    ? "0 0 34px rgba(246,196,83,0.85), inset 0 0 20px rgba(246,196,83,0.18)"
                    : "inset 0 0 16px rgba(255,255,255,0.05)",
                  opacity: lit ? 1 : 0.55,
                }}
              >
                <Glyph
                  name={node.glyph}
                  size={48}
                  glow={lit ? "#f6c453" : undefined}
                  className={active ? "animate-pulse" : ""}
                />
              </div>

              <span
                className="font-mono text-[11px] tracking-[0.22em] uppercase"
                style={{
                  color: lit ? "#f6c453" : "rgba(255,255,255,0.34)",
                  textShadow: lit ? "0 0 10px rgba(246,196,83,0.6)" : "none",
                }}
              >
                {node.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
