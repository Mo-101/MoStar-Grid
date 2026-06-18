import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/grid/parts";
import { GridVoiceConsole } from "@/components/grid/voice-console";

export const Route = createFileRoute("/voice")({
  head: () => ({
    meta: [
      { title: "Grid Voice Console — MoStar" },
      { name: "description", content: "Sovereign system surface for the MoStar Grid voice. Routes through Piper, DCX Trinity, and Personality Engine." },
      { property: "og:title", content: "Grid Voice Console — MoStar" },
      { property: "og:description", content: "The Grid speaks. Sovereign voice service surface — not a TTS widget." },
    ],
  }),
  component: VoicePage,
});

function VoicePage() {
  return (
    <PageShell active="voice">
      <GridVoiceConsole />
    </PageShell>
  );
}
