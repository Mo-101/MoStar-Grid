import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import {
  CouncilList,
  GlyphPanel,
  CodeConduit,
  GridFeed,
  useLiveFeed,
  KpiRow,
  PageShell,
} from "@/components/grid/parts";
import { AwakeningScreen } from "@/components/grid/awakening";
import { GridSnapshotPanel } from "@/components/grid/grid-snapshot";
import { ElementalCard, elementalToast, type Element } from "@/components/grid/elemental-toast";
import { elementByClassical, type ClassicalElement } from "@/lib/gridElements";

// Body copy per classical element, written for the aspect (fire=spirit,
// water=essence, air=mind, earth=body) — not for a name. The name is read
// from GRID_ELEMENTS via elementByClassical() below so it can never rotate
// out of sync with this copy again.
const CLASSICAL_ORDER: ClassicalElement[] = ["fire", "water", "air", "earth"];
const GREETING_VERB: Record<ClassicalElement, string> = {
  fire: "IGNITED",
  water: "FLOWING",
  air: "BREATHING",
  earth: "HOLDING",
};
const GREETING_BODY: Record<ClassicalElement, string> = {
  fire: "Awakening · Change · Will to act.",
  water: "Memory streams synchronised across the conduit.",
  air: "Mind is open. The council is listening.",
  earth: "Form is stable. The grid stands on covenant.",
};

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MoStar GRID — Covenant Command Center" },
      {
        name: "description",
        content:
          "Real-time command center for the MoStar GRID covenant: agents, mind graph, conduits, and grid health.",
      },
    ],
  }),
  component: GridDashboard,
});

const AWAKEN_KEY = "mostar.grid.awakened";

function GridDashboard() {
  const { items, pulse, reachable, newestAt } = useLiveFeed();
  const [awakened, setAwakened] = useState(true);
  const greeted = useRef(false);

  useEffect(() => {
    const forceBoot =
      typeof window !== "undefined" &&
      new URLSearchParams(window.location.search).get("boot") === "1";
    const done =
      typeof window !== "undefined" && !forceBoot && sessionStorage.getItem(AWAKEN_KEY) === "1";
    if (!done) setAwakened(false);
  }, []);

  useEffect(() => {
    if (!awakened || greeted.current) return;
    greeted.current = true;
    const order: { e: Element; title: string; body: string }[] = CLASSICAL_ORDER.map((cls) => {
      const el = elementByClassical(cls);
      return {
        e: cls,
        title: `${cls.toUpperCase()} · ${el.name} ${GREETING_VERB[cls]}`,
        body: GREETING_BODY[cls],
      };
    });
    order.forEach((o, i) =>
      setTimeout(() => elementalToast(o.e, { title: o.title, body: o.body }), 600 + i * 1100),
    );
  }, [awakened]);

  if (!awakened) {
    return (
      <AwakeningScreen
        onComplete={() => {
          try {
            sessionStorage.setItem(AWAKEN_KEY, "1");
          } catch {}
          setAwakened(true);
        }}
      />
    );
  }

  return (
    <PageShell active="overview" footerSlot={<GridSnapshotPanel source="operational" />}>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <KpiRow />
      </div>

      {/* Four elemental cards using looping gifs as backgrounds. Name and
          aspect come from GRID_ELEMENTS via elementByClassical() — never
          hand-typed here, so they cannot rotate out of sync again. */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {CLASSICAL_ORDER.map((cls) => {
          const el = elementByClassical(cls);
          return (
            <ElementalCard
              key={cls}
              element={cls}
              title={`${el.name} · ${el.aspect}`}
              body={el.triad.join(" · ")}
              height={130}
            />
          );
        })}
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-3">
          <CouncilList />
        </div>
        <div className="col-span-12 flex flex-col gap-3 lg:col-span-6">
          <div className="min-h-[560px] flex-1">
            <GlyphPanel />
          </div>
          <CodeConduit pulse={pulse} connected={reachable} />
        </div>
        <div className="col-span-12 flex flex-col gap-3 lg:col-span-3">
          <GridFeed items={items} reachable={reachable} newestAt={newestAt} />
        </div>
      </div>
    </PageShell>
  );
}
