import { useEffect, useState } from "react";

// Four sacred elements drive the animation. Ornamental glyphs fade in behind.
const ELEMENTS = [
  { g: "🜂", name: "ikang", color: "224 100% 60%", weight: 6 },   // Fire — blue flame
  { g: "🜄", name: "mmong", color: "200 100% 70%", weight: 5 },   // Water
  { g: "🜁", name: "afim", color: "0 0% 100%", weight: 5 },       // Air — white
  { g: "🜃", name: "isong", color: "52 100% 60%", weight: 6 },    // Earth — yellow
];
const ORNAMENTS = ["⬡", "✦", "◈", "⚡", "ꔀ", "ꔁ", "ꔂ", "ꔃ", "ꔄ", "ꔅ", "ꔆ", "ꔇ"];

// Weighted pool — elements appear ~70% of the time.
const POOL: { g: string; color?: string; element?: boolean }[] = [
  ...ELEMENTS.flatMap((e) => Array(e.weight).fill({ g: e.g, color: e.color, element: true })),
  ...ORNAMENTS.map((g) => ({ g, element: false as const })),
];

type Particle = {
  id: number;
  x: number;
  y: number;
  glyph: string;
  color?: string;
  element: boolean;
  size: number;
  speed: number;
  opacity: number;
  drift: number;
  spin: number;
  phase: number;
};

const pick = () => POOL[Math.floor(Math.random() * POOL.length)];

const GlyphCanvas = () => {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    const initial: Particle[] = Array.from({ length: 60 }, (_, i) => {
      const p = pick();
      return {
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        glyph: p.g,
        color: p.color,
        element: p.element,
        size: p.element ? 28 + Math.random() * 48 : 18 + Math.random() * 26,
        speed: 0.2 + Math.random() * 0.5,
        opacity: p.element ? 0.25 + Math.random() * 0.35 : 0.08 + Math.random() * 0.18,
        drift: (Math.random() - 0.5) * 0.25,
        spin: (Math.random() - 0.5) * 0.6,
        phase: Math.random() * Math.PI * 2,
      };
    });
    setParticles(initial);
  }, []);

  useEffect(() => {
    let raf: number;
    const tick = () => {
      setParticles((prev) =>
        prev.map((p) => {
          const ny = p.y + p.speed;
          if (ny > 105) {
            const np = pick();
            return {
              ...p,
              y: -8,
              x: Math.random() * 100,
              glyph: np.g,
              color: np.color,
              element: np.element,
              opacity: np.element ? 0.25 + Math.random() * 0.35 : 0.08 + Math.random() * 0.18,
            };
          }
          return { ...p, y: ny, x: p.x + p.drift, phase: p.phase + 0.04 };
        })
      );
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden bg-gradient-bg">
      {/* Resonance grid */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, hsl(var(--primary) / 0.4) 1px, transparent 1px),
                            radial-gradient(circle at 75% 75%, hsl(var(--secondary) / 0.35) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />

      {particles.map((p) => {
        const pulse = p.element ? 0.7 + Math.sin(p.phase) * 0.3 : 1;
        const color = p.color ? `hsl(${p.color})` : "hsl(var(--muted-foreground))";
        return (
          <div
            key={p.id}
            className="absolute font-mono pointer-events-none select-none"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              fontSize: `${p.size}px`,
              opacity: p.opacity * pulse,
              color,
              textShadow: p.element
                ? `0 0 ${20 + pulse * 24}px ${p.color ? `hsl(${p.color} / 0.7)` : "transparent"}`
                : "none",
              transform: `rotate(${p.y * p.spin}deg)`,
              transition: "opacity 400ms linear",
            }}
          >
            {p.glyph}
          </div>
        );
      })}

      {/* Vignette */}
      <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-r from-background/70 via-transparent to-transparent" />

      {/* Federation rings */}
      <div className="absolute bottom-20 right-20 w-72 h-72 border border-primary/15 rounded-full animate-pulse opacity-40" />
      <div className="absolute bottom-24 right-24 w-60 h-60 border border-secondary/15 rounded-full" />
      <div className="absolute bottom-28 right-28 w-48 h-48 border border-foreground/5 rounded-full" />
    </div>
  );
};

export default GlyphCanvas;
