import { createFileRoute } from "@tanstack/react-router";
import MindGraph from "@/pages/05-MindGraph";

export const Route = createFileRoute("/dashboard/mind-graph")({
  component: MindGraph,
});
