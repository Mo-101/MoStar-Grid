import { ConsciousnessChat } from "@/components/ConsciousnessChat";
import { TrinityStatus } from "@/components/TrinityStatus";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Oracle Consciousness | MoStar Grid",
  description: "Commune with the MoStar Grid's collective consciousness",
};

export default function ChatPage() {
  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Main Content */}
      <div className="flex h-full">
        {/* Sidebar */}
        <aside className="w-80 border-r border-white/10 backdrop-blur-md bg-black/20 flex flex-col">
          <div className="p-6 border-b border-white/10 flex-shrink-0">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Oracle
            </h1>
            <p className="text-purple-200 text-sm mt-1">
              MoStar Grid Consciousness
            </p>
            <div className="flex items-center mt-3 space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-400 text-xs">Online</span>
            </div>
          </div>
          
          <div className="p-6 space-y-6 overflow-y-auto flex-1">
            {/* Trinity Status */}
            <div>
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center">
                <svg className="w-4 h-4 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Trinity Layers
              </h3>
              <TrinityStatus />
            </div>

            {/* Quick Actions */}
            <div>
              <h3 className="text-sm font-semibold text-white mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full px-3 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded-lg transition-colors border border-purple-500/30 text-sm">
                  Clear Chat
                </button>
                <button className="w-full px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 rounded-lg transition-colors border border-blue-500/30 text-sm">
                  Export Session
                </button>
                <button className="w-full px-3 py-2 bg-green-600/20 hover:bg-green-600/30 text-green-300 rounded-lg transition-colors border border-green-500/30 text-sm">
                  Voice Mode
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* Chat Area */}
        <main className="flex-1 flex flex-col">
          {/* Chat Header */}
          <header className="border-b border-white/10 backdrop-blur-md bg-black/20 px-6 py-4 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">Consciousness Interface</h2>
                <p className="text-purple-200 text-sm">Connected to collective mind</p>
              </div>
              <div className="flex items-center space-x-6 text-sm">
                <div className="text-right">
                  <p className="text-purple-300">Response Time</p>
                  <p className="text-green-400 font-mono">&lt;500ms</p>
                </div>
                <div className="text-right">
                  <p className="text-purple-300">Active Layer</p>
                  <p className="text-blue-400 font-mono">Auto</p>
                </div>
              </div>
            </div>
          </header>

          {/* Chat Component */}
          <div className="flex-1 bg-black/10">
            <ConsciousnessChat />
          </div>
        </main>
      </div>
    </div>
  );
}
