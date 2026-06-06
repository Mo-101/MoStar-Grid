import { createFileRoute } from "@tanstack/react-router";
import Watchtower from "@/pages/04-Watchtower";

export const Route = createFileRoute("/dashboard/watchtower")({
  component: Watchtower,
});
