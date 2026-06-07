import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  KpiCard, CouncilList, GlyphPanel, CodeConduit,
  GridFeed, QuickCommands, CovenantOath,
  useGridStream, KPI, FEED_SEED, PageShell,
} from "@/components/grid/parts";
import { AwakeningScreen } from "@/components/grid/awakening";

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
  const { items, pulse } = useGridStream(FEED_SEED);
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

  return (
    <PageShell active="overview">
      <div className="flex h-full flex-col gap-3 min-h-0">
        {/* KPI strip */}
        <div className="grid shrink-0 grid-cols-4 gap-3">
          {KPI.map((k) => <KpiCard key={k.label} k={k} />)}
        </div>
        {/* Main grid */}
        <div className="grid min-h-0 flex-1 grid-cols-12 gap-3">
          <div className="col-span-3 min-h-0"><CouncilList /></div>
          <div className="col-span-6 flex min-h-0 flex-col gap-3">
            <div className="min-h-0 flex-1"><GlyphPanel /></div>
            <div className="shrink-0"><CodeConduit pulse={pulse} /></div>
          </div>
          <div className="col-span-3 flex min-h-0 flex-col gap-3">
            <div className="min-h-0 flex-1"><GridFeed items={items} /></div>
            <div className="shrink-0"><QuickCommands /></div>
          </div>
        </div>
        {/* Covenant oath — compact strip */}
        <div className="shrink-0"><CovenantOath /></div>
      </div>
    </PageShell>
  );
}
