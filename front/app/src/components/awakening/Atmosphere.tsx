export function Atmosphere() {
  const particles = Array.from({ length: 40 }, (_, i) => ({
    cx: Math.random() * 100,
    cy: Math.random() * 100,
    r: Math.random() * 1.2 + 0.3,
    delay: Math.random() * 12,
    dur: 18 + Math.random() * 14,
    op: 0.15 + Math.random() * 0.35,
    key: i,
  }));

  return (
    <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
      {/* Drifting fog gradient */}
      <div
        className="absolute inset-0 animate-[bloom-pulse_12s_ease-in-out_infinite]"
        style={{
          background:
            "radial-gradient(ellipse at 50% 60%, oklch(0.7 0.15 60 / 0.18) 0%, transparent 55%)",
        }}
      />
      <div
        className="absolute inset-0 mix-blend-screen"
        style={{
          background:
            "linear-gradient(180deg, transparent 0%, oklch(0.3 0.08 250 / 0.12) 50%, transparent 100%)",
          animation: "dust-drift 30s linear infinite",
        }}
      />

      {/* Particles */}
      <svg
        className="absolute inset-0 h-full w-full"
        preserveAspectRatio="none"
        viewBox="0 0 100 100"
      >
        {particles.map((p) => (
          <circle
            key={p.key}
            cx={p.cx}
            cy={p.cy}
            r={p.r}
            fill="oklch(0.95 0.05 80)"
            opacity={p.op}
            style={{
              animation: `dust-drift ${p.dur}s ease-in-out ${p.delay}s infinite`,
              transformOrigin: `${p.cx}px ${p.cy}px`,
            }}
          />
        ))}
      </svg>
    </div>
  );
}
