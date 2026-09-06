import { createFileRoute, useRouterState } from "@tanstack/react-router";
import { PageShell } from "@/components/grid/parts";
import { Glyph } from "@/components/grid/glyph";

export const Route = createFileRoute("/$")({
  component: ComingSoon,
});

const TITLES: Record<string, { id: string; title: string; sub: string }> = {
  council:   { id: "council",   title: "COUNCIL CHAMBER",  sub: "11 Agents · Guardians of the Grid" },
  conduit:   { id: "conduit",   title: "CODE CONDUIT",     sub: "All Glyphs · All Layers · All Time" },
  analytics: { id: "analytics", title: "GRID INTELLIGENCE", sub: "Patterns · Insights · Forecasts" },
  settings:  { id: "settings",  title: "GRID CONTROL",     sub: "Configure the Covenant" },
};

function ComingSoon() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const slug = pathname.replace(/^\//, "").split("/")[0];
  const meta = TITLES[slug] ?? { id: "overview", title: "NOT FOUND", sub: pathname };

  return (
    <PageShell active={meta.id}>
      <div className="panel flex flex-1 flex-col items-center justify-center gap-4 p-12">
        <div className="grid h-24 w-24 place-items-center rounded-full border border-[var(--color-neon-gold)]/40 shadow-[0_0_40px_var(--color-neon-gold)]">
          <Glyph name="covenant" size={56} />
        </div>
        <div className="text-center">
          <div className="text-2xl tracking-[0.32em] neon-text-gold">{meta.title}</div>
          <div className="mt-2 text-[11px] tracking-[0.28em] text-muted-foreground">{meta.sub}</div>
          <div className="mt-6 text-xs tracking-[0.25em] neon-text-cyan">CHAMBER AWAKENING · COMING SOON</div>
        </div>
      </div>
    </PageShell>
  );
}
