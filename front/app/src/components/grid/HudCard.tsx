import type { ReactNode } from "react";

// ── Corner SVGs — top-left cyan staircase ────────────────────────────────────
export function CornerTL({ size = 55 }: { size?: number }) {
  return (
    <svg
      width={size} height={size}
      viewBox="0 0 55 55"
      className="pointer-events-none absolute top-0 left-0 z-10"
      fill="none"
    >
      {/* Main L-bracket */}
      <line x1="2"  y1="2"  x2="2"  y2="51" stroke="#18FEFE" strokeWidth="2.5" />
      <line x1="2"  y1="2"  x2="51" y2="2"  stroke="#18FEFE" strokeWidth="2.5" />
      {/* Inner staircase — vertical ticks (stepping inward) */}
      <line x1="9"  y1="2"  x2="9"  y2="34" stroke="#18FEFE" strokeWidth="1.8" opacity="0.85" />
      <line x1="16" y1="2"  x2="16" y2="22" stroke="#18FEFE" strokeWidth="1.5" opacity="0.7"  />
      <line x1="22" y1="2"  x2="22" y2="14" stroke="#18FEFE" strokeWidth="1.2" opacity="0.55" />
      {/* Inner staircase — horizontal ticks (stepping downward) */}
      <line x1="2"  y1="9"  x2="34" y2="9"  stroke="#18FEFE" strokeWidth="1.8" opacity="0.85" />
      <line x1="2"  y1="16" x2="22" y2="16" stroke="#18FEFE" strokeWidth="1.5" opacity="0.7"  />
      <line x1="2"  y1="22" x2="14" y2="22" stroke="#18FEFE" strokeWidth="1.2" opacity="0.55" />
    </svg>
  );
}

// ── Corner SVGs — bottom-right yellow staircase ──────────────────────────────
export function CornerBR({ size = 55 }: { size?: number }) {
  return (
    <svg
      width={size} height={size}
      viewBox="0 0 55 55"
      className="pointer-events-none absolute bottom-0 right-0 z-10"
      fill="none"
    >
      {/* Main L-bracket */}
      <line x1="53" y1="53" x2="53" y2="4"  stroke="#FAFF08" strokeWidth="2.5" />
      <line x1="53" y1="53" x2="4"  y2="53" stroke="#FAFF08" strokeWidth="2.5" />
      {/* Inner staircase — vertical */}
      <line x1="46" y1="53" x2="46" y2="20" stroke="#FAFF08" strokeWidth="1.8" opacity="0.85" />
      <line x1="39" y1="53" x2="39" y2="32" stroke="#FAFF08" strokeWidth="1.5" opacity="0.7"  />
      <line x1="33" y1="53" x2="33" y2="41" stroke="#FAFF08" strokeWidth="1.2" opacity="0.55" />
      {/* Inner staircase — horizontal */}
      <line x1="53" y1="46" x2="20" y2="46" stroke="#FAFF08" strokeWidth="1.8" opacity="0.85" />
      <line x1="53" y1="39" x2="32" y2="39" stroke="#FAFF08" strokeWidth="1.5" opacity="0.7"  />
      <line x1="53" y1="33" x2="41" y2="33" stroke="#FAFF08" strokeWidth="1.2" opacity="0.55" />
    </svg>
  );
}

// ── Small card corners (for KPI cards) ───────────────────────────────────────
function CornerTLSm() {
  return (
    <svg
      width="32" height="32"
      viewBox="0 0 32 32"
      className="pointer-events-none absolute top-0 left-0 z-10"
      fill="none"
    >
      <line x1="1.5" y1="1.5" x2="1.5" y2="26" stroke="#18FEFE" strokeWidth="2" />
      <line x1="1.5" y1="1.5" x2="26"  y2="1.5" stroke="#18FEFE" strokeWidth="2" />
      <line x1="7"  y1="1.5" x2="7"  y2="17" stroke="#18FEFE" strokeWidth="1.5" opacity="0.8" />
      <line x1="12" y1="1.5" x2="12" y2="10" stroke="#18FEFE" strokeWidth="1.2" opacity="0.6" />
      <line x1="1.5" y1="7"  x2="17" y2="7"  stroke="#18FEFE" strokeWidth="1.5" opacity="0.8" />
      <line x1="1.5" y1="12" x2="10" y2="12" stroke="#18FEFE" strokeWidth="1.2" opacity="0.6" />
    </svg>
  );
}

function CornerBRSm() {
  return (
    <svg
      width="32" height="32"
      viewBox="0 0 32 32"
      className="pointer-events-none absolute bottom-0 right-0 z-10"
      fill="none"
    >
      <line x1="30.5" y1="30.5" x2="30.5" y2="6"  stroke="#FAFF08" strokeWidth="2" />
      <line x1="30.5" y1="30.5" x2="6"    y2="30.5" stroke="#FAFF08" strokeWidth="2" />
      <line x1="25" y1="30.5" x2="25" y2="14" stroke="#FAFF08" strokeWidth="1.5" opacity="0.8" />
      <line x1="20" y1="30.5" x2="20" y2="20" stroke="#FAFF08" strokeWidth="1.2" opacity="0.6" />
      <line x1="30.5" y1="25" x2="14" y2="25" stroke="#FAFF08" strokeWidth="1.5" opacity="0.8" />
      <line x1="30.5" y1="20" x2="20" y2="20" stroke="#FAFF08" strokeWidth="1.2" opacity="0.6" />
    </svg>
  );
}

