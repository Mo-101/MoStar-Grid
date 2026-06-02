/**
 * MoCon — sovereign icon component
 *
 * GLYPHS (actual alchemical symbols from moCons library):
 *   f3.png      = 🜂  upward triangle + flame  = Fire  / Ikang
 *   glo3t.png   = 🜄  inverted triangle        = Water / Mmọng
 *   gff1.png    = 🜁  circle / ring            = Air   / Afim
 *   glot.png    = 🜃  inverted triangle + bars = Earth / Isong
 *
 * 3D SHAPES (for decorative/UI use):
 *   Pyramid 1/2, Sphere, Helix, Thorus, Icosahedron, Cube, Cylinder, Cone…
 *
 * All glyph files are blue — hue-rotate tints them to their elemental color.
 */

export const ICON = {
  // ── Actual element glyphs ──────────────────────────────────────────────────
  fire:  "f3.png",       // 🜂 Ikang  — upward triangle + flame
  water: "glo3t.png",    // 🜄 Mmọng  — inverted triangle
  air:   "gff1.png",     // 🜁 Afim   — circle / ring
  earth: "glot.png",     // 🜃 Isong  — inverted triangle + bars

  // ── 3D shapes for UI / decorative ─────────────────────────────────────────
  hex:   "Icosahedron.png",  // ⬡ Guest / hex
  star:  "Spheres 2.png",    // ✦ VoiceOrb
  seal:  "Thorus Knot.png",  // ∴ Seal
  gate:  "Pyramid 2.png",    // ⟁ Boot / gate
  node:  "Cube 1.png",       // □ Graph node
  link:  "Cylinder 1.png",   // — Relationship link
  veto:  "Cone.png",         // ✗ Veto / block
} as const;

export type IconKey = keyof typeof ICON;

// hue-rotate shifts the blue base of the glyph files to the elemental color
// blue ≈ 240° on hue wheel; +150° → orange, 0° → blue, -30° → teal, -90° → green
const FILTER: Record<IconKey, string> = {
  fire:  "hue-rotate(150deg) saturate(1.8) brightness(1.1) drop-shadow(0 0 10px hsl(25 100% 55% / 0.9))",
  water: "hue-rotate(0deg)   saturate(1.6) brightness(1.05) drop-shadow(0 0 10px hsl(210 90% 55% / 0.9))",
  air:   "hue-rotate(-30deg) saturate(1.6) brightness(1.05) drop-shadow(0 0 10px hsl(185 80% 50% / 0.9))",
  earth: "hue-rotate(-90deg) saturate(1.6) brightness(1.05) drop-shadow(0 0 10px hsl(140 65% 45% / 0.9))",
  hex:   "drop-shadow(0 0 6px hsl(240 40% 65% / 0.7))",
  star:  "drop-shadow(0 0 8px hsl(45 95% 55% / 0.9))",
  seal:  "drop-shadow(0 0 8px hsl(175 80% 50% / 0.9))",
  gate:  "drop-shadow(0 0 8px hsl(120 70% 45% / 0.9))",
  node:  "drop-shadow(0 0 8px hsl(25 100% 55% / 0.85))",
  link:  "drop-shadow(0 0 8px hsl(210 90% 55% / 0.85))",
  veto:  "drop-shadow(0 0 8px hsl(350 80% 50% / 0.85))",
};

interface MoConProps {
  icon: IconKey;
  size?: number;
  glow?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function MoCon({ icon, size = 24, glow = true, className = "", style }: MoConProps) {
  return (
    <img
      src={`/moCons/${ICON[icon]}`}
      alt=""
      draggable={false}
      width={size}
      height={size}
      className={`object-contain select-none pointer-events-none shrink-0 ${className}`}
      style={{ filter: glow ? FILTER[icon] : "none", ...style }}
    />
  );
}

/** SSE event type → MoCon icon */
export const EVENT_ICON: Record<string, IconKey> = {
  SCROLL:  "fire",
  SEAL:    "seal",
  COMMIT:  "node",
  ATTEST:  "earth",
  PROPOSE: "air",
  DISPUTE: "water",
  VETO:    "veto",
  REJECT:  "veto",
};

/** Legacy emoji → icon key */
export const ELEMENT_ICON: Record<string, IconKey> = {
  "🜂": "fire",
  "🜄": "water",
  "🜁": "air",
  "🜃": "earth",
};
