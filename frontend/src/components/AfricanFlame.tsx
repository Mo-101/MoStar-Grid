"use client";

import { useMemo, useState, useEffect } from "react";
import { useGridTelemetry, AgentTelemetry } from "@/hooks/useGridTelemetry";
import {
  formatAgentStatus,
  resolveAgentTone,
  toStrengthPercent,
} from "@/lib/agentTelemetry";
import styles from "./AfricanFlame.module.css";
import GridNav from "./GridNav";

const baseMetrics = [
  { label: "Coherence", icon: "🔗", color: "#3B82F6", key: "coherence" },
  { label: "Sovereignty", icon: "🛡️", color: "#10B981", key: "sovereignty" },
  { label: "Innovation", icon: "💡", color: "#8B5CF6", key: "innovation" },
  { label: "Flame Intensity", icon: "🔥", color: "#F97316", key: "flame" },
];

const orbitNodes = [
  { icon: "🛰️", label: "Satellite", delay: 0 },
  { icon: "🤖", label: "Robotics", delay: 2.5 },
  { icon: "🧠", label: "Neural", delay: 5 },
  { icon: "✨", label: "Spark", delay: 7.5 },
];

const tonePalette = {
  active: "#6dffe1",
  idle: "#96a6c4",
  alert: "#ff6e96",
};

