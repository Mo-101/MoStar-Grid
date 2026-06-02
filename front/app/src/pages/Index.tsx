import { FormEvent, useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import GlyphCanvas from "@/components/GlyphCanvas";
import LoadingHUD from "@/components/LoadingHUD";
import TierTab from "@/components/TierTab";
import { MoCon, ELEMENT_ICON, EVENT_ICON, type IconKey } from "@/components/MoCon";
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

  // ── Vaporize state ──────────────────────────────────────────────────────────
  const [vaporizing, setVaporizing] = useState(false);
  const [formRipple, setFormRipple] = useState(false);
  const formRef = useRef<HTMLDivElement>(null);

  const triggerVaporize = useCallback(() => {
    setVaporizing(true);
    setFormRipple(true);
    setTimeout(() => setFormRipple(false), 700);
    setTimeout(() => { setVaporizing(false); setSecret(""); setSigil(""); }, 2200);
  }, []);

  // ── Real SSE scroll stream ──────────────────────────────────────────────────
  const [scrollEvents, setScrollEvents] = useState<
    { tag: string; glyph: string; txt: string; color: string; ts: number }[]
  >([]);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const es = new EventSource("/api/stream");
    sseRef.current = es;

    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const colorMap: Record<string, string> = {
          SCROLL: "text-primary",
          ATTEST: "text-secondary",
          PROPOSE: "text-foreground",
          VETO: "text-destructive",
          COMMIT: "text-primary",
          DISPUTE: "text-secondary",
          SEAL: "text-primary",
          REJECT: "text-destructive",
        };
        // VETO triggers the vaporize sequence on the input
        if (payload.type === "VETO" && showGate) triggerVaporize();

        setScrollEvents((prev) => [
          {
            tag: payload.type ?? "EVENT",
            glyph: EVENT_ICON[payload.type] ?? "fire",
            txt: payload.message ?? payload.detail ?? JSON.stringify(payload),
            color: colorMap[payload.type] ?? "text-foreground",
            ts: Date.now(),
          },
          ...prev.slice(0, 19), // keep last 20 events max
        ]);
      } catch {
        // non-JSON ping frame — ignore
      }
    };

    es.onerror = () => {
      // SSE dropped — reconnect handled by browser automatically
    };

    return () => {
      es.close();
      sseRef.current = null;
    };
  }, []);

  // ── Real cluster + grid status ──────────────────────────────────────────────
  const [gridStatus, setGridStatus] = useState<{
    covenant: string;
    mcpOnline: boolean;
    mcpScopes: string[];
    phase: string;
    clusters: { name: string; graph: string; pulse: number; status: string }[];
  } | null>(null);

  const censusIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [censusRes, healthRes] = await Promise.all([
          fetch("/api/grid/census"),
          fetch("/api/health"),
        ]);
        const census = await censusRes.json();
        const health = await healthRes.json();

        setGridStatus({
          covenant: census.seal ?? "—",
          mcpOnline: health?.mcp?.online ?? false,
          mcpScopes: health?.mcp?.scopes ?? [],
          phase: health?.phase ?? "—",
          clusters: [
            {
              name: "nairobi-α",
              graph: "neo4j-local",
              pulse: Math.round((census.nodes / 100000) * 100),
              status: census.nodes > 0 ? "online" : "degraded",
            },
          ],
        });
      } catch {
        // Backend not ready yet — fail silently
      }
    };

    if (!showGate) {
      fetchStatus();
      censusIntervalRef.current = setInterval(fetchStatus, 30_000); // refresh every 30s
    }

    return () => {
      if (censusIntervalRef.current) clearInterval(censusIntervalRef.current);
    };
  }, [showGate]);

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

    // 1. Terminate all active landing view status background polling
    if (censusIntervalRef.current) {
      clearInterval(censusIntervalRef.current);
    }

    try {
      const soulData = await fetchGridSoul();

      // Woo speaks — calm, composed, a little dry wit. Let each line fully play.
      const welcomeText = `Grid online. ${soulData.soul.identity.name} standing by — which, given that I've been running for months, is frankly overdue.`;
      setVoice(welcomeText);
      await speak(welcomeText, "ceremonial");

      const elements = Object.values(soulData.soul.elements) as any[];
      let currentProgress = 0;
      const progressPerStep = 100 / (elements.length + 1);

      for (const el of elements) {
        setActiveGlyph(el.glyph);
        setSyncStatus(`${el.glyph} ${el.name} resonating — ${el.domain}…`);
        const speakText = `${el.name}. ${el.domain}. Holding.`;
        setVoice(speakText);
        await speak(speakText, "stable");
        currentProgress += progressPerStep;
        setProgress(currentProgress);
      }

      setSyncStatus(`TruthEngine sealed · ${soulData.soul.identity.organization} · Entering Vault.`);
      setProgress(100);
      const sealSpeak = `Truth sealed. Welcome back, Architect. Try not to break anything this time.`;
      setVoice(sealSpeak);
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
        <div className="z-10 flex flex-col items-center text-center px-6 max-w-3xl w-full">
          <div className="flex items-center gap-2 mb-6 text-[10px] font-mono uppercase tracking-[0.3em] text-muted-foreground">
            <span className="w-8 h-px bg-primary/50" />
            MoStar Industries · African Flame Initiative
            <span className="w-8 h-px bg-primary/50" />
          </div>
          {/* MoStar Grid logo */}
          <div className="mb-8 drop-shadow-[0_0_72px_hsl(45_95%_60%/0.9)] animate-[pulse_5s_ease-in-out_infinite]">
            <img
              src="/moCons/moGrid-removebg-preview.png"
              alt="MoStar Grid"
              className="w-44 h-44 object-contain"
              draggable={false}
            />
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

          {/* Elemental thresholds — centered, large, animated */}
          <div className="flex justify-center gap-4 sm:gap-6 w-full mb-10 flex-wrap">
            {[
              { icon: "fire"  as IconKey, n: "Ikang", t: "0.75", h: "Fire",  delay: "0ms"   },
              { icon: "water" as IconKey, n: "Mmọng", t: "0.70", h: "Water", delay: "200ms" },
              { icon: "air"   as IconKey, n: "Afim",  t: "0.65", h: "Air",   delay: "400ms" },
              { icon: "earth" as IconKey, n: "Isong", t: "0.80", h: "Earth", delay: "600ms" },
            ].map((e) => (
              <div
                key={e.n}
                className="flex flex-col items-center gap-3 bg-card/50 backdrop-blur-sm border border-border/60 rounded-2xl px-5 py-5 min-w-[90px]"
                style={{ animation: `element-float 3.5s ease-in-out ${e.delay} infinite` }}
              >
                <MoCon icon={e.icon} size={56} />
                <div className="text-center">
                  <p className="text-sm font-black uppercase tracking-widest">{e.n}</p>
                  <p className="text-[10px] font-mono text-muted-foreground uppercase">{e.h}</p>
                  <p className="text-[10px] font-mono text-primary mt-1">≥ {e.t}</p>
                </div>
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
          <span className="flex items-center gap-2 justify-center flex-wrap">
            <MoCon icon="fire" size={14} /><MoCon icon="water" size={14} /><MoCon icon="air" size={14} /><MoCon icon="earth" size={14} />
            African Epistemological Ground · MoStar Industries · The Grid v4.0a
          </span>
        </footer>
      </main>
    );
  }

  // ── Tier color overlays — half-transparent, shift on tab change ─────────────
  const tierOverlay: Record<AccessTier, string> = {
    architect: "radial-gradient(ellipse at center, hsl(25 100% 40% / 0.18) 0%, transparent 70%)",
    ledger:    "radial-gradient(ellipse at center, hsl(350 80% 35% / 0.18) 0%, transparent 70%)",
    guest:     "radial-gradient(ellipse at center, hsl(240 20% 50% / 0.14) 0%, transparent 70%)",
  };

  // ── Gate page — matte black + animated glyphs + tier colour overlay ──────────
  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden" style={{ background: "#0a0a0a" }}>
      <GlyphCanvas />
      {/* Tier colour overlay — transitions smoothly on tab change */}
      <div
        className="absolute inset-0 pointer-events-none transition-all duration-700 z-[1]"
        style={{ background: tierOverlay[activeTier] }}
      />

      <div className="z-10 relative w-full max-w-md px-6 py-10 flex flex-col items-center" style={{ zIndex: 2 }}>
        <button
          onClick={() => setShowGate(false)}
          className="self-start mb-6 text-xs font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground transition-smooth flex items-center gap-2"
        >
          <span>←</span> Back
        </button>

        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-orange flex-shrink-0">
            <MoCon icon="fire" size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-foreground tracking-tight">MoStar Grid</h1>
            <p className="text-xs text-muted-foreground uppercase tracking-[0.2em]">Sovereign Gate</p>
          </div>
        </div>

        {/* Tier tabs */}
        <div className="flex gap-2 mb-6 w-full">
          <TierTab active={activeTier === "architect"} onClick={() => setActiveTier("architect")} icon={<MoCon icon="fire"  size={activeTier === "architect" ? 52 : 38} />} title="Architect" subtitle="Supreme Authority" color="orange" />
          <TierTab active={activeTier === "ledger"}    onClick={() => setActiveTier("ledger")}    icon={<MoCon icon="water" size={activeTier === "ledger"    ? 52 : 38} />} title="Ledger"    subtitle="Core Access"      color="red"    />
          <TierTab active={activeTier === "guest"}     onClick={() => setActiveTier("guest")}     icon={<MoCon icon="hex"   size={activeTier === "guest"     ? 52 : 38} />} title="Guest"     subtitle="Pulse View"       color="zinc"   />
        </div>

        {/* Form card */}
        <div
          ref={formRef}
          className={`bg-card/85 backdrop-blur-md border rounded-2xl p-6 sm:p-8 shadow-elegant w-full transition-colors ${
            vaporizing ? "border-destructive/60 veto-pulse" : "border-border"
          } ${formRipple ? "form-ripple" : ""}`}
        >
          {activeTier === "architect" && (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-tier-orange/80 mb-2">Architect Secret</label>
                {vaporizing ? (
                  <div className="input-collapse border border-destructive/60 bg-background/30">
                    <MoCon icon="veto" size={28} />
                  </div>
                ) : (
                <input
                  type="password"
                  value={secret}
                  onChange={(e) => setSecret(e.target.value)}
                  placeholder="Enter your sovereign secret..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-tier-orange/50 focus:ring-1 focus:ring-tier-orange/20 transition-smooth font-mono tracking-wider"
                />
                )}
                <p className="text-[10px] text-muted-foreground/70 mt-2 font-mono">IDENTITY: THE FLAME ARCHITECT</p>
              </div>
              <button type="submit" className="w-full bg-gradient-primary text-primary-foreground font-black py-4 rounded-xl transition-smooth uppercase tracking-[0.15em] text-sm shadow-glow-orange hover:opacity-90 active:scale-[0.98]">
                Ascend to Throne
              </button>
            </form>
          )}

          {activeTier === "ledger" && (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-tier-red/80 mb-2">Family Sigil</label>
                <input type="text" value={sigil} onChange={(e) => setSigil(e.target.value)} placeholder="Enter family sigil..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-tier-red/50 focus:ring-1 focus:ring-tier-red/20 transition-smooth font-mono tracking-wider" />
              </div>
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-tier-red/80 mb-2">Member ID</label>
                <input type="text" value={memberId} onChange={(e) => setMemberId(e.target.value)} placeholder="Enter member identifier..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-tier-red/50 focus:ring-1 focus:ring-tier-red/20 transition-smooth font-mono tracking-wider" />
              </div>
              <button type="submit" className="w-full bg-gradient-red text-secondary-foreground font-black py-4 rounded-xl transition-smooth uppercase tracking-[0.15em] text-sm shadow-glow-red hover:opacity-90 active:scale-[0.98]">
                Request Entry
              </button>
            </form>
          )}

          {activeTier === "guest" && (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2">Guest Identity</label>
                <input type="text" value={guestName} onChange={(e) => setGuestName(e.target.value)} placeholder="Enter your name..."
                  className="w-full bg-background/50 border border-border rounded-xl px-4 py-4 text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-muted-foreground focus:ring-1 focus:ring-muted-foreground/20 transition-smooth" />
              </div>
              <div className="p-4 bg-muted/40 rounded-xl border border-border">
                <p className="text-xs text-muted-foreground leading-relaxed">Guest access provides read-only pulse view. All activity is logged to the Sovereign Ledger.</p>
              </div>
              <button type="submit" className="w-full bg-gradient-zinc text-background font-black py-4 rounded-xl transition-smooth uppercase tracking-[0.15em] text-sm hover:opacity-90 active:scale-[0.98]">
                Enter Sanctum
              </button>
            </form>
          )}
        </div>

        <p className="mt-8 text-[10px] text-muted-foreground font-mono uppercase tracking-[0.2em]">
          African Epistemological Ground · MoStar Industries · The Grid v4.0a
        </p>
      </div>
    </main>
  );
};

export default Index;
