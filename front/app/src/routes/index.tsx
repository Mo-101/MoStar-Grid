import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AwakeningScreen } from "@/components/grid/awakening";
import Grid from "@/pages/01-Grid";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MoStar GRID — Covenant Command Center" },
      { name: "description", content: "Real-time command center for the MoStar GRID covenant: agents, mind graph, conduits, and grid health." },
    ],
  }),
  component: GridDashboard,
});

const AWAKEN_KEY = "mostar.grid.awakened";

function GridDashboard() {
  const [awakened, setAwakened] = useState(() => {
    if (typeof window === "undefined") return true;
    return sessionStorage.getItem(AWAKEN_KEY) === "1";
  });

  if (!awakened) {
    return (
      <AwakeningScreen
        onComplete={() => {
          try { sessionStorage.setItem(AWAKEN_KEY, "1"); } catch {}
          setAwakened(true);
        }}
      />
    );
  }

  return <Grid />;
}
