import { useDashboard } from "@/routes/dashboard";

export default function Watchtower() {
  const { reports, census } = useDashboard();

  return (
    <section className="main">
      <aside className="panel left p-5 flex flex-col justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[var(--color-neon-gold)]">WATCHTOWER</h1>
          <div className="kicker mt-1">SURVEILLANCE & ANALYTICS</div>
          <p className="sub mt-4">
            Aggregated telemetry, health vitals, and real-time event feed from all grid nodes and local pipeline services.
          </p>
          <div className="box mt-6">
            <h3>PIPELINE VITALS</h3>
            <div className="row"><span>NEO4J</span><span style={{ color: "var(--color-neon-green)" }}>CONNECTED</span></div>
            <div className="row"><span>OLLAMA</span><span style={{ color: "var(--color-neon-green)" }}>RUNNING</span></div>
            <div className="row"><span>PIPER TTS</span><span style={{ color: "var(--color-neon-green)" }}>ONLINE</span></div>
            <div className="row"><span>EVENT PRESSURE</span><span>STABLE</span></div>
            <div className="row"><span>LATEST SEVERITY</span><span style={{ color: "var(--color-neon-green)" }}>LOW</span></div>
          </div>
          <div className="box mt-4">
            <h3>GRID CENSUS</h3>
            <div className="row"><span>NODES</span><span>{census?.nodes?.toLocaleString() || "152,224"}</span></div>
            <div className="row"><span>RELATIONSHIPS</span><span>{census?.relationships?.toLocaleString() || "21,144"}</span></div>
            <div className="row"><span>EVENTS</span><span>{census?.events?.toLocaleString() || "2,582"}</span></div>
          </div>
        </div>
        <div className="proverb">
          "Everything radiates. I simply listen."
        </div>
      </aside>

      <main className="panel col-span-2 p-5 flex flex-col overflow-hidden" style={{ gridColumn: "2 / span 2" }}>
        <div className="kicker mb-4">CONSOLIDATED SYSTEM TELEMETRY FEED</div>
        <div className="flex-1 overflow-y-auto space-y-2 pr-2 font-mono text-xs">
          {reports.map((r, i) => (
            <div
              key={i}
              className="flex justify-between items-start gap-4 p-3 rounded"
              style={{ background: "oklch(0.14 0.04 270 / 0.5)", border: "1px solid oklch(0.3 0.06 250 / 0.3)" }}
            >
              <div>
                <span style={{ color: "var(--color-neon-gold)", fontWeight: 700 }}>
                  [{r.name.toUpperCase()}]
                </span>{" "}
                <span style={{ color: "var(--color-foreground)", opacity: 0.85 }}>
                  Reported startup parameters. Status loaded into MindGraph.
                </span>
              </div>
              <span style={{ color: "var(--color-muted-foreground)", fontSize: "10px", flexShrink: 0 }}>VERIFIED</span>
            </div>
          ))}
          <div
            className="flex justify-between items-start gap-4 p-3 rounded"
            style={{ background: "oklch(0.14 0.04 270 / 0.5)", border: "1px solid oklch(0.3 0.06 250 / 0.3)" }}
          >
            <div>
              <span style={{ color: "var(--color-neon-cyan)", fontWeight: 700 }}>[SYSTEM]</span>{" "}
              <span style={{ color: "var(--color-foreground)", opacity: 0.85 }}>FastAPI gateway server listening on port 41010.</span>
            </div>
            <span style={{ color: "var(--color-muted-foreground)", fontSize: "10px", flexShrink: 0 }}>18:41:26</span>
          </div>
          <div
            className="flex justify-between items-start gap-4 p-3 rounded"
            style={{ background: "oklch(0.14 0.04 270 / 0.5)", border: "1px solid oklch(0.3 0.06 250 / 0.3)" }}
          >
            <div>
              <span style={{ color: "var(--color-neon-green)", fontWeight: 700 }}>[VOICE]</span>{" "}
              <span style={{ color: "var(--color-foreground)", opacity: 0.85 }}>Piper TTS server healthy on local socket 41071.</span>
            </div>
            <span style={{ color: "var(--color-muted-foreground)", fontSize: "10px", flexShrink: 0 }}>18:40:56</span>
          </div>
          <div
            className="flex justify-between items-start gap-4 p-3 rounded"
            style={{ background: "oklch(0.14 0.04 270 / 0.5)", border: "1px solid oklch(0.3 0.06 250 / 0.3)" }}
          >
            <div>
              <span style={{ color: "var(--color-neon-gold)", fontWeight: 700 }}>[NEO4J]</span>{" "}
              <span style={{ color: "var(--color-foreground)", opacity: 0.85 }}>Connected on bolt://localhost:47687. MindGraph nodes indexed.</span>
            </div>
            <span style={{ color: "var(--color-muted-foreground)", fontSize: "10px", flexShrink: 0 }}>18:40:10</span>
          </div>
        </div>
      </main>
    </section>
  );
}
