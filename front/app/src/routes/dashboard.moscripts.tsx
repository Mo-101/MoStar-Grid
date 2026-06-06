import { createFileRoute } from "@tanstack/react-router";
import MoScripts from "@/pages/06-MoScripts";

export const Route = createFileRoute("/dashboard/moscripts")({
  component: MoScripts,
});
