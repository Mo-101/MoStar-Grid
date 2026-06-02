import { useEffect, useState } from "react";

// All glyphs in the background pool
// hueShift rotates the base blue glyphs to varied elemental colors
// Gold/white glyphs use hueShift: 0 and their natural shadow
const GLYPHS = [
  // ── Four alchemical element glyphs ─────────────────────────────────────────
  { src: "f3.png",                           hueShift: 150,  shadow: "25 100% 55%",   weight: 7 },  // 🜂 Fire  — orange
  { src: "glo3t.png",                        hueShift: 0,    shadow: "210 90% 55%",   weight: 7 },  // 🜄 Water — blue
  { src: "gff1.png",                         hueShift: -30,  shadow: "185 80% 50%",   weight: 7 },  // 🜁 Air   — teal
  { src: "glot.png",                         hueShift: -90,  shadow: "140 65% 45%",   weight: 7 },  // 🜃 Earth — green

  // ── New sovereign glyphs ────────────────────────────────────────────────────
  { src: "ms__18_-removebg-preview.png",     hueShift: 0,    shadow: "45 95% 55%",    weight: 5 },  // ☀ Sun wheel      — gold (natural)
  { src: "ms__41_-removebg-preview.png",     hueShift: 0,    shadow: "45 90% 50%",    weight: 5 },  // ♀ Mercury        — gold (natural)
  { src: "ms__33_-removebg-preview.png",     hueShift: 0,    shadow: "45 95% 55%",    weight: 4 },  // ⚯ Trinity knot   — gold (natural)
  { src: "ms__19_-removebg-preview.png",     hueShift: 150,  shadow: "25 100% 55%",   weight: 4 },  // ✦ Star sparkle   — orange tint
  { src: "ms__34_-removebg-preview.png",     hueShift: -30,  shadow: "185 80% 50%",   weight: 4 },  // ⊙ Alch circle    — teal tint
  { src: "ms__14_-removebg-preview.png",     hueShift: 270,  shadow: "270 75% 60%",   weight: 3 },  // ⊕ Crosshair      — violet tint
  { src: "ms__16_-removebg-preview.png",     hueShift: -60,  shadow: "160 70% 45%",   weight: 3 },  // ⚡ Zigzag         — green tint
  { src: "ms__35_-removebg-preview.png",     hueShift: 0,    shadow: "0 0% 85%",      weight: 2 },  // ⊙ Alch spiral    — white (natural)
];

type Entry = { src: string; hueShift: number; shadow: string };

const POOL: Entry[] = GLYPHS.flatMap((g) =>
  Array(g.weight).fill({ src: g.src, hueShift: g.hueShift, shadow: g.shadow })
);

type Particle = {
  id: number;
  x: number;
  y: number;
  src: string;
  hueShift: number;
  shadow: string;
  size: number;
  speed: number;
  opacity: number;
  drift: number;
  spin: number;
  phase: number;
};

const pick = (): Entry => POOL[Math.floor(Math.random() * POOL.length)];

const GlyphCanvas = () => {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    const initial: Particle[] = Array.from({ length: 60 }, (_, i) => {
      const p = pick();
      return {
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        src: p.src,
        hueShift: p.hueShift,
        shadow: p.shadow,
        size: 32 + Math.random() * 52,
        speed: 0.12 + Math.random() * 0.35,
        opacity: 0.18 + Math.random() * 0.3,
        drift: (Math.random() - 0.5) * 0.18,
        spin: (Math.random() - 0.5) * 0.4,
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
          if (ny > 108) {
            const np = pick();
            return {
              ...p,
              y: -8,
              x: Math.random() * 100,
              src: np.src,
              hueShift: np.hueShift,
              shadow: np.shadow,
              opacity: 0.18 + Math.random() * 0.3,
            };
          }
          return { ...p, y: ny, x: p.x + p.drift, phase: p.phase + 0.03 };
        })
      );
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden bg-gradient-bg">
      {/* Resonance dot grid */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `radial-gradient(circle at 25% 25%, hsl(var(--primary) / 0.4) 1px, transparent 1px),
                            radial-gradient(circle at 75% 75%, hsl(var(--secondary) / 0.35) 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
        }}
      />

      {particles.map((p) => {
        const pulse = 0.7 + Math.sin(p.phase) * 0.3;
        const filter = [
          `hue-rotate(${p.hueShift}deg)`,
          "saturate(1.7)",
          "brightness(1.05)",
          `drop-shadow(0 0 ${10 + pulse * 14}px hsl(${p.shadow} / 0.65))`,
        ].join(" ");

        return (
          <div
            key={p.id}
            className="absolute pointer-events-none select-none"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              opacity: p.opacity * pulse,
              filter,
              transform: `rotate(${p.y * p.spin}deg)`,
              transition: "opacity 300ms linear",
            }}
          >
            <img
              src={`/moCons/${p.src}`}
              alt=""
              draggable={false}
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
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
