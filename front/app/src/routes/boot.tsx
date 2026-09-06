import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AwakeningScreen } from "@/components/grid/awakening";

export const Route = createFileRoute("/boot")({
  head: () => ({
    meta: [{ title: "MoStar GRID — Awakening" }],
  }),
  component: BootRoute,
});

function BootRoute() {
  const navigate = useNavigate();

  return (
    <AwakeningScreen
      onComplete={() => {
        try {
          sessionStorage.setItem("mostar.grid.awakened", "1");
        } catch {
          // Storage is optional; the dedicated route remains replayable.
        }
        void navigate({ to: "/" });
      }}
    />
  );
}
