import { createFileRoute } from "@tanstack/react-router";
import Council from "@/pages/02-Council";

export const Route = createFileRoute("/dashboard/council")({
  component: Council,
});
