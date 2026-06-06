import { useEffect, useState } from "react";

const LINES = [
  "[MO]        Mostar Grid handshake established.",
  "[DEEPCAL]   Calibration matrix online.",
  "[SIGMA]     Predictive lattice engaged.",
  "[OMEGA]     Threshold breach armed.",
  "[SENTINEL]  Perimeter integrity nominal.",
  "[VAULT]     Cryptographic seal: green.",
  "[CORE]      Consciousness awakening.",
];

export function StartupFeed({ onComplete }: { onComplete: () => void }) {
  const [shown, setShown] = useState<string[]>([]);
  const [current, setCurrent] = useState("");
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);

  useEffect(() => {
    if (lineIdx >= LINES.length) {
      onComplete();
      return;
    }
    const target = LINES[lineIdx];
    if (charIdx < target.length) {
      const t = setTimeout(() => {
        setCurrent(target.slice(0, charIdx + 1));
        setCharIdx(charIdx + 1);
      }, 18);
      return () => clearTimeout(t);
    }
    const pause = setTimeout(() => {
      setShown((s) => [...s, target]);
      setCurrent("");
      setCharIdx(0);
      setLineIdx(lineIdx + 1);
    }, 220);
    return () => clearTimeout(pause);
  }, [lineIdx, charIdx, onComplete]);

  return (
    <div className="pointer-events-none absolute bottom-32 left-8 z-[5] max-w-md font-mono text-[11px] leading-relaxed">
      {shown.map((line, i) => (
        <div key={i} className="text-[oklch(0.85_0.1_75_/_0.75)]">
          {line}
        </div>
      ))}
      {lineIdx < LINES.length && (
        <div className="text-[oklch(0.95_0.18_80)]">
          {current}
          <span className="ml-0.5 inline-block h-[10px] w-[6px] translate-y-[1px] bg-[oklch(0.95_0.18_80)] animate-[typewriter-caret_1s_steps(1)_infinite]" />
        </div>
      )}
    </div>
  );
}