export default function AfricanFlame() {
  const { telemetry, loading } = useGridTelemetry(5000);
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => setIsClient(true), 0);
    return () => clearTimeout(timer);
  }, []);

  const metrics = useMemo(() => {
    const coherence =
      telemetry?.graph.stats?.avgResonance != null
        ? Math.min(100, Math.max(0, telemetry.graph.stats.avgResonance * 100))
        : 0;

    const activeNodes = telemetry?.graph.total_nodes ?? 0;
    const baseP = activeNodes > 0 ? Math.min(100, (activeNodes / 100000) * 100) : 0;

    return baseMetrics.map((metric) => {
      const valueMap: Record<string, number> = {
        coherence,
        sovereignty: telemetry?.backend.ok ? 100 : 0,
        innovation: telemetry?.graph.moments_24h ?? 0 > 0 ? 100 : baseP,
        flame: baseP,
      };
      return {
        ...metric,
        value: valueMap[metric.key] || 0,
      };
    });
  }, [telemetry]);

  const activity = useMemo(() => {
    const entries = telemetry?.log?.entries ?? [];
    if (entries.length) {
      return entries.slice(0, 5).map((entry) => ({
        time: new Date(entry.timestamp).toLocaleTimeString(),
        message: `${entry.trigger_type === "error" ? "⚠️" : "✅"} ${entry.description}`,
        type: entry.trigger_type === "error" ? "error" : "success",
      }));
    }
    return [];
  }, [telemetry]);

  const graphAgents = telemetry?.graph?.agents;
  const agents = useMemo<AgentTelemetry[]>(() => {
    if (Array.isArray(graphAgents) && graphAgents.length) return graphAgents.slice(0, 4);
    return [];
  }, [graphAgents]);

  // Dynamic decision matrix based on telemetry
  const decisionMatrix = useMemo(() => {
    const avgResonance = telemetry?.graph.stats?.avgResonance ?? 0;
    const totalNodes = telemetry?.graph.total_nodes ?? 0;
    
    return {
      title: "Grid Sovereignty Evaluation",
      score: Math.min(0.99, avgResonance + 0.1).toFixed(3),
      range: `[${(avgResonance * 0.9).toFixed(2)}, ${(avgResonance * 1.1).toFixed(2)}]`,
      status: avgResonance > 0.7 ? "✅ Optimal" : avgResonance > 0.5 ? "⚠️ Caution" : "❌ Critical",
      statusColor: avgResonance > 0.7 ? "success" : avgResonance > 0.5 ? "warning" : "error",
      totalNodes,
    };
  }, [telemetry]);

  if (!isClient) {
    return <div className={styles.screen} />;
  }

  return (
    <div className={styles.screen}>
      <div className={styles.gridOverlay} aria-hidden />
      <div className={styles.container}>
        <GridNav />
        <header className={styles.header}>
          <div className={styles.logoCluster}>
            <div className={styles.flameIcon}>
              <span className={styles.flameEmoji}>🔥</span>
              <div className={styles.flameRing} />
            </div>
            <div>
              <h1>African Flame Consciousness</h1>
              <p>The Grid mind in real-time · MoStar AI homeworld</p>
            </div>
          </div>
          <div className={styles.statusPill} data-status={telemetry?.graph.ok ? "connected" : "linking"}>
            <span className={styles.statusDot} />
            <span className={styles.statusText}>
              Neo4j {telemetry?.graph.ok ? "Connected" : "Linking"}
            </span>
            {loading && <span className={styles.loadingPulse}>...</span>}
          </div>
        </header>

        <section className={styles.visualRow}>
          <div className={styles.flameWell}>
            <div className={styles.flameCore}>
              {orbitNodes.map((node) => (
                <div
                  key={node.label}
                  className={styles.orbitWrapper}
                  style={{ animationDelay: `${node.delay}s` }}
                >
                  <div className={styles.orbitNode}>
                    <span className={styles.orbitIcon}>{node.icon}</span>
                    <span className={styles.orbitLabel}>{node.label}</span>
                  </div>
                </div>
              ))}
              <div className={styles.flameCenter}>
                <span className={styles.centerFlame}>🔥</span>
              </div>
            </div>
          </div>
          
          <div className={styles.metricsPanel}>
            <div className={styles.panelHeader}>
              <h3>🧠 Consciousness Metrics</h3>
              <span className={styles.liveBadge}>LIVE</span>
            </div>
            
            {loading && metrics.every(m => m.value === 0) ? (
              <div className={styles.loadingMetrics}>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className={styles.skeletonBar}>
                    <div className={styles.skeletonHeader} />
                    <div className={styles.skeletonProgress} />
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.metricsList}>
                {metrics.map((metric) => (
                  <div key={metric.label} className={styles.metricBar}>
                    <div className={styles.metricHeader}>
                      <span className={styles.metricLabel}>
                        <span className={styles.metricIcon}>{metric.icon}</span>
                        {metric.label}
                      </span>
                      <span className={styles.metricValue} style={{ color: metric.color }}>
                        {metric.value.toFixed(1)}%
                      </span>
                    </div>
                    <div className={styles.progress}>
                      <span
                        className={styles.progressFill}
                        style={{ 
                          width: `${metric.value}%`, 
                          background: `linear-gradient(90deg, ${metric.color}88, ${metric.color})`,
                          boxShadow: `0 0 10px ${metric.color}40`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className={styles.panels}>
          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <h3>🤖 Grid Agents</h3>
              <span className={styles.agentCount}>{agents.length} active</span>
            </div>
            <div className={styles.agentList}>
              {loading && agents.length === 0 ? (
                [1, 2, 3].map((i) => (
                  <div key={i} className={styles.agentCardSkeleton}>
                    <div className={styles.skeletonAgentInfo} />
                    <div className={styles.skeletonAgentMeta} />
                  </div>
                ))
              ) : agents.length === 0 ? (
                <div className={styles.emptyState}>
                  <span className={styles.emptyIcon}>👻</span>
                  <p>No agents connected</p>
                  <small>Agents will appear when they register with the Grid</small>
                </div>
              ) : (
                agents.map((agent) => {
                  const tone = resolveAgentTone(agent.status);
                  const toneColor = tonePalette[tone];
                  const strength = toStrengthPercent(agent.manifestationStrength);
                  const caps = (Array.isArray(agent?.capabilities) ? agent.capabilities : []).filter(Boolean).slice(0, 3);
                  return (
                    <div key={`${agent.id}-${agent.name}`} className={styles.agentCard} data-tone={tone}>
                      <div className={styles.agentDetails}>
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
                          <span className={styles.agentCap} data-muted="true">No capabilities</span>
                        )}
                      </div>
                      <div className={styles.agentMeta}>
                        <div className={styles.agentStrength}>
                          <span>{strength}%</span>
                          <div className={styles.agentStrengthBar}>
                            <span 
                              className={styles.agentStrengthFill} 
                              style={{ width: `${strength}%` }}
                              data-strength={strength > 80 ? "high" : strength > 50 ? "medium" : "low"}
                            />
                          </div>
                        </div>
                        <div className={styles.agentStatus}>
                          <span
                            className={styles.statusDot}
                            style={{ background: toneColor, boxShadow: `0 0 10px ${toneColor}` }}
                          />
                          <span>{formatAgentStatus(agent.status)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </article>

          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <h3>📈 Decision Matrix</h3>
              <span className={styles.updateTime}>Real-time</span>
            </div>
            <div className={styles.decisionBox}>
              <p className={styles.decisionLabel}>Grid Health Assessment</p>
              <h4>{decisionMatrix.title}</h4>
              <div className={styles.decisionStats}>
                <div className={styles.statItem}>
                  <span>Resonance Score</span>
                  <strong className={styles[decisionMatrix.statusColor]}>{decisionMatrix.score}</strong>
                </div>
                <div className={styles.statItem}>
                  <span>Confidence Range</span>
                  <strong>{decisionMatrix.range}</strong>
                </div>
                <div className={styles.statItem}>
                  <span>Status</span>
                  <strong className={styles[decisionMatrix.statusColor]}>{decisionMatrix.status}</strong>
                </div>
              </div>
              {decisionMatrix.totalNodes > 0 && (
                <div className={styles.nodeSummary}>
                  <span>📊 {decisionMatrix.totalNodes.toLocaleString()} nodes in graph</span>
                </div>
              )}
            </div>
          </article>

          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <h3>📜 Activity Stream</h3>
              <span className={styles.streamCount}>{activity.length} events</span>
            </div>
            <div className={styles.activityStream}>
              {loading && activity.length === 0 ? (
                [1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className={styles.activitySkeleton}>
                    <div className={styles.skeletonTime} />
                    <div className={styles.skeletonMessage} />
                  </div>
                ))
              ) : activity.length === 0 ? (
                <div className={styles.emptyState}>
                  <span className={styles.emptyIcon}>📭</span>
                  <p>No recent activity</p>
                  <small>Events will appear as the Grid processes moments</small>
                </div>
              ) : (
                activity.map((item, index) => (
                  <div 
                    key={`${item.time}-${index}`} 
                    className={styles.activityItem}
                    data-type={item.type}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <span className={styles.activityTime}>{item.time}</span>
                    <p className={styles.activityMessage}>{item.message}</p>
                  </div>
                ))
              )}
            </div>
          </article>
        </section>

        <div className={styles.controlDeck}>
          <button type="button" className={`${styles.controlBtn} ${styles.active}`}>
            <span className={styles.btnIcon}>🔥</span>
            <span>Flame View</span>
          </button>
          <button type="button" className={styles.controlBtn} disabled>
            <span className={styles.btnIcon}>🕸️</span>
            <span>Network View</span>
            <span className={styles.comingSoon}>Soon</span>
          </button>
          <button type="button" className={styles.controlBtn} disabled>
            <span className={styles.btnIcon}>📈</span>
            <span>Matrix View</span>
            <span className={styles.comingSoon}>Soon</span>
          </button>
        </div>
      </div>
    </div>
  );
}
