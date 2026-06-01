import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Flame } from "lucide-react";
import { GridMap, GridSignal } from "@/components/moCenter/grid-map";
import { CommandHUD } from "@/components/moCenter/command-hud";
import { StatsPanel } from "@/components/moCenter/stats-panel";
import { SigmaFlowLayer } from "@/components/moCenter/sigma-flow-layer";
import { AgenticToastContainer, ActiveToast } from "@/components/moCenter/agentic-toast-container";



export default function Watchtower() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const pages = [
    {
      id: 'alpha-terminal',
      title: 'Alpha Terminal',
      description: 'Real-time MoStar entity monitoring with graph database integration',
      icon: '⚡',
      color: 'from-cyan-500 to-blue-600',
      accent: '#00ffcc'
    },
    {
      id: 'planet-dashboard',
      title: 'Planet Dashboard',
      description: 'Interactive 3D planet visualization with analytics widgets',
      icon: '🌍',
      color: 'from-purple-500 to-pink-600',
      accent: '#991BFA'
    },
    {
      id: 'line-dashboard',
      title: 'Line Charts',
      description: 'Live animated charts and metrics with real-time updates',
      icon: '📊',
      color: 'from-orange-500 to-red-600',
      accent: '#FFA63F'
    }
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#05050F] via-[#0a0a15] to-[#05050F] overflow-hidden">
      {/* ANIMATED BACKGROUND ELEMENTS */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* CONTENT */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6">
        {/* HEADER */}
        <div className="text-center mb-20 space-y-4">
          <div className="inline-block">
            <div className="text-6xl font-bold bg-gradient-to-r from-cyan-400 via-purple-400 to-orange-400 bg-clip-text text-transparent mb-2">
              MoStar Grid
            </div>
          </div>
          <p className="text-xl text-slate-400 max-w-2xl">
            Unified command center for strategic soul entities with real-time monitoring and analytics
          </p>
          <div className="h-1 w-24 mx-auto bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full"></div>
        </div>

        {/* NAVIGATION CARDS */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl w-full mb-12">
          {pages.map((page) => (
            <Link key={page.id} href={`/${page.id}`}>
              <div
                onMouseEnter={() => setHoveredCard(page.id)}
                onMouseLeave={() => setHoveredCard(null)}
                className="group relative h-64 bg-[#191932]/40 backdrop-blur-xl border border-slate-700/30 rounded-2xl p-8 cursor-pointer transition-all duration-500 overflow-hidden hover:border-slate-400/50"
              >
                {/* GRADIENT BORDER EFFECT */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                {/* BACKGROUND GLOW */}
                <div className={`absolute inset-0 bg-gradient-to-br ${page.color} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}></div>

                {/* CONTENT */}
                <div className="relative z-10 h-full flex flex-col justify-between">
                  <div>
                    <div className="text-5xl mb-4 transform group-hover:scale-110 transition-transform duration-300">
                      {page.icon}
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2 group-hover:translate-x-1 transition-transform duration-300">
                      {page.title}
                    </h2>
                    <p className="text-slate-400 text-sm leading-relaxed">
                      {page.description}
                    </p>
                  </div>

                  {/* HOVER INDICATOR */}
                  <div className="flex items-center gap-2 text-sm font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ color: page.accent }}>
                    <span>Explore</span>
                    <span className="transform group-hover:translate-x-2 transition-transform duration-300">→</span>
                  </div>
                </div>

                {/* ACCENT LINE */}
                <div
                  className="absolute bottom-0 left-0 h-1 bg-gradient-to-r transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"
                  style={{ background: `linear-gradient(90deg, ${page.accent}, transparent)` }}
                ></div>
              </div>
            </Link>
          ))}
        </div>

        {/* FOOTER INFO */}
        <div className="text-center text-slate-500 text-sm max-w-2xl">
          <p>
            Select a module to begin monitoring the MoStar Universe. Each page provides unique insights into entity performance and system health.
          </p>
        </div>
      </div>
    </main>
  );
}

