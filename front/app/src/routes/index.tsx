import { createFileRoute } from "@tanstack/react-router";
import {
  CouncilList,
  CodeConduit,
  GridFeed,
  useLiveFeed,
  useGridStatus,
  KPI_META,
  PageShell,
} from "@/components/grid/parts";
import { ElementalCard, type Element } from "@/components/grid/elemental-toast";
import { GlyphPanel as CovenantRuntimeRing } from "@/components/grid/parts";

const ELEMENT_QUADRANTS: { element: Element; title: string; body: string }[] = [
  { element: "fire", title: "ISONG · SPIRIT", body: "Awakening · Change · Fire" },
  { element: "water", title: "M MỌNG · ESSENCE", body: "Pulse · Memory · Flow" },
  { element: "air", title: "IKANG · MIND", body: "Logic · Will · Structure" },
  { element: "earth", title: "AFIM · BODY", body: "Form · Action · Creation" },
];

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MoStar GRID — Covenant Home" },
      {
        name: "description",
        content:
          "Ultra real-time Covenant Home for the MoStar GRID: awakening nodes, live telemetry, agents, soulprint, Woo, and grid health.",
      },
    ],
  }),
  component: GridDashboard,
});

function GridDashboard() {
  const { items, pulse, connected } = useLiveFeed();
  const { data: status } = useGridStatus();

  const liveValues: Record<(typeof KPI_META)[number]["key"], number | null> = {
    nodes: status?.mindgraph.nodes ?? null,
    relationships: status?.mindgraph.relationships ?? null,
    events: status?.density.label_distribution.GridEvent ?? null,
    utterances: status?.density.label_distribution.WooUtterance ?? null,
  };

  return (
    <PageShell active="overview">
      <section className="grid shrink-0 grid-cols-2 gap-3 md:grid-cols-4">
        {ELEMENT_QUADRANTS.map((q, i) => {
          const meta = KPI_META[i];
          return (
            <ElementalCard
              key={q.element}
              element={q.element}
              title={q.title}
              body={q.body}
              metric={{ label: meta.label, value: liveValues[meta.key] ?? 0 }}
              height={130}
            />
          );
        })}
      </section>

      <section className="grid min-h-0 flex-1 grid-cols-12 gap-3">
        <aside className="col-span-12 min-h-0 lg:col-span-3">
          <CouncilList />
        </aside>

        <main className="col-span-12 flex min-h-0 flex-col gap-3 lg:col-span-6">
          <div className="min-h-0 flex-1">
            <CovenantRuntimeRing />
          </div>
          <div className="shrink-0">
            <CodeConduit pulse={pulse} />
          </div>
        </main>

        <aside className="col-span-12 min-h-0 lg:col-span-3">
          <GridFeed items={items} connected={connected} />
        </aside>
      </section>
    </PageShell>
  );
}
