/**
 * ElementalToast — sonner toasts and cards skinned with looping element gifs.
 * Use `elementalToast(element, { title, body })` anywhere, or render
 * `<ElementalCard element="fire" .../>` inline.
 */
import { toast } from "sonner";
import fire from "@/assets/elements/fire.gif.asset.json";
import earth from "@/assets/elements/earth.gif.asset.json";
import air from "@/assets/elements/air.gif.asset.json";
import water from "@/assets/elements/water.gif.asset.json";

export type Element = "fire" | "earth" | "air" | "water";

export const ELEMENT_GIF: Record<Element, string> = {
  fire: fire.url,
  earth: earth.url,
  air: air.url,
  water: water.url,
};

const GLOW: Record<Element, string> = {
  fire: "#ff5a2e",
  earth: "#f6c453",
  air: "#9cd0ff",
  water: "#168bff",
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
  className = "",
  height = 140,
}: {
  element: Element;
  title: string;
  body?: string;
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
        <div
          className="text-[10px] tracking-[0.32em]"
          style={{ color: glow, textShadow: `0 0 8px ${glow}` }}
        >
          {SIGIL[element]} {element.toUpperCase()}
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
