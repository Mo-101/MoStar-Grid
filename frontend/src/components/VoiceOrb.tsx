import { useEffect, useState, useCallback } from "react";
import { speak } from "@/utils/voice";
import "./voice-orb.css";

export const VoiceOrb = () => {
  const [state, setState] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error("SpeechRecognition not supported in this browser.");
      return;
    }

    const rcg = new SpeechRecognition();
    rcg.continuous = false;
    rcg.interimResults = true;
    rcg.lang = "en-US";

    rcg.onstart = () => setState("listening");
    
    rcg.onend = () => {
      // If we stopped listening but aren't thinking, go back to idle
      setState((prev) => (prev === "listening" ? "idle" : prev));
    };

    rcg.onresult = async (event: any) => {
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalText += event.results[i][0].transcript;
        }
      }

      const text = finalText.trim();
      if (text) {
        await handleCommand(text);
      }
    };

    setRecognition(rcg);

    // Listen for TTS events to update state
    const handleWooStart = () => setState("speaking");
    const handleWooEnd = () => setState("idle");

    window.addEventListener("woo-speaking-start", handleWooStart);
    window.addEventListener("woo-speaking-end", handleWooEnd);

    return () => {
      window.removeEventListener("woo-speaking-start", handleWooStart);
      window.removeEventListener("woo-speaking-end", handleWooEnd);
    };
  }, []);

  const handleCommand = async (text: string) => {
    setState("thinking");
    try {
      const res = await fetch("/api/voice-command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      const speech = data.speech || "Command received.";
      
      // State changes to "speaking" automatically via woo-speaking-start event
      await speak(speech, "stable");
    } catch (err) {
      console.error("Voice Agent error:", err);
      setState("idle");
    }
  };

  const startListening = useCallback(() => {
    if (!recognition || state !== "idle") return;
    try {
      recognition.start();
    } catch (e) {
      console.error("Recognition start error:", e);
    }
  }, [recognition, state]);

  // Sync state to body for CSS animations
  useEffect(() => {
    document.body.setAttribute("data-voice-state", state);
  }, [state]);

  return (
    <button
      id="mostar-voice-orb"
      onClick={startListening}
      aria-label="Activate Voice Agent"
      className="mostar-voice-orb"
    >
      ✦
    </button>
  );
};
