import { useEffect, useState } from "react";
import { Brain, Database, Hexagon, Shield, Sparkles, Star } from "lucide-react";
import { MoCon, ELEMENT_ICON, type IconKey } from "@/components/MoCon";


type Props = { progress: number; status?: string; voice?: string; activeGlyph?: string };

const GATES_LEFT = [
  { icon: Brain, label: "SOUL GATE" },
  { icon: Sparkles, label: "SIGNAL" },
  { icon: Database, label: "MEMORY" },
];
const GATES_RIGHT = [
  { icon: Hexagon, label: "MIND GATE" },
  { icon: Star, label: "PATTERN" },
  { icon: Shield, label: "BODY GATE" },
];

const BARS = [
  { icon: Star, label: "SOUL GATE AUTHENTICATION", target: 100 },
  { icon: Brain, label: "ENGINE CALIBRATION", target: 68 },
  { icon: Hexagon, label: "SIGNAL INTAKE", target: 100 },
  { icon: Shield, label: "BODY GATE VERIFICATION", target: 42 },
  { icon: Sparkles, label: "PATTERN SYNTHESIS", target: 84 },
  { icon: Star, label: "COVENANT SEAL", target: 18 },
];

const Corner = ({ className }: { className: string }) => (
  <svg viewBox="0 0 80 80" className={`absolute w-16 h-16 ${className}`} fill="none">
    <path d="M2 30 L2 2 L30 2" stroke="hsl(var(--secondary))" strokeWidth="1.5" />
    <path d="M10 45 L10 10 L45 10" stroke="hsl(var(--primary))" strokeWidth="1" opacity="0.6" />
    <circle cx="10" cy="10" r="2" fill="hsl(var(--secondary))" />
    <path d="M20 4 L28 4 M4 20 L4 28" stroke="hsl(var(--secondary))" strokeWidth="1" opacity="0.5" />
  </svg>
);

