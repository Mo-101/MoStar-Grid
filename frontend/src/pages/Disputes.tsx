import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import GlyphCanvas from "@/components/GlyphCanvas";

type Severity = "low" | "medium" | "high" | "critical";

interface Dispute {
  id: string;
  scrollId: string;
  raisedBy: string;
  reason: string;
  severity: Severity;
  evidenceCount: number;
  status: "open" | "review" | "resolved";
  ts: string;
}

// [PLACEHOLDER_API_DISPUTES] — replace with /api/disputes
const SEED: Dispute[] = [
  { id: "DSP-091", scrollId: "SCR-0419", raisedBy: "Ledger · Adichie", reason: "Afim resonance below threshold (0.62 < 0.65)", severity: "high", evidenceCount: 4, status: "open", ts: "2m ago" },
  { id: "DSP-090", scrollId: "SCR-0411", raisedBy: "TruthEngine", reason: "JCS hash mismatch on attestation", severity: "critical", evidenceCount: 7, status: "review", ts: "18m ago" },
  { id: "DSP-089", scrollId: "SCR-0405", raisedBy: "Architect Proxy", reason: "Federation handshake replay detected", severity: "medium", evidenceCount: 2, status: "resolved", ts: "1h ago" },
  { id: "DSP-088", scrollId: "SCR-0398", raisedBy: "Ledger · Soyinka", reason: "Memory compaction drift > 0.04", severity: "low", evidenceCount: 1, status: "resolved", ts: "3h ago" },
];

const SEV: Record<Severity, string> = {
  low: "bg-muted/40 text-muted-foreground border-border",
  medium: "bg-secondary/10 text-secondary border-secondary/40",
  high: "bg-primary/10 text-primary border-primary/40",
  critical: "bg-destructive/10 text-destructive border-destructive/50",
};

const Disputes = () => {
  const [selected, setSelected] = useState<Dispute>(SEED[0]);

  useEffect(() => {
    document.title = "Disputes & Evidence — MoStar Grid";
  }, []);

  return (
    <main className="min-h-screen bg-background relative">
      <GlyphCanvas />
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">
        <header className="flex items-center justify-between mb-10 flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-xs font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground transition-smooth">
              ← Dashboard
            </Link>
            <div className="w-px h-6 bg-border" />
            <div>
              <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground mb-1">TruthEngine Chamber</p>
              <h1 className="text-3xl font-black tracking-tight">Disputes & Evidence</h1>
            </div>
          </div>
          <nav className="flex gap-2 text-xs font-mono">
            <Link to="/proposals" className="px-3 py-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:border-foreground/40 transition-smooth uppercase tracking-wider">
              ← Proposals
            </Link>
          </nav>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-6">
          {/* List */}
          <div className="bg-card/60 backdrop-blur-sm border border-border rounded-2xl overflow-hidden shadow-elegant">
            <div className="px-5 py-3 border-b border-border flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">Active Disputes</span>
              <span className="text-[10px] font-mono text-primary">{SEED.filter((d) => d.status !== "resolved").length} open</span>
            </div>
            <ul>
              {SEED.map((d) => {
                const active = d.id === selected.id;
                return (
                  <li key={d.id}>
                    <button
                      onClick={() => setSelected(d)}
                      className={`w-full text-left px-5 py-4 border-b border-border/40 last:border-0 transition-smooth ${
                        active ? "bg-primary/10" : "hover:bg-foreground/5"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono text-xs text-primary">{d.id}</span>
                        <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border ${SEV[d.severity]}`}>
                          {d.severity}
                        </span>
                      </div>
                      <p className="text-sm font-semibold mb-1 truncate">{d.reason}</p>
                      <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
                        <span>{d.raisedBy}</span>
                        <span>{d.ts}</span>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Detail / Evidence */}
          <div className="bg-card/60 backdrop-blur-sm border border-border rounded-2xl p-6 shadow-elegant">
            <div className="flex items-start justify-between mb-6">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground mb-1">
                  Dispute {selected.id} · against {selected.scrollId}
                </p>
                <h2 className="text-2xl font-black tracking-tight">{selected.reason}</h2>
              </div>
              <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded border ${SEV[selected.severity]}`}>
                {selected.severity}
              </span>
            </div>

            <dl className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <dt className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1">Raised by</dt>
                <dd className="text-sm font-semibold">{selected.raisedBy}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1">Status</dt>
                <dd className="text-sm font-semibold capitalize">{selected.status}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1">Evidence items</dt>
                <dd className="text-sm font-semibold">{selected.evidenceCount}</dd>
              </div>
              <div>
                <dt className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1">Filed</dt>
                <dd className="text-sm font-semibold">{selected.ts}</dd>
              </div>
            </dl>

            <div className="mb-6">
              <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground mb-3">Evidence Chain</p>
              {/* [PLACEHOLDER_API_EVIDENCE_CHAIN] */}
              <ol className="space-y-2">
                {Array.from({ length: selected.evidenceCount }).map((_, i) => (
                  <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-background/40 border border-border">
                    <span className="text-[10px] font-mono text-primary mt-0.5">#{String(i + 1).padStart(3, "0")}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm">JCS attestation snapshot · cluster nairobi-α</p>
                      <p className="text-[10px] font-mono text-muted-foreground">hash 7b21…99ae · signed by TruthEngine</p>
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground">{i + 1}m</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="flex gap-3">
              <button className="flex-1 bg-gradient-primary text-primary-foreground font-black py-3 rounded-xl uppercase tracking-[0.15em] text-xs shadow-glow-orange hover:opacity-90 transition-smooth">
                Uphold
              </button>
              <button className="flex-1 bg-gradient-red text-secondary-foreground font-black py-3 rounded-xl uppercase tracking-[0.15em] text-xs shadow-glow-red hover:opacity-90 transition-smooth">
                Dismiss
              </button>
              <button className="flex-1 border border-border text-foreground font-black py-3 rounded-xl uppercase tracking-[0.15em] text-xs hover:bg-foreground/5 transition-smooth">
                Escalate
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};

export default Disputes;
