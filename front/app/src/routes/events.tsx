import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageShell, QuickCommands } from "@/components/grid/parts";
import { Glyph } from "@/components/grid/glyph";

export const Route = createFileRoute("/events")({
  head: () => ({
    meta: [
      { title: "MoStar GRID — Events River" },
      { name: "description", content: "Real-time flow of the MoStar GRID covenant events." },
    ],
  }),
  component: EventsPage,
});

type RiverEvent = {
  id: string; time: string; title: string; cat: string; impact: "HIGH" | "MED" | "LOW";
  color: string; desc: string; side: "left" | "right"; y: number;
};

const EVENTS: RiverEvent[] = [
  { id: "MSG-01",     time: "05:42:18", title: "MSG-01 SEALED",         cat: "ALIGNMENT",  impact: "HIGH", color: "neon-gold",   desc: "Alignment verified across all covenant protocols.", side: "right", y: 18 },
  { id: "DCX-77",     time: "05:41:10", title: "DEEPCAL UTTERED",       cat: "UTTERANCE",  impact: "HIGH", color: "neon-cyan",   desc: "Pattern analysis dispatched to the council.",        side: "left",  y: 36 },
  { id: "RAD-12",     time: "05:40:01", title: "RAD-X-FLB PATTERN",     cat: "SYSTEM",     impact: "MED",  color: "neon-blue",   desc: "Irregularity flagged in observation lattice.",       side: "right", y: 54 },
  { id: "THR-09",     time: "05:38:02", title: "THRONE LOCK SEALED",    cat: "SYSTEM",     impact: "HIGH", color: "neon-purple", desc: "Vault integrity confirmed; ward protocol active.",   side: "left",  y: 72 },
];

