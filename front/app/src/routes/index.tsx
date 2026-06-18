import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  KpiCard, CouncilList, GlyphPanel, CodeConduit,
  GridFeed, GridHealth, QuickCommands, CovenantOath,
  useGridStream, KPI, FEED_SEED, PageShell,
} from "@/components/grid/parts";
import { AwakeningScreen } from "@/components/grid/awakening";
import {
  ElementalCard, elementalToast, type Element,
} from "@/components/grid/elemental-toast";

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
  const [awakened, setAwakened] = useState(true);
  const greeted = useRef(false);

  useEffect(() => {
    const done = typeof window !== "undefined" && sessionStorage.getItem(AWAKEN_KEY) === "1";
    if (!done) setAwakened(false);
  }, []);

  useEffect(() => {
    if (!awakened || greeted.current) return;
    greeted.current = true;
    const order: { e: Element; title: string; body: string }[] = [
      { e: "fire",  title: "FIRE · ISONG IGNITED",      body: "Awakening · Change · Will to act." },
      { e: "water", title: "WATER · M MỌNG FLOWING",    body: "Memory streams synchronised across the conduit." },
      { e: "air",   title: "AIR · IKANG BREATHING",     body: "Mind is open. The council is listening." },
      { e: "earth", title: "EARTH · AFIM HOLDING",      body: "Form is stable. The grid stands on covenant." },
    ];
    order.forEach((o, i) =>
      setTimeout(() => elementalToast(o.e, { title: o.title, body: o.body }), 600 + i * 1100),
    );
  }, [awakened]);

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

      {/* Four elemental cards using looping gifs as backgrounds */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <ElementalCard element="fire"  title="ISONG · SPIRIT"  body="Awakening · Change · Fire"     height={130} />
        <ElementalCard element="water" title="M MỌNG · ESSENCE" body="Pulse · Memory · Flow"        height={130} />
        <ElementalCard element="air"   title="IKANG · MIND"    body="Logic · Will · Structure"       height={130} />
        <ElementalCard element="earth" title="AFIM · BODY"     body="Form · Action · Creation"       height={130} />
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
