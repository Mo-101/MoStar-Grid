import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  KpiCard, CouncilList, GlyphPanel, CodeConduit,
  GridFeed, GridHealth, QuickCommands, CovenantOath,
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
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {KPI.map((k) => <KpiCard key={k.label} k={k} />)}
      </div>
      <div className="grid flex-1 grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-3"><CouncilList /></div>
        <div className="col-span-12 flex flex-col gap-3 lg:col-span-6">
          <div className="min-h-[560px] flex-1"><GlyphPanel /></div>
          <CodeConduit pulse={pulse} />
        </div>
        <div className="col-span-12 flex flex-col gap-3 lg:col-span-3">
          <GridFeed items={items} />
          <GridHealth />
          <QuickCommands />
        </div>
      </div>
      <CovenantOath />
    </PageShell>
  );
}
