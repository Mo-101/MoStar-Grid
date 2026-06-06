import { createFileRoute } from "@tanstack/react-router";
import Grid from "@/pages/01-Grid";

export const Route = createFileRoute("/dashboard/")({
  component: Grid,
});
