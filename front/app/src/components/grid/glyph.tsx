export type GlyphName =
  | "covenant"
  | "grid"
  | "council"
  | "mind"
  | "lattice"
  | "events"
  | "conduit"
  | "sanctuary"
  | "moscripts"
  | "settings"
  | "health"
  | "nodes"
  | "relationships"
  | "utterances"
  | "status"
  | "warning"
  | "alert"
  | "info"
  | "seal"
  | "memory"
  | "target"
  | "sun"
  | "spark"
  | "eye"
  | "eyelight"
  | "venus"
  | "ban"
  | "cube";

const icon = (file: string) => `/moCons/${encodeURIComponent(file)}`;

const MAP: Record<GlyphName, { url: string }> = {
  covenant: { url: icon("df (10).png") },
  grid: { url: icon("df (1).png") },
  council: { url: icon("df (2).png") },
  mind: { url: icon("df (3).png") },
  lattice: { url: icon("df (4).png") },
  events: { url: icon("df (5).png") },
  conduit: { url: icon("df (6).png") },
  sanctuary: { url: icon("df (7).png") },
  moscripts: { url: icon("df (8).png") },
  settings: { url: icon("df (9).png") },

  health: { url: icon("sd (2).png") },
  nodes: { url: icon("sd (3).png") },
  relationships: { url: icon("sd (4).png") },
  utterances: { url: icon("sd (5).png") },
  status: { url: icon("sd (6).png") },

  warning: { url: icon("f3.png") },
  alert: { url: icon("glo3t.png") },
  info: { url: icon("ms_34_-removebg-preview.png") },
  seal: { url: icon("ms_18_-removebg-preview.png") },
  memory: { url: icon("ms_19_-removebg-preview.png") },
  target: { url: icon("ms_14_-removebg-preview.png") },
  sun: { url: icon("ms_41_-removebg-preview.png") },
  spark: { url: icon("ms_16_-removebg-preview.png") },
  eye: { url: icon("ms_35_-removebg-preview.png") },
  eyelight: { url: icon("ms_35_-removebg-preview.png") },
  venus: { url: icon("ms_41_-removebg-preview.png") },
  ban: { url: icon("ms_17_-removebg-preview.png") },
  cube: { url: icon("Cube 1.png") },
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
  const src = MAP[name]?.url ?? MAP.covenant.url;

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
        filter: glow
          ? `drop-shadow(0 0 6px ${glow}) drop-shadow(0 0 14px ${glow})`
          : undefined,
      }}
    />
  );
}
