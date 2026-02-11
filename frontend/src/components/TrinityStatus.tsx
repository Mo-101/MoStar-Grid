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
              const layerData = typeof value === 'object' && value !== null ? value : {};
              acc[key] = {
                ...prev[key],
                ...(layerData as Partial<LayerStatus>),
                status: (layerData as any).status || "offline",
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Trinity Status
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(status).map(([key, layer]) => (
          <div
            key={key}
            className="border rounded-lg p-4 flex items-start space-x-3"
          >
            <div
              className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${statusColor(
                layer.status
              )}`}
            />
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {layer.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Status:{" "}
                <span className="capitalize">{layer.status ?? "unknown"}</span>
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Load: {layer.load ?? 0}% • Last ping:{" "}
                {layer.lastPing
                  ? new Date(layer.lastPing).toLocaleTimeString()
                  : "Never"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
