import { useEffect, useMemo, useRef } from "react";
import { deriveScene, type SkyScene, type SkyReading } from "@/lib/weather-scene";

/**
 * Live sky renderer for the weather command card.
 *
 * This component contains no meteorology — it draws exactly what deriveScene()
 * reports from the measured reading. Cloud deck, rain rate, drift direction,
 * haze and daylight are all live values, so the card's background genuinely is
 * the observed weather at that hub rather than a decorative loop.
 *
 * Palette note: this sits behind body copy inside a dark console UI, so even
 * full midday is rendered in a muted night-ops range. Brightness tracks the
 * real sun; absolute luminance stays low enough for text contrast.
 */

const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";

interface Drop {
  x: number;
  y: number;
  len: number;
  speed: number;
  alpha: number;
}

interface Cloud {
  x: number;
  y: number;
  radius: number;
  alpha: number;
  drift: number;
}

interface Star {
  x: number;
  y: number;
  radius: number;
  phase: number;
}

/** Sky gradient stops, interpolated between night and day by scene.daylight. */
function skyStops(scene: SkyScene): [string, string] {
  const { daylight, condition, goldenHour, cloudCover } = scene;

  // Storm and overcast decks flatten the sky toward slate regardless of hour.
  const heavy = condition === "THUNDERSTORM" || condition === "HEAVY_RAIN";
  const dusty = condition === "DUST";

  if (dusty) {
    const l = 0.16 + daylight * 0.14;
    return [`oklch(${l} 0.05 68)`, `oklch(${l + 0.06} 0.07 74)`];
  }
  if (heavy) {
    const l = 0.09 + daylight * 0.07;
    return [`oklch(${l} 0.02 265)`, `oklch(${l + 0.05} 0.025 258)`];
  }
  if (goldenHour) {
    // Real low-sun warmth, kept dim so it reads as horizon glow not a sunset
    // wallpaper.
    return [`oklch(${0.11 + daylight * 0.05} 0.04 285)`, `oklch(${0.2 + daylight * 0.1} 0.09 55)`];
  }

  const top = 0.08 + daylight * 0.1 - cloudCover * 0.02;
  const bottom = 0.13 + daylight * 0.16 - cloudCover * 0.03;
  const chroma = 0.035 + daylight * 0.045;
  return [`oklch(${top} ${chroma} 258)`, `oklch(${bottom} ${chroma} 240)`];
}

function makeClouds(count: number, width: number, height: number): Cloud[] {
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    // Cloud banks concentrate in the upper two-thirds, as they appear from
    // the ground looking up.
    y: Math.random() * height * 0.62,
    radius: height * (0.16 + Math.random() * 0.3),
    alpha: 0.16 + Math.random() * 0.3,
    // Parallax: nearer (larger) banks travel faster.
    drift: 0.35 + Math.random() * 0.85,
  }));
}

function makeDrops(count: number, width: number, height: number): Drop[] {
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    len: 8 + Math.random() * 16,
    speed: 0.6 + Math.random() * 0.7,
    alpha: 0.18 + Math.random() * 0.4,
  }));
}

function makeStars(count: number, width: number, height: number): Star[] {
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height * 0.7,
    radius: 0.4 + Math.random() * 0.9,
    phase: Math.random() * Math.PI * 2,
  }));
}

