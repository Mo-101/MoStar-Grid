// All glyphs served from /public/moCons/ — no asset.json, no CDN dependency.
const BASE = "/moCons";

export type GlyphName =
  | "covenant"       // gold trinity network        — df (7)
  | "target"         // blue crosshair              — df (2)
  | "ban"            // black prohibition           — df (4)
  | "sun"            // gold quartered circle       — df (5)
  | "spark"          // blue 4-point sparkle        — df (6)
  | "eye"            // blue eye-spiral             — df (8)
  | "eyeLight"       // white eye-spiral            — df (9)
  | "venus"          // gold venus                  — df (1)
  | "pulse"          // blue lightning bolt         — df (3)
  | "venusDark"      // black venus                 — df (10)
  | "covenantGold"   // gold trinity (alias)        — sd (1)
  | "triangleUp"     // black upward triangle       — sd (2)
  | "triangleDown"   // white downward triangle     — sd (3)
  | "covenantLight"  // white trinity               — sd (4)
  | "banDark"        // black prohibition (alias)   — sd (5)
  | "sunGold";       // gold quartered circle (alias)— sd (6)

const MAP: Record<GlyphName, string> = {
  venus:         `${BASE}/df (1).png`,
  target:        `${BASE}/df (2).png`,
  pulse:         `${BASE}/df (3).png`,
  ban:           `${BASE}/df (4).png`,
  sun:           `${BASE}/df (5).png`,
  spark:         `${BASE}/df (6).png`,
  covenant:      `${BASE}/df (7).png`,
  eye:           `${BASE}/df (8).png`,
  eyeLight:      `${BASE}/df (9).png`,
  venusDark:     `${BASE}/df (10).png`,
  covenantGold:  `${BASE}/sd (1).png`,
  triangleUp:    `${BASE}/sd (2).png`,
  triangleDown:  `${BASE}/sd (3).png`,
  covenantLight: `${BASE}/sd (4).png`,
  banDark:       `${BASE}/sd (5).png`,
  sunGold:       `${BASE}/sd (6).png`,
};

export function Glyph({
  name,
  size = 20,
  glow,
  className = "",
}: {
  name: GlyphName;
  size?: number;
  glow?: string;
  className?: string;
}) {
  return (
    <img
      src={MAP[name]}
      alt=""
      draggable={false}
      width={size}
      height={size}
      className={`inline-block select-none object-contain ${className}`}
      style={{
        width: size,
        height: size,
        filter: glow ? `drop-shadow(0 0 8px ${glow})` : undefined,
      }}
    />
  );
}
