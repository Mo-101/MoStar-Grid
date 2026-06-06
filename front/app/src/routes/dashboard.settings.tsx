import { createFileRoute } from "@tanstack/react-router";
import Settings from "@/pages/07-Settings";

export const Route = createFileRoute("/dashboard/settings")({
  component: Settings,
});
