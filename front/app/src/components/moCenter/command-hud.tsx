'use client';

import { AlertTriangle, Activity, Radio } from 'lucide-react';
import { useEffect, useState } from 'react';

interface Signal {
  id: string;
  type: 'weather' | 'disease';
  desc: string;
  region: string;
}

interface CommandHUDProps {
  activeAnomalies: number;
  criticalAlerts: number;
  totalSignals: Signal[];
}

export function CommandHUD({
  activeAnomalies,
  criticalAlerts,
  totalSignals,
}: CommandHUDProps) {
  const [timestamp, setTimestamp] = useState<string>('--:--:--');

  useEffect(() => {
    // Update timestamp on client side after hydration
    const updateTimestamp = () => {
      const now = new Date();
      setTimestamp(now.toISOString().split('T')[1].slice(0, 8));
    };

    updateTimestamp();
    const interval = setInterval(updateTimestamp, 1000);
    return () => clearInterval(interval);
  }, []);

  const diseaseCount = totalSignals.filter((s) => s.type === 'disease').length;
  const weatherCount = totalSignals.filter((s) => s.type === 'weather').length;

  return (
    <div className="absolute top-6 left-6 w-80 glass z-10 p-6 space-y-6">
      {/* Header */}
      <div className="border-b border-primary/30 pb-4">
        <div className="flex items-center gap-3 mb-2">
          <Radio className="w-4 h-4 text-primary animate-pulse" />
          <h2 className="text-lg font-bold neon-text uppercase tracking-widest">
            AlphaMostar Grid
          </h2>
        </div>
        <p className="text-xs text-neutral-light uppercase tracking-wide opacity-70">
          Real-Time Anomaly Terminal
        </p>
      </div>

      {/* Status Grid */}
      <div className="space-y-3">
        {/* System Status */}
        <div className="flex justify-between items-center">
          <span className="text-xs uppercase tracking-wide opacity-60">
            System Status
          </span>
          <span className="neon-text font-bold text-sm">AWAKENED</span>
        </div>

        {/* Active Anomalies */}
        <div className="flex justify-between items-center">
          <span className="text-xs uppercase tracking-wide opacity-60">
            Active Anomalies
          </span>
          <span className="font-bold text-sm text-foreground">
            {activeAnomalies}
          </span>
        </div>

        {/* Weather Signals */}
        <div className="flex justify-between items-center">
          <span className="text-xs uppercase tracking-wide opacity-60">
            Weather Vectors
          </span>
          <span className="font-bold text-sm text-foreground">{weatherCount}</span>
        </div>

        {/* Disease Alerts */}
        <div className="flex justify-between items-center">
          <span className="text-xs uppercase tracking-wide opacity-60">
            Health Vectors
          </span>
          {diseaseCount > 0 ? (
            <span className="neon-text-alert font-bold text-sm flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {diseaseCount} CRITICAL
            </span>
          ) : (
            <span className="neon-text font-bold text-sm">CLEAR</span>
          )}
        </div>

        {/* Protocol Status */}
        <div className="flex justify-between items-center">
          <span className="text-xs uppercase tracking-wide opacity-60">
            Protocol
          </span>
          <span className="neon-text font-bold text-sm">FLAMEBOUND</span>
        </div>
      </div>

      {/* Signal Count */}
      <div className="border-t border-primary/20 pt-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-3 h-3 text-primary" />
          <span className="text-xs uppercase tracking-wide opacity-60">
            Incoming Signals
          </span>
        </div>
        <div className="text-2xl font-bold neon-text">{totalSignals.length}</div>
        <p className="text-xs opacity-40 mt-1">
          Nodes mapped and monitoring
        </p>
      </div>

      {/* Timestamp */}
      <div className="border-t border-primary/20 pt-4">
        <div className="text-xs opacity-40 font-mono">
          LAST_UPDATE: {timestamp}
        </div>
      </div>
    </div>
  );
}