const LoadingHUD = ({ progress, status, voice, activeGlyph }: Props) => {
  const [dots, setDots] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setDots((d) => (d + 1) % 4), 400);
    return () => clearInterval(t);
  }, []);

  return (
    <main className="fixed inset-0 text-foreground font-mono overflow-hidden" style={{ background: "#0a0a0a" }}>
      {/* circuit grid background */}
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(hsl(var(--primary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--primary)) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background/60 to-background" />

      {/* corner brackets */}
      <Corner className="top-3 left-3" />
      <Corner className="top-3 right-3 rotate-90" />
      <Corner className="bottom-3 right-3 rotate-180" />
      <Corner className="bottom-3 left-3 -rotate-90" />

      <div className="relative h-full w-full grid grid-rows-[auto_1fr_auto] px-8 py-5">
        {/* HEADER */}
        <header className="flex flex-col items-center gap-1">
          <Star className="w-7 h-7 text-secondary drop-shadow-[0_0_8px_hsl(var(--secondary))]" />
          <h1 className="text-3xl font-black tracking-wide text-secondary leading-none">MoStar</h1>
          <p className="text-[10px] tracking-[0.4em] text-foreground/80 flex items-center gap-2">
            COVENANT <span className="text-secondary">·</span> INTELLIGENCE{" "}
            <span className="text-secondary">·</span> RESTORATION
          </p>
        </header>

        {/* MIDDLE: gates + sigil */}
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-6 min-h-0">
          {/* LEFT gates */}
          <div className="flex flex-col items-end gap-6 pr-4">
            {GATES_LEFT.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-4">
                <span className="text-[10px] tracking-[0.25em] text-foreground/80">{label}</span>
                <div className="relative w-14 h-14 rounded-full border border-secondary/60 flex items-center justify-center bg-background shadow-[0_0_18px_hsl(var(--secondary)/0.25)]">
                  <Icon className="w-6 h-6 text-secondary" strokeWidth={1.5} />
                </div>
                <div className="h-px w-16 bg-gradient-to-r from-primary/80 to-secondary/80" />
              </div>
            ))}
          </div>

          {/* CENTER sigil */}
          <div className="relative w-[clamp(220px,28vh,360px)] aspect-square">
            <div className="absolute inset-0 rounded-full border border-primary/40 animate-[spin_22s_linear_infinite]" />
            <div className="absolute inset-2 rounded-full border border-secondary/50 animate-[spin_14s_linear_infinite_reverse] shadow-[0_0_40px_hsl(var(--secondary)/0.25)]" />
            <div className="absolute inset-6 rounded-full border border-primary/30" />
            <div
              className="absolute inset-8 rounded-full border-2 border-dashed border-secondary/30 animate-[spin_30s_linear_infinite]"
              style={{ borderStyle: "dotted" }}
            />
            {/* tick marks */}
            <svg className="absolute inset-0 animate-[spin_60s_linear_infinite]" viewBox="0 0 100 100">
              {Array.from({ length: 36 }).map((_, i) => (
                <line
                  key={i}
                  x1="50"
                  y1="4"
                  x2="50"
                  y2={i % 3 === 0 ? "9" : "6"}
                  stroke="hsl(var(--secondary))"
                  strokeWidth="0.3"
                  opacity={i % 3 === 0 ? 0.8 : 0.35}
                  transform={`rotate(${i * 10} 50 50)`}
                />
              ))}
            </svg>
            {/* center glyph — moCon 3D icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              <MoCon
                icon={(ELEMENT_ICON[activeGlyph] ?? "fire") as IconKey}
                size={80}
                className="animate-pulse"
              />
            </div>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="flex gap-10 opacity-60 translate-y-[5.5rem]">
                <MoCon icon="water" size={28} />
                <div className="w-7" />
                <MoCon icon="earth" size={28} />
              </div>
            </div>
          </div>

          {/* RIGHT gates */}
          <div className="flex flex-col items-start gap-6 pl-4">
            {GATES_RIGHT.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-4">
                <div className="h-px w-16 bg-gradient-to-l from-primary/80 to-secondary/80" />
                <div className="relative w-14 h-14 rounded-full border border-secondary/60 flex items-center justify-center bg-background shadow-[0_0_18px_hsl(var(--secondary)/0.25)]">
                  <Icon className="w-6 h-6 text-secondary" strokeWidth={1.5} />
                </div>
                <span className="text-[10px] tracking-[0.25em] text-foreground/80">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PROGRESS BARS */}
        <div className="grid grid-cols-2 gap-x-10 gap-y-2 max-w-6xl mx-auto w-full">
          {BARS.map(({ icon: Icon, label, target }) => {
            const value = Math.min(target, Math.round((progress / 100) * target * 1.2));
            return (
              <div key={label} className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full border border-primary/60 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-secondary" strokeWidth={1.5} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] tracking-[0.25em] text-foreground/85 truncate">
                      {label}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-foreground/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary via-primary to-secondary rounded-full transition-all duration-300 shadow-[0_0_10px_hsl(var(--secondary))]"
                      style={{ width: `${value}%` }}
                    />
                  </div>
                </div>
                <span className="text-secondary text-xs font-bold w-10 text-right tabular-nums">
                  {value}%
                </span>
              </div>
            );
          })}

          {/* footer divider */}
          <div className="col-span-2 mt-3 flex items-center gap-3">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-secondary/40 to-transparent" />
            <div className="w-2 h-2 rotate-45 bg-secondary" />
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-secondary/40 to-transparent" />
          </div>

          <div className="col-span-2 flex flex-col items-center gap-1">
            <p className="text-secondary tracking-[0.6em] text-lg font-bold">
              LOADING{" "}
              <span className="text-primary">
                {".".repeat(dots).padEnd(3, " ")}
              </span>
            </p>
            <p className="text-foreground/70 italic text-xs max-w-xl text-center">
              {voice || '"Truth is the architecture. Justice is the path. Integrity is the destination."'}
            </p>
            {status && (
              <p className="text-muted-foreground text-[10px] mt-1 lowercase">{status}</p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
};

export default LoadingHUD;
