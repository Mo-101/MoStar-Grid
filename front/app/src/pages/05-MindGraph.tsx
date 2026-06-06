import { useDashboard } from "@/routes/dashboard";

export default function MindGraph() {
  const { census } = useDashboard();

  return (
    <section className="main">
      <aside className="panel left p-5 flex flex-col justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[var(--gold)]">MIND GRAPH</h1>
          <div className="kicker mt-1">KNOWLEDGE MATRIX</div>
          <p className="text-sm text-foreground/80 leading-relaxed mt-4">
            The primary cognitive substrate of MoStar Grid. Shows semantic connections and entities currently synchronized in Nairobi-α.
          </p>
          <div className="box mt-6">
            <h3 className="text-[var(--cyan)] font-semibold text-xs tracking-wider">GRAPH METRICS</h3>
            <div className="row"><span>NODES</span><span>{census?.nodes || 152224}</span></div>
            <div className="row"><span>RELATIONSHIPS</span><span>{census?.relationships || 21144}</span></div>
            <div className="row"><span>EVENTS</span><span>{census?.events || 2582}</span></div>
          </div>
        </div>
        <div className="proverb text-xs text-[var(--gold)]/80 p-3 border-l-2 border-[var(--gold)] bg-[var(--gold)]/5">
          "A network grows stable by the strength of its connections."
        </div>
      </aside>
      <main className="panel col-span-2 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-sm tracking-wider text-[var(--cyan)] mb-4">SPINNING SEMANTIC REGISTRY</div>
          <div className="relative h-96 w-96 mx-auto border border-dashed border-[var(--cyan)]/20 rounded-full flex items-center justify-center animate-spin-slow">
            <div className="absolute inset-8 border border-dashed border-[var(--gold)]/20 rounded-full flex items-center justify-center">
              <div className="absolute inset-12 border border-solid border-[var(--purple)]/30 rounded-full flex items-center justify-center">
                <div className="h-16 w-16 border-2 border-[var(--cyan)] flex items-center justify-center shadow-[0_0_30px_var(--cyan)] rounded-full">
                  <div className="crest"></div>
                </div>
              </div>
            </div>
            <div className="absolute top-4 left-1/2 -translate-x-1/2 h-4 w-4 bg-[var(--gold)] rounded-full animate-pulse shadow-[0_0_10px_var(--gold)]"></div>
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 h-4 w-4 bg-[var(--green)] rounded-full animate-pulse shadow-[0_0_10px_var(--green)]"></div>
            <div className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 bg-[var(--cyan)] rounded-full animate-pulse shadow-[0_0_10px_var(--cyan)]"></div>
            <div className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 bg-[var(--purple)] rounded-full animate-pulse shadow-[0_0_10px_var(--purple)]"></div>
          </div>
          <div className="text-xs text-foreground/60 mt-6 tracking-widest font-mono">
            SEMANTIC MAPPING PIPELINE SECURED
          </div>
        </div>
      </main>
    </section>
  );
}
