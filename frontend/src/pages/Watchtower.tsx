import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Flame } from "lucide-react";
import { GridMap, GridSignal } from "@/components/moCenter/grid-map";
import { CommandHUD } from "@/components/moCenter/command-hud";
import { StatsPanel } from "@/components/moCenter/stats-panel";
import { SigmaFlowLayer } from "@/components/moCenter/sigma-flow-layer";
import { AgenticToastContainer, ActiveToast } from "@/components/moCenter/agentic-toast-container";

const MOCK_SIGNALS: GridSignal[] = [
  { id: "sig_nbo", type: "weather", coords: [36.82, -1.29], desc: "Anomalous temperature spike", region: "Nairobi" },
  { id: "sig_los", type: "disease", coords: [3.37, 6.52], desc: "Pathogen vector warning", region: "Lagos" },
  { id: "sig_kla", type: "weather", coords: [32.58, 0.34], desc: "Barometric pressure drop", region: "Kampala" },
];

const MOCK_TOASTS: ActiveToast[] = [
  { id: "t1", name: "AlphaMostar", location: "Central Core", message: "Igniting primary consciousness layer. Authorizing flame-write badges.", color: "#00ffcc" },
  { id: "t2", name: "DeepCAL", location: "Logic Hub", message: "Processing environmental metrics to isolate deviations.", color: "#38bdf8" },
];

export default function Watchtower() {
  const [mapInstance, setMapInstance] = useState<any>(null);
  const [toasts, setToasts] = useState<ActiveToast[]>(MOCK_TOASTS);

  const handleMapLoad = useCallback((map: any) => {
    setMapInstance(map);
  }, []);

  const handleDismissToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <main className="min-h-screen bg-background text-foreground flex relative overflow-hidden">
      {/* Sidebar - minimal copy of Dashboard sidebar to maintain structural integrity */}
      <nav className="w-[100px] shrink-0 bg-[hsl(240_36%_15%)] flex flex-col items-center py-8 border-r border-border relative z-20 shadow-[4px_0_24px_rgba(0,0,0,0.4)]">
        <Link
          to="/"
          className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-orange mb-12"
          aria-label="Back to gate"
        >
          <Flame className="w-6 h-6 text-primary-foreground" />
        </Link>
        <Link
          to="/dashboard"
          className="text-xs uppercase font-mono tracking-widest text-muted-foreground hover:text-tier-orange"
        >
          Back
        </Link>
      </nav>

      {/* Main UI */}
      <div className="flex-1 relative w-full h-full">
        <GridMap signals={MOCK_SIGNALS} onMapLoad={handleMapLoad} />
        {mapInstance && <SigmaFlowLayer map={mapInstance} isActive={true} />}
        
        <CommandHUD 
          activeAnomalies={2} 
          criticalAlerts={1} 
          totalSignals={MOCK_SIGNALS as any[]} 
        />
        
        <StatsPanel 
          signalCount={MOCK_SIGNALS.length} 
          anomalyCount={1} 
        />
        
        <AgenticToastContainer 
          toasts={toasts} 
          onDismiss={handleDismissToast} 
        />
      </div>
    </main>
  );
}
