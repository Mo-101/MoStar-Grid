import g10 from "@/assets/moCons/g10.png";
import g2 from "@/assets/moCons/g2.png";
import g8 from "@/assets/moCons/g8.png";
import g5 from "@/assets/moCons/g5.png";
import g12 from "@/assets/moCons/g12.png";
import g11 from "@/assets/moCons/g11.png";
import g7 from "@/assets/moCons/g7.png";
import g3 from "@/assets/moCons/g3.png";

export type GlyphName =
  | "covenant"   // blue inverted-triangle bar — main MoStar / hand replacement
  | "target"     // blue crosshair circle — radar / target
  | "ban"        // black prohibition — alerts
  | "sun"        // gold cross-in-circle — legacy
  | "spark"      // blue 4-point sparkle — essence / info
  | "eye"        // blue eye-spiral — vision
  | "eyeLight"   // white eye-spiral — light variant
  | "venus";     // gold venus — gold accent

const MAP: Record<GlyphName, { url: string }> = {
  covenant: { url: g2 },
  target: { url: g8 },
  ban: { url: g5 },
  sun: { url: g12 },
  spark: { url: g11 },
  eye: { url: g7 },
  eyeLight: { url: g3 },
  venus: { url: g10 },
};

export function Glyph({
  name,
  size = 40,
  glow,
  className = "",
}: {
  name: GlyphName;
  size?: number;
  glow?: string; // css color
  className?: string;
}) {
  const src = MAP[name].url;
  return (
    <img
      src={src}
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
