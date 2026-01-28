"use client";

import { useEffect, useState } from "react";

type LayerState = "online" | "degraded" | "offline";

interface LayerStatus {
  name: string;
  status: LayerState;
  load: number;
  lastPing: string | null;
}

export function TrinityStatus() {
  const [status, setStatus] = useState<Record<string, LayerStatus>>({
    dcx0: { name: "Mind (DCX0)", status: "offline", load: 0, lastPing: null },
    dcx1: { name: "Soul (DCX1)", status: "offline", load: 0, lastPing: null },
    dcx2: { name: "Body (DCX2)", status: "offline", load: 0, lastPing: null },
  });

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch("/api/status");
        const data = await response.json();

        if (data.layers) {
          setStatus((prev) => ({
            ...prev,
            ...Object.entries(data.layers).reduce((acc, [key, value]) => {
              // Ensure value is an object before spreading
              const layerData = typeof value === 'object' && value !== null ? value as Partial<LayerStatus> : {};
              acc[key] = {
                ...prev[key],
                ...layerData,
                status: layerData.status || "offline",
              } as LayerStatus;
              return acc;
            }, {} as Record<string, LayerStatus>),
          }));
        }
      } catch (error) {
        console.error("Failed to fetch status:", error);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColor = (layerStatus: LayerState) => {
    switch (layerStatus) {
      case "online":
        return "bg-green-500";
      case "degraded":
        return "bg-yellow-500";
      default:
        return "bg-red-500";
    }
  };

  return (
    <div className="space-y-4">
      {Object.entries(status).map(([key, layer]) => (
        <div
          key={key}
          className="backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-4 transition-all hover:bg-white/10"
        >
          <div className="flex items-start space-x-3">
            <div
              className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${statusColor(
                layer.status
              )} ${layer.status === 'online' ? 'animate-pulse' : ''}`}
            />
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-white truncate">
                {layer.name}
              </h3>
              <p className="text-xs text-purple-300 mt-1">
                Status:{" "}
                <span className="capitalize">{layer.status ?? "unknown"}</span>
              </p>
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs text-purple-400 mb-1">
                  <span>Load</span>
                  <span>{layer.load ?? 0}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      layer.status === 'online' 
                        ? 'bg-gradient-to-r from-green-400 to-green-600' 
                        : layer.status === 'degraded'
                        ? 'bg-gradient-to-r from-yellow-400 to-yellow-600'
                        : 'bg-gradient-to-r from-red-400 to-red-600'
                    }`}
                    style={{ width: `${layer.load ?? 0}%` }}
                  />
                </div>
              </div>
              <p className="text-xs text-purple-400 mt-2">
                Last ping:{" "}
                {layer.lastPing
                  ? new Date(layer.lastPing).toLocaleTimeString()
                  : "Never"}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
