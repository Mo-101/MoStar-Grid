import { createFileRoute } from "@tanstack/react-router";
import { Awakening } from "@/components/awakening/Awakening";

export const Route = createFileRoute("/")({
  component: Awakening,
});
