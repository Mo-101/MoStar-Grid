import { useEffect, useState } from "react";

interface RadioEmitterProps {
  gridPulse: number; // 0-100
}

export const RadioEmitter = ({ gridPulse }: RadioEmitterProps) => {
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    const handleStart = () => setIsSpeaking(true);
    const handleEnd = () => setIsSpeaking(false);

    window.addEventListener("woo-speaking-start", handleStart);
    window.addEventListener("woo-speaking-end", handleEnd);

    // Initial check in case it's already speaking when mounted
    if (window.speechSynthesis && window.speechSynthesis.speaking) {
      setIsSpeaking(true);
    }

    return () => {
      window.removeEventListener("woo-speaking-start", handleStart);
      window.removeEventListener("woo-speaking-end", handleEnd);
    };
  }, []);

  // Calculate animation duration based on pulse. 
  // Heartbeat mode (not speaking): slower pulse based on gridPulse (e.g. 100% = 1.5s, 50% = 3s)
  // Broadcast mode (speaking): fast, continuous waves (0.6s)
  const duration = isSpeaking ? 0.6 : Math.max(1.5, 4 - (gridPulse / 100) * 2.5);

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none flex items-center justify-center opacity-30">
      <div className="relative w-[150vw] h-[150vw] sm:w-[100vw] sm:h-[100vw] max-w-[1400px] max-h-[1400px] flex items-center justify-center mix-blend-screen">
        <svg viewBox="0 0 100 100" className="w-full h-full overflow-visible" preserveAspectRatio="xMidYMid meet">
          <defs>
            <radialGradient id="elemental-gradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="hsl(var(--tier-orange))" /> {/* Ikang */}
              <stop offset="40%" stopColor="#06b6d4" /> {/* Mmọng (Cyan) */}
              <stop offset="70%" stopColor="hsl(var(--tier-zinc))" /> {/* Afim */}
              <stop offset="100%" stopColor="hsl(var(--tier-red))" /> {/* Isong */}
            </radialGradient>
            
            <style>
              {`
                @keyframes ripple {
                  0% { transform: scale(0); opacity: 1; stroke-width: 0.5px; }
                  100% { transform: scale(1); opacity: 0; stroke-width: 2.5px; }
                }
                .wave-circle {
                  fill: none;
                  stroke: url(#elemental-gradient);
                  transform-origin: 50px 50px;
                  animation: ripple ${duration}s linear infinite;
                }
              `}
            </style>
          </defs>

          {/* Render multiple ripples with delays */}
          {[...Array(isSpeaking ? 6 : 3)].map((_, i, arr) => (
            <circle
              key={i}
              cx="50"
              cy="50"
              r="48"
              className="wave-circle"
              style={{
                animationDelay: `${(i / arr.length) * duration}s`,
                opacity: isSpeaking ? 0.9 : 0.4
              }}
            />
          ))}
          
          {/* Core pulse */}
          <circle
            cx="50"
            cy="50"
            r="1"
            fill="url(#elemental-gradient)"
            className="animate-pulse"
            style={{ animationDuration: `${duration}s` }}
          />
        </svg>
      </div>
    </div>
  );
};
