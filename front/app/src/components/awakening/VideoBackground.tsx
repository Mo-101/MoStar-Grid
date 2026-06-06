import { useRef, useEffect, useState } from "react";
import sunVideo from "@/assets/sun5.mp4";

interface Props {
  progress?: number; // 0-100; when provided, scrubs video instead of autoplaying
}

export function VideoBackground({ progress }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const [failed, setFailed] = useState(false);

  // Scrub currentTime to match loading progress
  useEffect(() => {
    const video = ref.current;
    if (!video || progress === undefined) return;
    const onReady = () => {
      video.currentTime = (progress / 100) * video.duration;
    };
    if (video.readyState >= 1) {
      onReady();
    } else {
      video.addEventListener("loadedmetadata", onReady, { once: true });
    }
  }, [progress]);

  if (failed) {
    return (
      <div
        className="absolute inset-0 z-[1]"
        style={{
          background:
            "radial-gradient(ellipse at 50% 70%, oklch(0.22 0.05 40) 0%, oklch(0.08 0.02 260) 70%, oklch(0.04 0.01 260) 100%)",
        }}
      />
    );
  }

  const controlled = progress !== undefined;

  return (
    <video
      ref={ref}
      className="absolute inset-0 z-[1] h-full w-full object-cover"
      style={{ filter: "brightness(0.65) contrast(1.15) saturate(1.1)" }}
      src={sunVideo}
      autoPlay={!controlled}
      muted
      loop={!controlled}
      playsInline
      preload="auto"
      onError={() => setFailed(true)}
    />
  );
}
