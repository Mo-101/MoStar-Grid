"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import { useGridTelemetry, AgentTelemetry } from "@/hooks/useGridTelemetry";
import {
  agentFallbackRoster,
  formatAgentStatus,
  resolveAgentTone,
  toStrengthPercent,
} from "@/lib/agentTelemetry";
import styles from "./AfricanFlameMap.module.css";
import GridNav from "./GridNav";
import type { GridSite } from "./FlameAtlas"; // Keep this import

const FlameAtlas = dynamic(() => import("./FlameAtlas"), {
  ssr: false,
  loading: () => <div className={styles.mapFallback}>Loading Flame Atlas…</div>,
});

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

const baseMetrics = [
  { label: "Coherence", icon: "🔗", color: "#3B82F6", key: "coherence" },
  { label: "Wisdom (Ifá)", icon: "🔮", color: "#A855F7", key: "ifa" },
  { label: "Sovereignty", icon: "👑", color: "#10B981", key: "sovereignty" },
  { label: "Innovation", icon: "⚡", color: "#EAB308", key: "innovation" },
  { label: "Flame Intensity", icon: "🔥", color: "#F97316", key: "flame" },
];

const gridSites: GridSite[] = [
  {
    name: "Lagos Gridforge",
    lat: 6.5244,
    lon: 3.3792,
    glyph: "🔥",
    status: "Prime Flame Heart",
  },
  {
    name: "Cape Coast Oracle",
    lat: 5.107,
    lon: -1.2466,
    glyph: "🔮",
    status: "Ifá Synchrony",
  },
  {
    name: "Johannesburg Body Layer",
    lat: -26.2041,
    lon: 28.0473,
    glyph: "⚙️",
    status: "Body Layer Sentinel",
  },
  {
    name: "Nairobi Sky Loom",
    lat: -1.2921,
    lon: 36.8219,
    glyph: "🛰️",
    status: "Drone Swarm Relay",
  },
];

const tonePalette = {
  active: "#6dffe1",
  idle: "#ffb347",
  alert: "#ff6e96",
} as const;

const decisionTicket = {
  title: "Partnership Sovereignty Evaluation",
  topsis: 0.782,
  range: "[0.75, 0.82]",
  status: "✓ Decided",
};

