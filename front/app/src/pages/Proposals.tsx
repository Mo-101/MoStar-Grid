import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import GlyphCanvas from "@/components/GlyphCanvas";
import { MoCon, ELEMENT_ICON, type IconKey } from "@/components/MoCon";

type ProposalStatus = "draft" | "sealed" | "attested" | "vetoed";

interface Proposal {
  id: string;
  title: string;
  author: string;
  cluster: "nairobi-α" | "kampala-β";
  element: "🜂" | "🜄" | "🜁" | "🜃";
  resonance: number;
  status: ProposalStatus;
  hash: string;
  ts: string;
}

const SEED: Proposal[] = [
  { id: "SCR-0421", title: "Seal Federation Handshake v4.0a", author: "Flame Architect", cluster: "nairobi-α", element: "🜂", resonance: 0.91, status: "sealed", hash: "a83f…cd12", ts: "12s ago" },
  { id: "SCR-0420", title: "Mmọng Memory Compaction Cycle", author: "Ledger · Achebe", cluster: "kampala-β", element: "🜄", resonance: 0.78, status: "attested", hash: "7b21…99ae", ts: "1m ago" },
  { id: "SCR-0419", title: "Afim Voice Recalibration", author: "Ledger · Nyong'o", cluster: "nairobi-α", element: "🜁", resonance: 0.62, status: "vetoed", hash: "5e44…01bb", ts: "3m ago" },
  { id: "SCR-0418", title: "Isong Weight Reallocation", author: "Architect Proxy", cluster: "kampala-β", element: "🜃", resonance: 0.84, status: "sealed", hash: "c012…77df", ts: "7m ago" },
  { id: "SCR-0417", title: "Truth Threshold Audit — Q3", author: "TruthEngine", cluster: "nairobi-α", element: "🜂", resonance: 0.73, status: "draft", hash: "—", ts: "14m ago" },
];

const STATUS_STYLES: Record<ProposalStatus, string> = {
  draft: "bg-muted/40 text-muted-foreground border-border",
  sealed: "bg-primary/10 text-primary border-primary/40",
  attested: "bg-secondary/10 text-secondary border-secondary/40",
  vetoed: "bg-destructive/10 text-destructive border-destructive/40",
};

interface ProposalsProps {
  role?: string;
}

const Proposals = ({ role = "architect" }: ProposalsProps) => {
  const [filter, setFilter] = useState<"all" | ProposalStatus>("all");
  const [proposals] = useState<Proposal[]>(SEED);

  useEffect(() => {
    document.title = "Proposals & Scrolls — MoStar Grid";
  }, []);

  const filtered = filter === "all" ? proposals : proposals.filter((p) => p.status === filter);

  return (
    <main className="min-h-screen bg-background relative">
      <GlyphCanvas />
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <header className="flex items-center justify-between mb-10 flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-xs font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground transition-smooth">
              ← Dashboard
            </Link>
            <div className="w-px h-6 bg-border" />
            <div>
              <p className="text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground mb-1">Federation Scrolls</p>
              <h1 className="text-3xl font-black tracking-tight">Proposals & Scrolls</h1>
            </div>
          </div>
          <nav className="flex gap-2 text-xs font-mono">
            <Link to="/disputes" className="px-3 py-2 rounded-lg border border-border text-muted-foreground hover:text-foreground hover:border-foreground/40 transition-smooth uppercase tracking-wider">
              Disputes →
            </Link>
          </nav>
        </header>

        {/* Filter pills */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {(["all", "draft", "sealed", "attested", "vetoed"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-4 py-2 rounded-lg text-xs font-mono uppercase tracking-wider border transition-smooth ${
                filter === s ? "bg-foreground text-background border-foreground" : "border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-card/60 backdrop-blur-sm border border-border rounded-2xl overflow-hidden shadow-elegant">
          <div className="grid grid-cols-[100px_1fr_160px_120px_100px_100px_80px] gap-4 px-6 py-3 border-b border-border text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            <span>Scroll ID</span>
            <span>Title</span>
            <span>Author</span>
            <span>Cluster</span>
            <span>Resonance</span>
            <span>Status</span>
            <span className="text-right">Time</span>
          </div>
          {filtered.map((p) => (
            <button
              key={p.id}
              className="w-full grid grid-cols-[100px_1fr_160px_120px_100px_100px_80px] gap-4 px-6 py-4 border-b border-border/40 last:border-0 hover:bg-foreground/5 transition-smooth text-left items-center"
            >
              <span className="font-mono text-xs text-primary">{p.id}</span>
              <span className="flex items-center gap-2 truncate">
                <MoCon icon={(ELEMENT_ICON[p.element] ?? "fire") as IconKey} size={20} />
                <span className="text-sm font-semibold truncate">{p.title}</span>
              </span>
              <span className="text-xs text-muted-foreground truncate">{p.author}</span>
              <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">{p.cluster}</span>
              <span className="flex items-center gap-2">
                <span className="text-xs font-mono">{p.resonance.toFixed(2)}</span>
                <span className="flex-1 h-1 rounded-full bg-muted overflow-hidden">
                  <span
                    className="block h-full bg-gradient-to-r from-primary to-secondary"
                    style={{ width: `${p.resonance * 100}%` }}
                  />
                </span>
              </span>
              <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded border text-center ${STATUS_STYLES[p.status]}`}>
                {p.status}
              </span>
              <span className="text-[10px] font-mono text-muted-foreground text-right">{p.ts}</span>
            </button>
          ))}
        </div>

        <div className="mt-6 flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-muted-foreground">
          <MoCon icon="fire" size={14} />
          SCROLL · ATTEST · VETO — sealed by JCS hash · governed by TruthEngine thresholds
        </div>
      </div>
    </main>
  );
};

export default Proposals;
