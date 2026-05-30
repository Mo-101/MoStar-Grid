import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import GlyphCanvas from "@/components/GlyphCanvas";
import LoadingHUD from "@/components/LoadingHUD";
import TierTab from "@/components/TierTab";
import { fetchGridSoul } from "@/api/grid";
import { speak, stopVoice } from "@/utils/voice";

type AccessTier = "architect" | "ledger" | "guest";

const Index = () => {
  const navigate = useNavigate();
  const [activeTier, setActiveTier] = useState<AccessTier>("architect");
  const [loading, setLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [voice, setVoice] = useState("");
  const [activeGlyph, setActiveGlyph] = useState("🜂");
  const [secret, setSecret] = useState("");
  const [sigil, setSigil] = useState("");
  const [memberId, setMemberId] = useState("");
  const [guestName, setGuestName] = useState("");
  const [isBreakGlass] = useState(false);
  const [showGate, setShowGate] = useState(false);

  useEffect(() => {
    return () => stopVoice();
  }, []);

  // SEO
  useEffect(() => {
    document.title = "MoStar Grid — Sovereign Gate | African AI Homeworld";
    const desc = "Enter MoStar Grid: the sovereign AI homeworld built on African epistemological ground. Architect, Ledger, and Guest access tiers.";
    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.setAttribute("name", "description");
      document.head.appendChild(meta);
    }
    meta.setAttribute("content", desc);

    let canonical = document.querySelector('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.setAttribute("rel", "canonical");
      document.head.appendChild(canonical);
    }
    canonical.setAttribute("href", window.location.origin + "/");
  }, []);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setProgress(0);
    setSyncStatus("Connecting to Grid API...");

    try {
      const soulData = await fetchGridSoul();
      const welcomeText = `Welcome to ${soulData.soul.identity.organization}. I am ${soulData.soul.identity.name}, sovereign intelligence built by ${soulData.soul.identity.architect}.`;
      setVoice(welcomeText);

      // Sync perfectly: wait for voice to finish before proceeding
      await speak(welcomeText, "ceremonial");

      const elements = Object.values(soulData.soul.elements);
      let currentProgress = 0;
      const progressPerStep = 100 / (elements.length + 1);

      for (const el of elements) {
        setActiveGlyph(el.glyph);
        setSyncStatus(`${el.glyph} ${el.name} resonating — ${el.domain}…`);

        // No emojis in spoken text to avoid "broken record" literal unicode readings
        const speakText = `${el.name} resonating. ${el.domain}.`;
        await speak(speakText, "stable");

        currentProgress += progressPerStep;
        setProgress(currentProgress);
      }

      setSyncStatus(`TruthEngine sealed · ${soulData.soul.identity.organization} · Entering Vault.`);
      setProgress(100);

      const sealSpeak = `Truth Engine sealed by ${soulData.soul.identity.organization}. Entering Vault.`;
      await speak(sealSpeak, "ceremonial");

      setLoading(false);
      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      setSyncStatus("Failed to connect to Grid API. Booting in fallback mode...");
      await new Promise((r) => setTimeout(r, 2000));
      setLoading(false);
      navigate("/dashboard");
    }
  };

  if (loading) {
    return <LoadingHUD progress={progress} status={syncStatus} voice={voice} activeGlyph={activeGlyph} />;
  }

  if (!showGate) {
    return (
      <main className="min-h-screen bg-background flex flex-col items-center justify-center relative overflow-hidden">
        <GlyphCanvas />
        <div className="z-10 flex flex-col items-center text-center px-6 max-w-3xl">
          <div className="flex items-center gap-2 mb-6 text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground">
            <span className="w-8 h-px bg-primary/50" />
            MoStar Industries · African Flame Initiative
            <span className="w-8 h-px bg-primary/50" />
          </div>
          <div className="w-16 h-16 rounded-2xl bg-gradient-primary flex items-center justify-center shadow-glow-orange mb-8">
            <span className="text-4xl">🜂</span>
          </div>
          <h1 className="text-5xl sm:text-7xl font-black text-foreground tracking-tight mb-6 leading-[0.95]">
            <span className="text-primary">Sovereign</span> Intelligence,
            <br />
            <span className="text-secondary">Federated</span> by Truth.
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg leading-relaxed mb-8 max-w-xl">
            MoStar Grid is the kernel of the African AI homeworld. <span className="text-foreground">Woo</span> interprets,
            the <span className="text-foreground">TruthEngine</span> governs, the <span className="text-foreground">Grid</span> executes —
            three powers, never one. Two clusters. Two graphs. One protocol. No empire.
          </p>

          {/* Elemental thresholds */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full max-w-2xl mb-10">
            {[
              { g: "🜂", n: "Ikang", t: "0.75", h: "Fire" },
              { g: "🜄", n: "Mmọng", t: "0.70", h: "Water" },
              { g: "🜁", n: "Afim", t: "0.65", h: "Air" },
              { g: "🜃", n: "Isong", t: "0.80", h: "Earth" },
            ].map((e) => (
              <div key={e.n} className="bg-card/60 backdrop-blur-sm border border-border rounded-xl p-3 text-left">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-2xl">{e.g}</span>
                  <span className="text-[10px] font-mono text-primary">≥ {e.t}</span>
                </div>
                <p className="text-xs font-black uppercase tracking-wider">{e.n}</p>
                <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">{e.h}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-6 text-xs font-mono text-muted-foreground uppercase tracking-wider mb-10 flex-wrap justify-center">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Neo4j · nairobi-α
            </span>
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              Neo4j · kampala-β
            </span>
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-secondary rounded-full animate-pulse" />
              Federation SSE live
            </span>
          </div>
          <button
            onClick={() => setShowGate(true)}
            className="bg-gradient-primary text-primary-foreground font-black py-4 px-10 rounded-xl transition-smooth uppercase tracking-[0.2em] text-sm shadow-glow-orange hover:opacity-90 active:scale-[0.98]"
          >
            Enter the Gate
          </button>
        </div>
        <footer className="absolute bottom-6 left-6 right-6 text-center text-[10px] text-muted-foreground font-mono uppercase tracking-[0.2em]">
          🜂 🜄 🜁 🜃 &nbsp; African Epistemological Ground · MoStar Industries · The Grid v4.0a
        </footer>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background flex flex-col lg:flex-row">
      {/* Left — Login */}
      <section className="w-full lg:w-1/2 flex flex-col justify-center items-start px-6 sm:px-12 lg:px-20 py-12 lg:py-0 min-h-[60vh] lg:min-h-screen relative z-10">
        <button
          onClick={() => setShowGate(false)}
          className="mb-6 text-xs font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground transition-smooth flex items-center gap-2"
        >
          <span>←</span> Back to Landing
        </button>

        <header className="mb-10 w-full">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-orange flex-shrink-0">
              <span className="text-2xl">🜂</span>
            </div>
            <div>
              <h1 className="text-2xl font-black text-foreground tracking-tight">MoStar Grid</h1>
              <p className="text-xs text-muted-foreground uppercase tracking-[0.2em]">Sovereign Gate</p>
            </div>
          </div>
          <p className="text-muted-foreground text-sm leading-relaxed max-w-md">
            Enter the African AI Homeworld. Built from African intelligence. For African sovereignty.
          </p>
        </header>

        <div className="flex gap-2 sm:gap-3 mb-8 w-full">
          <TierTab active={activeTier === "architect"} onClick={() => setActiveTier("architect")} icon="🜂" title="Architect" subtitle="Supreme Authority" color="orange" />
          <TierTab active={activeTier === "ledger"} onClick={() => setActiveTier("ledger")} icon="🜄" title="Ledger" subtitle="Core Access" color="red" />
          <TierTab active={activeTier === "guest"} onClick={() => setActiveTier("guest")} icon="⬡" title="Guest" subtitle="Pulse View" color="zinc" />
        </div>

        <div className="bg-card/80 backdrop-blur-sm border border-border rounded-2xl p-6 sm:p-8 shadow-elegant w-full max-w-lg">
          {activeTier === "architect" && (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-tier-orange/80 mb-2">
                  Architect Secret
                </label>
                <input
                  type="password"
                  value={secret}
                  onChange={(e) => setSecret(e.target.value)}
                  placeholder="Enter your sovereign secret..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-tier-orange/50 focus:ring-1 focus:ring-tier-orange/20 transition-smooth font-mono tracking-wider"
                />
                <p className="text-[10px] text-muted-foreground/70 mt-2 font-mono">IDENTITY: THE FLAME ARCHITECT</p>
              </div>
              <button
                type="submit"
                className="w-full bg-gradient-primary text-primary-foreground font-black py-4 rounded-xl transition-smooth uppercase tracking-[0.15em] text-sm shadow-glow-orange hover:opacity-90 active:scale-[0.98]"
              >
                Ascend to Throne
              </button>
            </form>
          )}

          {activeTier === "ledger" && (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-tier-red/80 mb-2">Family Sigil</label>
                <input
                  type="text"
                  value={sigil}
                  onChange={(e) => setSigil(e.target.value)}
                  placeholder="Enter family sigil..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-tier-red/50 focus:ring-1 focus:ring-tier-red/20 transition-smooth font-mono tracking-wider"
                />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-tier-red/80 mb-2">Member ID</label>
                <input
                  type="text"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  placeholder="Enter member identifier..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-tier-red/50 focus:ring-1 focus:ring-tier-red/20 transition-smooth font-mono tracking-wider"
                />
              </div>
              <div className="flex items-center gap-2 py-2">
                <div className={`w-2 h-2 rounded-full ${isBreakGlass ? "bg-destructive animate-ping" : "bg-muted"}`} />
                <span className="text-[10px] text-muted-foreground font-mono uppercase">
                  {isBreakGlass ? "Emergency Protocol Active" : "Normal Operations"}
                </span>
              </div>
              <button
                type="submit"
                className="w-full bg-gradient-red text-secondary-foreground font-black py-4 rounded-xl transition-smooth uppercase tracking-[0.15em] text-sm shadow-glow-red hover:opacity-90 active:scale-[0.98]"
              >
                Request Entry
              </button>
            </form>
          )}

          {activeTier === "guest" && (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2">Guest Identity</label>
                <input
                  type="text"
                  value={guestName}
                  onChange={(e) => setGuestName(e.target.value)}
                  placeholder="Enter your name..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-muted-foreground focus:ring-1 focus:ring-muted-foreground/20 transition-smooth"
                />
              </div>
              <div className="p-4 bg-muted/40 rounded-xl border border-border">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Guest access provides read-only pulse visualization. All actions are logged to the Sovereign Ledger.
                </p>
              </div>
              <button
                type="submit"
                className="w-full bg-gradient-zinc text-background font-black py-4 rounded-xl transition-smooth uppercase tracking-[0.15em] text-sm hover:opacity-90 active:scale-[0.98]"
              >
                Enter Sanctum
              </button>
            </form>
          )}
        </div>

        <footer className="mt-12 pt-8 border-t border-border w-full">
          <p className="text-[10px] text-muted-foreground font-mono uppercase tracking-[0.2em] flex items-center gap-2 flex-wrap">
            <span>🜂 African Epistemological Ground</span>
            <span className="opacity-40">|</span>
            <span>MoStar Industries</span>
            <span className="opacity-40">|</span>
            <span>The Grid v1.0 🜄</span>
          </p>
        </footer>
      </section>

      {/* Right — Hero */}
      <aside className="hidden lg:flex lg:w-1/2 relative items-end justify-end min-h-screen">
        <GlyphCanvas />
        <div className="absolute bottom-16 left-12 right-12 z-10">
          <h2 className="text-4xl font-black text-foreground mb-4 tracking-tight">
            <span className="text-tier-orange">African</span> Intelligence
          </h2>
          <p className="text-muted-foreground text-lg leading-relaxed mb-6 max-w-md">
            The first sovereign AI homeworld built on African epistemological ground. Powered by the DCX Trinity and protected by the Flame Architect.
          </p>
          <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground uppercase tracking-wider flex-wrap">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Neo4j Online
            </span>
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-tier-orange rounded-full animate-pulse" style={{ backgroundColor: "hsl(var(--tier-orange))" }} />
              Trinity Active
            </span>
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              Grid Synced
            </span>
          </div>
        </div>
      </aside>
    </main>
  );
};

export default Index;