export function WeatherSky({
  reading,
  className = "",
}: {
  reading: SkyReading;
  className?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const sceneRef = useRef<SkyScene | null>(null);
  // Set by the render effect; lets a condition change re-seed particle
  // populations without tearing down the animation loop.
  const reseedRef = useRef<(() => void) | null>(null);

  // Re-derived whenever the live reading changes, so a new observation
  // immediately becomes a new sky.
  const scene = useMemo(() => deriveScene(reading), [reading]);
  sceneRef.current = scene;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let clouds: Cloud[] = [];
    let drops: Drop[] = [];
    let stars: Star[] = [];
    let frame = 0;
    let flashUntil = 0;
    let nextFlashAt = performance.now() + 2_000 + Math.random() * 5_000;

    const reduce = window.matchMedia(REDUCED_MOTION);

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const current = sceneRef.current;
      const cloudCount = Math.round(4 + (current?.cloudCover ?? 0) * 14);
      const dropCount = Math.round((current?.rainRate ?? 0) * (current?.snow ? 90 : 320));
      clouds = makeClouds(cloudCount, width, height);
      drops = makeDrops(dropCount, width, height);
      stars = makeStars(70, width, height);
    };

    const draw = (time: number) => {
      const current = sceneRef.current;
      if (!current || !width || !height) return;

      const still = reduce.matches;
      const t = still ? 0 : time;

      // ── Sky ──────────────────────────────────────────────────────────────
      const [top, bottom] = skyStops(current);
      const sky = ctx.createLinearGradient(0, 0, 0, height);
      sky.addColorStop(0, top);
      sky.addColorStop(1, bottom);
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, width, height);

      // ── Stars (only a genuinely dark, open sky) ───────────────────────────
      if (current.night && current.cloudCover < 0.55) {
        const visibility = (1 - current.cloudCover / 0.55) * 0.7;
        for (const star of stars) {
          const twinkle = still ? 0.7 : 0.55 + 0.45 * Math.sin(t / 900 + star.phase);
          ctx.globalAlpha = visibility * twinkle;
          ctx.fillStyle = "#dfe9ff";
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = 1;
      }

      // ── Sun / moon ───────────────────────────────────────────────────────
      // Vertical position follows real elevation; below the horizon the body
      // is simply not drawn.
      if (current.sunElevationDeg > -4) {
        const x = current.sunX * width;
        const y = height * (0.86 - Math.min(1, Math.max(0, current.sunElevationDeg / 70)) * 0.72);
        const occlusion = 1 - current.cloudCover * 0.75;
        const radius = height * 0.09;
        const glow = ctx.createRadialGradient(x, y, 0, x, y, radius * 4.5);
        const warm = current.goldenHour;
        glow.addColorStop(0, warm ? "rgba(255,186,110,0.85)" : "rgba(255,238,200,0.7)");
        glow.addColorStop(0.18, warm ? "rgba(255,150,80,0.3)" : "rgba(210,235,255,0.26)");
        glow.addColorStop(1, "rgba(255,255,255,0)");
        ctx.globalAlpha = Math.max(0, occlusion);
        ctx.fillStyle = glow;
        ctx.fillRect(x - radius * 4.5, y - radius * 4.5, radius * 9, radius * 9);
        ctx.globalAlpha = 1;
      } else if (current.night && current.cloudCover < 0.7) {
        const x = (1 - current.sunX) * width;
        const y = height * 0.26;
        const radius = height * 0.055;
        const glow = ctx.createRadialGradient(x, y, 0, x, y, radius * 3.4);
        glow.addColorStop(0, "rgba(214,228,255,0.5)");
        glow.addColorStop(0.3, "rgba(160,190,255,0.13)");
        glow.addColorStop(1, "rgba(255,255,255,0)");
        ctx.globalAlpha = 1 - current.cloudCover;
        ctx.fillStyle = glow;
        ctx.fillRect(x - radius * 3.4, y - radius * 3.4, radius * 6.8, radius * 6.8);
        ctx.globalAlpha = 1;
      }

      // ── Cloud deck ───────────────────────────────────────────────────────
      const speed = 0.004 + current.windStrength * 0.05;
      const tint =
        current.condition === "DUST"
          ? "225,180,120"
          : current.night
            ? "150,168,205"
            : "205,222,245";
      for (const cloud of clouds) {
        if (!still) {
          cloud.x += current.windX * speed * cloud.drift * 16;
          const span = cloud.radius * 2;
          if (cloud.x - span > width) cloud.x = -span;
          if (cloud.x + span < 0) cloud.x = width + span;
        }
        const gradient = ctx.createRadialGradient(
          cloud.x,
          cloud.y,
          0,
          cloud.x,
          cloud.y,
          cloud.radius,
        );
        const alpha = cloud.alpha * (0.35 + current.cloudCover * 0.85);
        gradient.addColorStop(0, `rgba(${tint},${alpha})`);
        gradient.addColorStop(0.55, `rgba(${tint},${alpha * 0.4})`);
        gradient.addColorStop(1, `rgba(${tint},0)`);
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(cloud.x, cloud.y, cloud.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      // ── Haze / fog / dust ────────────────────────────────────────────────
      if (current.hazeDensity > 0) {
        const haze = ctx.createLinearGradient(0, height, 0, 0);
        const base = current.condition === "DUST" ? "198,158,96" : "176,192,214";
        haze.addColorStop(0, `rgba(${base},${current.hazeDensity * 0.75})`);
        haze.addColorStop(1, `rgba(${base},${current.hazeDensity * 0.12})`);
        ctx.fillStyle = haze;
        ctx.fillRect(0, 0, width, height);
      }

      // ── Precipitation ────────────────────────────────────────────────────
      if (drops.length) {
        const slant = current.windX * current.windStrength * 26;
        if (current.snow) {
          ctx.fillStyle = "rgba(233,242,255,0.85)";
          for (const drop of drops) {
            if (!still) {
              drop.y += drop.speed * 0.7;
              drop.x += Math.sin(drop.y / 40) * 0.6 + current.windX * current.windStrength * 1.2;
              if (drop.y > height) {
                drop.y = -6;
                drop.x = Math.random() * width;
              }
            }
            ctx.globalAlpha = drop.alpha;
            ctx.beginPath();
            ctx.arc(drop.x, drop.y, 1.3, 0, Math.PI * 2);
            ctx.fill();
          }
        } else {
          ctx.strokeStyle = "rgba(186,214,255,0.9)";
          ctx.lineWidth = 1;
          for (const drop of drops) {
            const fall = 6 + current.rainRate * 16;
            if (!still) {
              drop.y += drop.speed * fall;
              drop.x += (slant / height) * drop.speed * fall;
              if (drop.y > height) {
                drop.y = -drop.len;
                drop.x = Math.random() * width;
              }
              if (drop.x > width + 20) drop.x = -20;
              if (drop.x < -20) drop.x = width + 20;
            }
            ctx.globalAlpha = drop.alpha;
            ctx.beginPath();
            ctx.moveTo(drop.x, drop.y);
            ctx.lineTo(drop.x + (slant / height) * drop.len, drop.y + drop.len);
            ctx.stroke();
          }
        }
        ctx.globalAlpha = 1;
      }

      // ── Lightning (measured thunderstorms only) ──────────────────────────
      if (current.lightning && !still) {
        if (time > nextFlashAt) {
          flashUntil = time + 90 + Math.random() * 110;
          nextFlashAt = time + 2_500 + Math.random() * 6_500;
        }
        if (time < flashUntil) {
          const intensity = 0.22 + Math.random() * 0.3;
          ctx.fillStyle = `rgba(214,230,255,${intensity})`;
          ctx.fillRect(0, 0, width, height);
        }
      }

      // ── Ground scrim ─────────────────────────────────────────────────────
      // Guarantees body-copy contrast no matter how bright the live sky gets.
      const scrim = ctx.createLinearGradient(0, 0, 0, height);
      scrim.addColorStop(0, "rgba(6,10,22,0.28)");
      scrim.addColorStop(0.55, "rgba(6,10,22,0.52)");
      scrim.addColorStop(1, "rgba(6,10,22,0.78)");
      ctx.fillStyle = scrim;
      ctx.fillRect(0, 0, width, height);
    };

    const loop = (time: number) => {
      draw(time);
      frame = requestAnimationFrame(loop);
    };

    reseedRef.current = resize;
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();

    // A static sky still has to be a correct sky, so reduced-motion renders one
    // frame rather than nothing.
    if (reduce.matches) {
      draw(0);
    } else {
      frame = requestAnimationFrame(loop);
    }

    const onMotionChange = () => {
      cancelAnimationFrame(frame);
      if (reduce.matches) draw(0);
      else frame = requestAnimationFrame(loop);
    };
    reduce.addEventListener("change", onMotionChange);

    // Background tabs must not burn frames.
    const onVisibility = () => {
      cancelAnimationFrame(frame);
      if (!document.hidden && !reduce.matches) frame = requestAnimationFrame(loop);
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      reduce.removeEventListener("change", onMotionChange);
      document.removeEventListener("visibilitychange", onVisibility);
      reseedRef.current = null;
    };
  }, []);

  // Cloud and droplet counts are populated from the scene, so a new observation
  // that changes the condition has to rebuild them. Colour, drift and daylight
  // are read fresh every frame and need no re-seed.
  useEffect(() => {
    reseedRef.current?.();
  }, [scene.condition, scene.rainRate, scene.cloudCover]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
    />
  );
}
