import { createFileRoute } from "@tanstack/react-router";
import { AfricaCommand } from "@/components/grid/africa-command";
import { GridSnapshotPanel } from "@/components/grid/grid-snapshot";
import { PageShell } from "@/components/grid/parts";

export const Route = createFileRoute("/continent-optics")({
  head: () => ({
    meta: [
      { title: "Continent Optics · MoStar GRID" },
      {
        name: "description",
        content: "Africa-wide weather, health, and sovereignty sensing with source provenance.",
      },
    ],
  }),
  component: ContinentOptics,
});

function ContinentOptics() {
  return (
    <PageShell active="continent-optics" footerSlot={<GridSnapshotPanel source="continent" />}>
      <AfricaCommand />
    </PageShell>
  );
}