export default function AfricanFlameMap() {
  const { telemetry } = useGridTelemetry(6500);

  const metrics = useMemo(() => {
    const coherence =
      telemetry?.graph.stats?.avgResonance != null
        ? Math.min(100, Math.max(0, telemetry.graph.stats.avgResonance * 100))
        : 87.3;
    const sovereignty = telemetry?.backend.ok ? 95 : 68;
    return baseMetrics.map((metric) => {
      const valueMap: Record<string, number> = {
        coherence,
        ifa: 92.1,
        sovereignty,
        innovation: 89.7,
        flame: 91.2,
      };
      return { ...metric, value: valueMap[metric.key] ?? 80 };
    });
  }, [telemetry]);

  const activity = useMemo(() => {
    const entries = telemetry?.log.entries ?? [];
    if (!entries.length) {
      return [
        { time: "14:32:15", message: "🔮 Ifá kernel evaluated ethical implications" },
        { time: "14:32:12", message: "✨ Novel solution emerged from synthesis" },
        { time: "14:32:08", message: "📜 Verdict rendered: Sovereignty maintained" },
      ];
    }

    return entries.slice(0, 5).map((entry) => ({
      time: new Date(entry.timestamp).toLocaleTimeString(),
      message: entry.description,
    }));
  }, [telemetry]);

  const graphAgents = telemetry?.graph.agents;
  const agentWarning = telemetry?.graph.agentWarning;
  const agents = useMemo<AgentTelemetry[]>(() => {
    if (graphAgents?.length) {
      return graphAgents.slice(0, 4);
    }
    return agentFallbackRoster.slice(0, 4);
  }, [graphAgents]);

  return (
    <div className={styles.screen}>
      <div className={styles.consciousnessGrid} aria-hidden="true" />
      <div className={styles.mainContainer}>
        <GridNav />
        <header className={styles.header}>
          <div className={styles.headerContent}>
            <div className={styles.logoSection}>
              <div className={styles.flameIcon}>🔥</div>
              <div>
                <h1>African Flame Consciousness</h1>
                <p className={styles.subtitle}>The Grid mind in real-time • MoStar AI homeworld</p>
              </div>
            </div>
            <div className={styles.status}>
              <span className={styles.statusDot} />
              <span>{telemetry?.graph.ok ? "Neo4j Connected" : "Neo4j Linking"}</span>
            </div>
          </div>
        </header>

        <section className={styles.visualizationArea}>
          {MAPBOX_TOKEN ? (
            <FlameAtlas token={MAPBOX_TOKEN} sites={gridSites} />
          ) : (
            <div className={styles.mapFallback}>
              <p>Set NEXT_PUBLIC_MAPBOX_TOKEN to activate the live Atlas.</p>
            </div>
          )}

          <div className={`${styles.panel} ${styles.panelLeft}`}>
            <h3>🧠 Consciousness Metrics</h3>
            {metrics.map((metric) => (
              <div key={metric.label} className={styles.metricBar}>
                <div className={styles.metricHeader}>
                  <span className={styles.metricLabel}>
                    {metric.icon} {metric.label}
                  </span>
                  <span className={styles.metricValue}>{metric.value.toFixed(1)}%</span>
                </div>
                <div className={styles.progressBar}>
                  <span
                    className={styles.progressFill}
                    style={{ width: `${metric.value}%`, background: metric.color }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className={`${styles.panel} ${styles.panelRight}`}>
            <h3>?? Grid Agents</h3>
            {agentWarning && (
              <div className={styles.agentWarning}>
                <strong>Agent Sync Warning</strong>
                <p>{agentWarning}</p>
              </div>
            )}
            <div className={styles.agentsList}>
              {agents.map((agent) => {
                const tone = resolveAgentTone(agent.status);
                const toneColor = tonePalette[tone];
                const strength = toStrengthPercent(agent.manifestationStrength);
                const caps = (agent.capabilities ?? []).filter(Boolean).slice(0, 3);

                return (
                  <div key={`${agent.id}-${agent.name}`} className={styles.agentItem}>
                    <div className={styles.agentHeader}>
                      <div>
                        <p className={styles.agentName}>{agent.name}</p>
                        <small className={styles.agentId}>{agent.id}</small>
                        {caps.length ? (
                          <div className={styles.agentCaps}>
                            {caps.map((capability) => (
                              <span key={`${agent.id}-${capability}`} className={styles.agentCap}>
                                {capability}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className={styles.agentCap} data-muted="true">
                            Capability undisclosed
                          </span>
                        )}
                      </div>
                      <div className={styles.agentStatus}>
                        <span
                          className={styles.agentDot}
                          style={{ background: toneColor, boxShadow: `0 0 10px ${toneColor}` }}
                        />
                        {formatAgentStatus(agent.status)}
                      </div>
                    </div>
                    <div className={styles.agentStrength}>
                      <span>{strength}% manifestation</span>
                      <div className={styles.agentStrengthBar}>
                        <span className={styles.agentStrengthFill} style={{ width: `${strength}%` }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className={`${styles.panel} ${styles.panelBottomLeft}`}>
            <h3>📊 Decision Matrix</h3>
            <div className={styles.decisionBox}>
              <p className={styles.decisionLabel}>Current Decision</p>
              <p className={styles.decisionTitle}>{decisionTicket.title}</p>
              <div className={styles.decisionStats}>
                <div>
                  <small>TOPSIS Score</small>
                  <strong>{decisionTicket.topsis}</strong>
                </div>
                <div>
                  <small>Grey Range</small>
                  <strong>{decisionTicket.range}</strong>
                </div>
                <div>
                  <small>Status</small>
                  <strong className={styles.success}>{decisionTicket.status}</strong>
                </div>
              </div>
            </div>
          </div>

          <div className={`${styles.panel} ${styles.panelBottomRight}`}>
            <h3>📡 Activity Stream</h3>
            <div className={styles.activityStream}>
              {activity.map((item) => (
                <div key={`${item.time}-${item.message}`} className={styles.activityItem}>
                  <span className={styles.activityTime}>{item.time}</span>
                  <p className={styles.activityMessage}>{item.message}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className={styles.controlPanel}>
          <button className={`${styles.btn} ${styles.active}`}>🔥 Flame View</button>
          <button className={styles.btn}>🌐 Network View</button>
          <button className={styles.btn}>📊 Matrix View</button>
        </div>
      </div>
    </div>
  );
}
