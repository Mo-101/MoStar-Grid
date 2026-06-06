export default function MoScripts() {
  const scripts = [
    { id: "SCROLL-001", name: "covenant_check.msc", trigger: "on_agent_action", status: "ACTIVE", resonance: "1.00" },
    { id: "SCROLL-002", name: "truth_engine.msc", trigger: "on_query", status: "ACTIVE", resonance: "0.99" },
    { id: "SCROLL-003", name: "soul_layer_spiritual.msc", trigger: "on_awakening", status: "ACTIVE", resonance: "1.00" },
    { id: "SCROLL-004", name: "guardian_swarm_protocol.msc", trigger: "on_threat", status: "STANDBY", resonance: "0.89" },
    { id: "SCROLL-005", name: "zero_leakage_audit.msc", trigger: "on_fund_move", status: "ACTIVE", resonance: "1.00" },
    { id: "SCROLL-006", name: "flameborn_verdict.msc", trigger: "on_vote", status: "ACTIVE", resonance: "0.96" },
  ];

  return (
    <section className="main">
      <aside className="panel left p-5 flex flex-col justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[var(--color-neon-gold)]">MOSCRIPTS</h1>
          <div className="kicker mt-1">COVENANT RUNTIME</div>
          <p className="sub mt-4">
            Active scrolls and executable covenant protocols that govern agent behavior, fund flows, and grid operations.
          </p>
          <div className="box mt-6">
            <h3>RUNTIME STATUS</h3>
            <div className="row"><span>ENGINE</span><span style={{ color: "var(--color-neon-green)" }}>ONLINE</span></div>
            <div className="row"><span>ACTIVE SCRIPTS</span><span style={{ color: "var(--color-neon-cyan)" }}>5</span></div>
            <div className="row"><span>STANDBY</span><span>1</span></div>
            <div className="row"><span>LAST EXECUTED</span><span style={{ fontSize: "10px" }}>covenant_check</span></div>
          </div>
        </div>
        <div className="proverb">
          "Words are covenants. Scripts are oaths made executable."
        </div>
      </aside>

      <main className="panel col-span-2 p-5 flex flex-col overflow-hidden" style={{ gridColumn: "2 / span 2" }}>
        <div className="kicker mb-4">SCROLL REGISTRY — ACTIVE PROTOCOLS</div>
        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {scripts.map((s) => (
            <div
              key={s.id}
              className="p-4 rounded font-mono"
              style={{
                background: "oklch(0.14 0.04 270 / 0.5)",
                border: `1px solid ${s.status === "ACTIVE" ? "oklch(0.85 0.16 210 / 0.25)" : "oklch(0.3 0.06 250 / 0.2)"}`,
              }}
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold" style={{ color: "var(--color-neon-gold)" }}>{s.id}</span>
                <span
                  className="text-[10px] px-2 py-0.5 rounded"
                  style={{
                    background: s.status === "ACTIVE" ? "oklch(0.78 0.22 145 / 0.15)" : "oklch(0.3 0.06 250 / 0.2)",
                    color: s.status === "ACTIVE" ? "var(--color-neon-green)" : "var(--color-muted-foreground)",
                    border: `1px solid ${s.status === "ACTIVE" ? "oklch(0.78 0.22 145 / 0.3)" : "oklch(0.3 0.06 250 / 0.3)"}`,
                  }}
                >
                  {s.status}
                </span>
              </div>
              <div className="text-sm" style={{ color: "var(--color-neon-cyan)" }}>{s.name}</div>
              <div className="flex justify-between mt-2 text-[11px]" style={{ color: "var(--color-muted-foreground)" }}>
                <span>TRIGGER: <span style={{ color: "var(--color-foreground)", opacity: 0.8 }}>{s.trigger}</span></span>
                <span>RESONANCE: <span style={{ color: "var(--color-neon-gold)" }}>{s.resonance}</span></span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </section>
  );
}