// ── Icon frame for KPI card — inset cyan shadow + green tick corners ──────────
export function GlyphFrame({
  children,
  colorVar,
}: {
  children: ReactNode;
  colorVar: string; // e.g. "var(--color-neon-blue)"
}) {
  return (
    <div
      className="relative flex h-11 w-11 shrink-0 items-center justify-center"
      style={{
        background: "rgba(0,0,0,0.01)",
        boxShadow: [
          "inset -10px 0 0 rgba(24,254,254,0.08)",
          "inset  10px 0 0 rgba(24,254,254,0.08)",
          "inset 0 -10px 0 rgba(24,254,254,0.08)",
          "inset 0  10px 0 rgba(24,254,254,0.08)",
          `0 0 0 1px ${colorVar}33`,
        ].join(", "),
      }}
    >
      {/* Green tick marks at all four corners of the icon frame */}
      <svg className="pointer-events-none absolute inset-0 w-full h-full" viewBox="0 0 44 44" fill="none">
        <line x1="0"  y1="0"  x2="9"  y2="0"  stroke="#06F7A1" strokeWidth="1" />
        <line x1="0"  y1="0"  x2="0"  y2="9"  stroke="#06F7A1" strokeWidth="1" />
        <line x1="44" y1="0"  x2="35" y2="0"  stroke="#06F7A1" strokeWidth="1" />
        <line x1="44" y1="0"  x2="44" y2="9"  stroke="#06F7A1" strokeWidth="1" />
        <line x1="0"  y1="44" x2="9"  y2="44" stroke="#06F7A1" strokeWidth="1" />
        <line x1="0"  y1="44" x2="0"  y2="35" stroke="#06F7A1" strokeWidth="1" />
        <line x1="44" y1="44" x2="35" y2="44" stroke="#06F7A1" strokeWidth="1" />
        <line x1="44" y1="44" x2="44" y2="35" stroke="#06F7A1" strokeWidth="1" />
        {/* Center cross */}
        <line x1="22" y1="16" x2="22" y2="28" stroke="#06F7A1" strokeWidth="0.5" opacity="0.5" />
        <line x1="16" y1="22" x2="28" y2="22" stroke="#06F7A1" strokeWidth="0.5" opacity="0.5" />
      </svg>
      {children}
    </div>
  );
}

// ── Big panel wrapper ─────────────────────────────────────────────────────────
export function HudPanel({
  children,
  className = "",
  cornerSize = 55,
}: {
  children: ReactNode;
  className?: string;
  cornerSize?: number;
}) {
  return (
    <div
      className={`relative overflow-hidden ${className}`}
      style={{
        background: "rgba(0, 3, 12, 0.45)",
        border: "2px solid #2F7093",
        borderRadius: 0,
      }}
    >
      <CornerTL size={cornerSize} />
      <CornerBR size={cornerSize} />
      {children}
    </div>
  );
}

// ── Small HUD metric card ─────────────────────────────────────────────────────
export function HudMetricCard({
  label,
  value,
  delta,
  color,
  glyphNode,
}: {
  label: string;
  value: number;
  delta: number;
  color: string; // Tailwind color name, e.g. "neon-blue"
  glyphNode: ReactNode;
}) {
  const fmt = (n: number) => n.toLocaleString("en-US");

  return (
    <div
      className="relative overflow-hidden p-3"
      style={{
        background: "rgba(0, 3, 12, 0.35)",
        border: "1px solid #2F7093",
      }}
    >
      <CornerTLSm />
      <CornerBRSm />

      {/* Gold left edge accent */}
      <div
        className="pointer-events-none absolute left-0 top-[15%] bottom-[35%] w-[2px]"
        style={{ background: "#987F41", opacity: 0.75 }}
      />
      {/* Gray left-edge ticks (3 tiny marks at top-left, from Group 225) */}
      <div className="pointer-events-none absolute left-[2px] top-[62%] flex flex-col gap-[2px]">
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ width: `${7 - i * 2}px`, height: "1.5px", background: "#9B9B9B", opacity: 0.5 }} />
        ))}
      </div>
      {/* Cyan top accent line */}
      <div
        className="pointer-events-none absolute top-0 left-[4%] right-[41%] h-[1.5px]"
        style={{ background: "#4AF4FF", opacity: 0.45 }}
      />
      {/* Green signal bar (bottom) */}
      <div
        className="pointer-events-none absolute bottom-[12%] left-[61%] right-[17%] h-[1.5px]"
        style={{ background: "#32FF81", opacity: 0.6 }}
      />

      <div className="flex items-center gap-3">
        <GlyphFrame colorVar={`var(--color-${color})`}>{glyphNode}</GlyphFrame>
        <div className="flex-1 min-w-0">
          <div className="text-[9px] tracking-[0.28em] text-muted-foreground truncate">{label}</div>
          <div
            className="mt-0.5 text-xl font-semibold tabular-nums"
            style={{ color: `var(--color-${color})` }}
          >
            {fmt(value)}
          </div>
          <div className="text-[9px] tracking-[0.2em] neon-text-green">+{fmt(delta)} TODAY</div>
        </div>
      </div>
    </div>
  );
}