function EventsPage() {
  const [sel, setSel] = useState(EVENTS[0]);
  return (
    <PageShell active="events">
      <div className="grid flex-1 grid-cols-12 gap-3">
        {/* LEFT */}
        <div className="col-span-12 flex flex-col gap-3 lg:col-span-3">
          <Panel title="EVENT STREAM">
            {[
              ["TOTAL EVENTS", "7,842"],
              ["TODAY", "243"],
              ["LAST 24H", "1,186"],
              ["HIGH IMPACT", "34"],
              ["SYNC INTEGRITY", "100%"],
            ].map(([k, v]) => (
              <div key={k} className="border-b border-white/5 py-2">
                <div className="text-[10px] tracking-[0.2em] text-muted-foreground">{k}</div>
                <div className="mt-1 text-xl tabular-nums neon-text-cyan">{v}</div>
              </div>
            ))}
          </Panel>
          <Panel title="EVENT CATEGORIES">
            {[
              ["UTTERANCES", "2,143", "neon-cyan"],
              ["SYSTEM", "1,672", "neon-blue"],
              ["MOMENTS", "1,248", "neon-purple"],
              ["ALIGNMENTS", "892", "neon-gold"],
              ["EXTERNAL", "1,887", "neon-green"],
            ].map(([k, v, c]) => (
              <div key={k} className="flex items-center justify-between border-b border-white/5 py-1.5 text-xs">
                <span className="flex items-center gap-2">
                  <span className="h-2 w-2 rotate-45" style={{ background: `var(--color-${c})`, boxShadow: `0 0 8px var(--color-${c})` }} />
                  <span className="tracking-[0.15em] text-foreground/85">{k}</span>
                </span>
                <span className="tabular-nums neon-text-cyan">{v}</span>
              </div>
            ))}
          </Panel>
          <Panel title="FILTERS">
            {["SHOW HIGH IMPACT","SHOW MOMENTS","SHOW SYSTEM"].map((l, i) => (
              <div key={l} className="flex items-center justify-between border-b border-white/5 py-2 text-xs">
                <span className="tracking-[0.15em] text-foreground/85">{l}</span>
                <span className={`relative inline-block h-4 w-8 rounded-full border ${i !== 2 ? "border-[var(--color-neon-cyan)]/60 bg-[oklch(0.25_0.10_240/0.6)]" : "border-white/15 bg-white/5"}`}>
                  <span className={`absolute top-0.5 h-2.5 w-2.5 rounded-full ${i !== 2 ? "left-4 bg-[var(--color-neon-cyan)] shadow-[0_0_8px_var(--color-neon-cyan)]" : "left-0.5 bg-white/40"}`} />
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between border-b border-white/5 py-2 text-xs">
              <span className="tracking-[0.15em] text-foreground/85">TIME RANGE</span>
              <span className="neon-text-cyan">Last 24h ⌄</span>
            </div>
            <button className="mt-3 w-full rounded border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.18_0.06_240/0.5)] py-2 text-[11px] tracking-[0.18em] neon-text-cyan">
              RESET FILTERS
            </button>
          </Panel>
        </div>

        {/* RIVER */}
        <div className="col-span-12 lg:col-span-6">
          <div className="panel relative h-full min-h-[680px] overflow-hidden">
            <div className="pointer-events-none absolute left-0 right-0 top-3 z-20 text-center">
              <div className="tracking-[0.32em] neon-text-gold text-lg">EVENTS RIVER</div>
              <div className="mt-1 text-[11px] tracking-[0.25em] text-muted-foreground">REAL-TIME FLOW OF THE GRID</div>
            </div>

            <div className="absolute right-4 top-3 z-30 flex gap-2">
              <button className="rounded border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.08_0.05_240/0.7)] px-3 py-1.5 text-[10px] tracking-[0.2em] neon-text-cyan">‖</button>
              <button className="rounded border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.08_0.05_240/0.7)] px-3 py-1.5 text-[10px] tracking-[0.2em] neon-text-cyan">AUTO SCROLL</button>
            </div>

            {/* River spine */}
            <div className="absolute left-1/2 top-[90px] bottom-12 -translate-x-1/2 w-[6px] rounded"
              style={{
                background: "linear-gradient(180deg, transparent, var(--color-neon-gold), rgba(255,255,255,.2), var(--color-neon-gold), transparent)",
                boxShadow: "0 0 35px var(--color-neon-gold)",
              }}
            />

            <div className="absolute left-1/2 top-[68px] -translate-x-1/2 z-20 rounded border border-[var(--color-neon-gold)] bg-black/60 px-5 py-1.5 text-[11px] tracking-[0.22em] neon-text-gold shadow-[0_0_18px_var(--color-neon-gold)]">
              PRESENT
            </div>
            <div className="absolute left-1/2 bottom-2 -translate-x-1/2 z-20 rounded border border-[var(--color-neon-cyan)] bg-black/60 px-5 py-1.5 text-[11px] tracking-[0.22em] neon-text-cyan shadow-[0_0_18px_var(--color-neon-cyan)]">
              PAST
            </div>

            {EVENTS.map((e) => (
              <div key={e.id}>
                <span
                  className="absolute left-1/2 z-30 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white"
                  style={{
                    top: `${e.y}%`,
                    background: `var(--color-${e.color})`,
                    boxShadow: `0 0 18px var(--color-${e.color}), 0 0 34px var(--color-${e.color})`,
                  }}
                />
                <button
                  onClick={() => setSel(e)}
                  className="absolute z-20 w-[280px] rounded border p-3 pl-16 text-left transition hover:scale-[1.02]"
                  style={{
                    top: `calc(${e.y}% - 40px)`,
                    [e.side]: "8%",
                    borderColor: `var(--color-${e.color})`,
                    background: `linear-gradient(135deg, color-mix(in oklab, var(--color-${e.color}) 18%, transparent), rgba(0,0,0,.7))`,
                    boxShadow: `0 0 22px color-mix(in oklab, var(--color-${e.color}) 50%, transparent)`,
                  } as React.CSSProperties}
                >
                  <span
                    className="absolute left-3 top-3 grid h-9 w-9 place-items-center rounded-full border bg-black/60"
                    style={{ borderColor: `var(--color-${e.color})`, boxShadow: `0 0 14px var(--color-${e.color})` }}
                  >
                    <Glyph name="spark" size={20} glow={`var(--color-${e.color})`} />
                  </span>
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-xs tracking-[0.1em]" style={{ color: `var(--color-${e.color})` }}>{e.title}</div>
                    <span className="rounded border px-1.5 py-0.5 text-[9px]" style={{ color: `var(--color-${e.color})`, borderColor: `var(--color-${e.color})` }}>{e.impact}</span>
                  </div>
                  <div className="mt-1 text-[11px] text-foreground/80">{e.desc}</div>
                  <div className="mt-1 text-[10px] text-muted-foreground tabular-nums">{e.time} UTC</div>
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT */}
        <div className="col-span-12 flex flex-col gap-3 lg:col-span-3">
          <Panel title="SELECTED EVENT">
            <div className="text-xl tracking-[0.08em] neon-text-gold">{sel.title}</div>
            <div className="mt-1 flex gap-2 text-[10px] tracking-[0.18em]">
              <span style={{ color: `var(--color-${sel.color})` }}>{sel.cat}</span>
              <span className="text-muted-foreground">·</span>
              <span className="neon-text-cyan">{sel.impact} IMPACT</span>
            </div>
            <div className="mt-3 flex h-24 items-center justify-center rounded border border-[var(--color-neon-gold)]/30 bg-[oklch(0.22_0.10_80/0.18)]">
              <Glyph name="spark" size={56} glow={`var(--color-${sel.color})`} />
            </div>
            <div className="mt-3 space-y-1.5 text-[11px]">
              {[
                ["TIME", `${sel.time} UTC`],
                ["DATE", "June 4, 2026"],
                ["SOURCE", "MO"],
                ["TYPE", sel.cat],
                ["ROUTING", "COVENANT → ALL"],
                ["RELATED MOMENTS", "12"],
                ["CONNECTED NODES", "18"],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-white/5 py-1">
                  <span className="text-muted-foreground tracking-wider">{k}</span>
                  <span className="neon-text-cyan">{v}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[11px] leading-relaxed text-foreground/80">{sel.desc}</p>
            <button className="mt-3 w-full rounded border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.18_0.06_240/0.5)] py-2 text-[11px] tracking-[0.18em] neon-text-cyan">
              VIEW FULL DETAILS ↗
            </button>
          </Panel>
          <Panel title="EVENT IMPACT">
            <div className="grid place-items-center py-3">
              <div
                className="h-32 w-32"
                style={{
                  clipPath: "polygon(50% 0,93% 25%,93% 75%,50% 100%,7% 75%,7% 25%)",
                  background: "conic-gradient(from 0deg, var(--color-neon-gold), var(--color-neon-cyan), var(--color-neon-gold))",
                  boxShadow: "0 0 32px var(--color-neon-gold)",
                }}
              />
            </div>
          </Panel>
        </div>
      </div>

      {/* BOTTOM */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-4 xl:grid-cols-5">
        <Panel title="HIGH IMPACT EVENTS">
          {EVENTS.map((e) => (
            <div key={e.id} className="flex gap-3 py-1 text-[11px]">
              <span className="tabular-nums text-muted-foreground">{e.time}</span>
              <span className="flex-1 text-foreground/85">{e.title}</span>
              <span style={{ color: `var(--color-${e.color})` }}>{e.cat}</span>
            </div>
          ))}
        </Panel>
        <Panel title="EVENT TREND (24H)">
          <svg viewBox="0 0 200 80" className="mt-1 h-24 w-full">
            <polyline
              fill="none" stroke="var(--color-neon-cyan)" strokeWidth="1.5"
              points="0,60 20,52 40,55 60,40 80,42 100,28 120,32 140,18 160,24 180,12 200,16"
              style={{ filter: "drop-shadow(0 0 4px var(--color-neon-cyan))" }}
            />
            <polyline
              fill="none" stroke="var(--color-neon-gold)" strokeWidth="1" opacity="0.7"
              points="0,68 20,64 40,58 60,60 80,50 100,52 120,42 140,46 160,34 180,30 200,26"
            />
          </svg>
        </Panel>
        <Panel title="CATEGORY FLOW">
          {[
            ["UTTERANCES", 27, "neon-cyan"],
            ["SYSTEM", 21, "neon-blue"],
            ["MOMENTS", 16, "neon-purple"],
            ["ALIGNMENTS", 11, "neon-gold"],
            ["EXTERNAL", 25, "neon-green"],
          ].map(([k, v, c]) => (
            <div key={k as string} className="grid grid-cols-[90px_1fr_36px] items-center gap-2 py-1 text-[11px]">
              <span className="tracking-[0.15em] text-foreground/85">{k}</span>
              <span className="h-1 rounded bg-white/5"><span className="block h-full rounded" style={{ width: `${(v as number) * 3}%`, background: `var(--color-${c})`, boxShadow: `0 0 8px var(--color-${c})` }} /></span>
              <span className="text-right tabular-nums neon-text-cyan">{v}%</span>
            </div>
          ))}
        </Panel>
        <Panel title="LIVE INDICATORS">
          {["EVENT STREAM","NEO4J SYNC","COUNCIL FEED","CONDUIT LINKS","MEMORY WRITE"].map((l) => (
            <div key={l} className="flex items-center justify-between py-1 text-[11px]">
              <span className="text-foreground/85">▸ {l}</span>
              <span className="neon-text-green">● LIVE</span>
            </div>
          ))}
        </Panel>
        <QuickCommands />
      </div>
    </PageShell>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="panel p-4">
      <div className="mb-3 text-[11px] tracking-[0.22em] neon-text-cyan">{title}</div>
      {children}
    </div>
  );
}
