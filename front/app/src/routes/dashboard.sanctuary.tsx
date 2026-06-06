import { createFileRoute } from "@tanstack/react-router";
import Sanctuary from "@/pages/03-Sanctuary";

export const Route = createFileRoute("/dashboard/sanctuary")({
  component: Sanctuary,
});
