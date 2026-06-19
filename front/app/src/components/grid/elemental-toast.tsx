/**
 * ElementalToast — sonner toasts and cards skinned with looping element gifs.
 * Use `elementalToast(element, { title, body })` anywhere, or render
 * `<ElementalCard element="fire" .../>` inline.
 */
import { toast } from "sonner";
import fire from "@/assets/moCons/fire_element.gif";
import earth from "@/assets/moCons/earth_element.gif";
import air from "@/assets/moCons/air_element.gif";
import water from "@/assets/moCons/water_element.gif";

export type Element = "fire" | "earth" | "air" | "water";

export const ELEMENT_GIF: Record<Element, string> = {
  fire,
  earth,
  air,
  water,
};

const GLOW: Record<Element, string> = {
  fire: "#e93908",
  earth: "#eea806",
  air: "#9aaef0",
  water: "#1625ff",
};

const SIGIL: Record<Element, string> = {
  fire: "🜂",
  earth: "🜃",
  air: "🜁",
  water: "🜄",
};

export function ElementalCard({
  element,
  title,
  body,
  metric,
  className = "",
  height = 140,
}: {
  element: Element;
  title: string;
  body?: string;
  metric?: { label: string; value: number; delta?: number };
  className?: string;
  height?: number;
}) {
  const glow = GLOW[element];
  return (
    <div
      className={`relative overflow-hidden rounded-md border ${className}`}
      style={{
        height,
        borderColor: `${glow}55`,
        boxShadow: `0 0 32px ${glow}33, inset 0 0 24px ${glow}22`,
      }}
    >
      <img
        src={ELEMENT_GIF[element]}
        alt=""
        aria-hidden
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-90"
      />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.55) 70%, rgba(0,0,0,0.85) 100%)",
        }}
      />
      <div className="relative z-10 flex h-full flex-col justify-between p-3 font-mono">
        <div className="flex items-start justify-between gap-2">
          <div
            className="text-[10px] tracking-[0.32em]"
            style={{ color: glow, textShadow: `0 0 8px ${glow}` }}
          >
            {SIGIL[element]} {element.toUpperCase()}
          </div>
          {metric && (
            <div className="text-right leading-tight">
              <div
                className="text-lg font-semibold tabular-nums"
                style={{ color: "#f3f7ff", textShadow: `0 0 10px ${glow}` }}
              >
                {metric.value.toLocaleString("en-US")}
              </div>
              {metric.delta != null && (
                <div
                  className="text-[9px] tracking-[0.15em]"
                  style={{ color: glow }}
                >
                  + {metric.delta.toLocaleString("en-US")} TODAY
                </div>
              )}
            </div>
          )}
        </div>
        <div>
          <div
            className="text-sm tracking-[0.18em]"
            style={{ color: "#f3f7ff", textShadow: `0 0 10px ${glow}` }}
          >
            {title}
          </div>
          {body && (
            <div className="mt-1 text-[11px] leading-snug text-white/80">
              {body}
            </div>
          )}
          {metric && (
            <div
              className="mt-0.5 text-[9px] tracking-[0.25em]"
              style={{ color: "rgba(255,255,255,0.6)" }}
            >
              {metric.label}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function elementalToast(
  element: Element,
  opts: { title: string; body?: string; duration?: number },
) {
  toast.custom(
    () => (
      <ElementalCard
        element={element}
        title={opts.title}
        body={opts.body}
        className="w-[360px]"
        height={120}
      />
    ),
    { duration: opts.duration ?? 4200 },
  );
}
