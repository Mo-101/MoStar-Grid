import glot from "@/assets/glyphs/glot.png.asset.json";
import ms14 from "@/assets/glyphs/ms14.png.asset.json";
import ms17 from "@/assets/glyphs/ms17.png.asset.json";
import ms18 from "@/assets/glyphs/ms18.png.asset.json";
import ms19 from "@/assets/glyphs/ms19.png.asset.json";
import ms34 from "@/assets/glyphs/ms34.png.asset.json";
import ms35 from "@/assets/glyphs/ms35.png.asset.json";
import ms41 from "@/assets/glyphs/ms41.png.asset.json";

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
  covenant: glot,
  target: ms14,
  ban: ms17,
  sun: ms18,
  spark: ms19,
  eye: ms34,
  eyeLight: ms35,
  venus: ms41,
};

export function Glyph({
  name,
  size = 20,
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
