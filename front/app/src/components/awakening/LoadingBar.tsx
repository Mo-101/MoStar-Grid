import { useEffect, useState } from "react";

export function LoadingBar({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const start = performance.now();
    const duration = 5000;
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration);
      setProgress(p);
      if (p < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        onComplete();
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [onComplete]);

  return (
    <div className="pointer-events-none absolute bottom-20 left-1/2 z-[6] w-[420px] -translate-x-1/2">
      <div className="mb-2 flex justify-between font-mono text-[10px] tracking-[0.3em] uppercase text-[oklch(0.85_0.12_75_/_0.85)]">
        <span>Grid Awakening</span>
        <span>{Math.floor(progress * 100).toString().padStart(3, "0")}%</span>
      </div>
      <div
        className="h-[2px] w-full overflow-hidden"
        style={{ background: "oklch(0.85 0.1 75 / 0.15)" }}
      >
        <div
          className="h-full"
          style={{
            width: `${progress * 100}%`,
            background:
              "linear-gradient(90deg, oklch(0.9 0.2 75) 0%, oklch(0.75 0.18 200) 100%)",
            boxShadow: "0 0 12px oklch(0.9 0.2 75 / 0.6)",
          }}
        />
      </div>
    </div>
  );
}
