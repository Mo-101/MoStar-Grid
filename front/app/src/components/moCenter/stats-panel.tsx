'use client';

import { Zap, AlertCircle, TrendingUp, Eye } from 'lucide-react';

interface StatsPanelProps {
  signalCount: number;
  anomalyCount: number;
}

export function StatsPanel({ signalCount, anomalyCount }: StatsPanelProps) {
  return (
    <div className="absolute bottom-6 right-6 space-y-3 max-w-sm">
      {/* Main Stat Card */}
      <div className="glass p-4">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-primary" />
            <span className="text-xs uppercase tracking-wide opacity-60">
              Grid Status
            </span>
          </div>
          <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-2xl font-bold neon-text">{signalCount}</div>
            <p className="text-xs opacity-50 mt-1">Total Nodes</p>
          </div>
          <div>
            <div className="text-2xl font-bold text-foreground">
              {anomalyCount}
            </div>
            <p className="text-xs opacity-50 mt-1">Anomalies</p>
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-light">
              {Math.round((anomalyCount / signalCount) * 100)}%
            </div>
            <p className="text-xs opacity-50 mt-1">Threat</p>
          </div>
        </div>
      </div>

      {/* Secondary Metric */}
      <div className="glass p-4">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-3 h-3 text-primary" />
              <span className="text-xs uppercase tracking-wide opacity-60">
                Processing Power
              </span>
            </div>
            <div className="h-1.5 bg-neutral-dark rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-primary to-alert w-3/4 rounded-full" />
            </div>
          </div>
          <span className="text-sm font-bold text-primary">75%</span>
        </div>
      </div>

      {/* Alert Box */}
      {anomalyCount > 0 && (
        <div className="glass p-3 border-l-2 border-alert">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-alert flex-shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <p className="font-bold text-alert">ANOMALY DETECTED</p>
              <p className="opacity-70">
                {anomalyCount} critical signal{anomalyCount > 1 ? 's' : ''}{' '}
                require immediate attention
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
