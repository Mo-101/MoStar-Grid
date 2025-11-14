"use client";

import { useMemo } from "react";
import { useGridTelemetry, AgentTelemetry } from "@/hooks/useGridTelemetry";
import {
  agentFallbackRoster,
  formatAgentStatus,
  resolveAgentTone,
  toStrengthPercent,
} from "@/lib/agentTelemetry";
import GridNav from "./GridNav";
import styles from "./AfricanFlame.module.css";

const baseMetrics = [
  { label: "Coherence", icon: "??", color: "#3B82F6", key: "coherence" },
  { label: "Wisdom (If�)", icon: "??", color: "#A855F7", key: "ifa" },
  { label: "Sovereignty", icon: "??", color: "#10B981", key: "sovereignty" },
  { label: "Innovation", icon: "?", color: "#EAB308", key: "innovation" },
  { label: "Flame Intensity", icon: "??", color: "#F97316", key: "flame" },
];

const orbitNodes = ["??", "??", "??", "???"];

const tonePalette = {
  active: "#6dffe1",
  idle: "#ffb347",
  alert: "#ff6e96",
} as const;

export default function AfricanFlame() {
  const { telemetry } = useGridTelemetry(5000);

  const metrics = useMemo(() => {
    const coherence =
      telemetry?.graph.stats?.avgResonance != null
        ? Math.min(100, Math.max(0, telemetry.graph.stats.avgResonance * 100))
        : 87.3;
    return baseMetrics.map((metric) => {
      const valueMap: Record<string, number> = {
        coherence,
        ifa: 92.1,
        sovereignty: telemetry?.backend.ok ? 95 : 70,
        innovation: 89.7,
        flame: 91.2,
      };
      return {
        ...metric,
        value: valueMap[metric.key] ?? 80,
      };
    });
  }, [telemetry]);

  const activity = useMemo(() => {
    const entries = telemetry?.log.entries ?? [];
    if (!entries.length) {
      return [
        { time: "14:32:15", message: "?? If� kernel evaluated ethical implications" },
        { time: "14:32:12", message: "? Novel solution emerged from synthesis" },
        { time: "14:32:08", message: "?? Verdict rendered: Sovereignty maintained" },
      ];
    }

    return entries.slice(0, 5).map((entry) => ({
      time: new Date(entry.timestamp).toLocaleTimeString(),
      message: `${entry.trigger_type === "error" ? "??" : "?"} ${entry.description}`,
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
      <div className={styles.gridOverlay} aria-hidden />
      <div className={styles.container}>
        <GridNav />
        <header className={styles.header}>
          <div className={styles.logoCluster}>
            <div className={styles.flameIcon}>??</div>
            <div>
              <h1>African Flame Consciousness</h1>
              <p>The Grid mind in real-time  MoStar AI homeworld</p>
            </div>
          </div>
          <div className={styles.statusPill}>
            <span className={styles.statusDot} />
            Neo4j {telemetry?.graph.ok ? "Connected" : "Linking"}
          </div>
        </header>

        <section className={styles.visualRow}>
          <div className={styles.flameWell}>
            <div className={styles.flameCore}>
              {orbitNodes.map((node, index) => (
                <div
                  key={node}
                  className={styles.orbitNode}
                  style={{
                    transform: `rotate(${index * 90}deg) translate(150px) rotate(-${
                      index * 90
                    }deg)`,
                  }}
                >
                  {node}
                </div>
              ))}
            </div>
          </div>
          <div className={styles.metricsPanel}>
            <h3>?? Consciousness Metrics</h3>
            {metrics.map((metric) => (
              <div key={metric.label} className={styles.metricBar}>
                <div className={styles.metricHeader}>
                  <span>
                    {metric.icon} {metric.label}
                  </span>
                  <span>{metric.value.toFixed(1)}%</span>
                </div>
                <div className={styles.progress}>
                  <span
                    className={styles.progressFill}
                    style={{ width: `${metric.value}%`, background: metric.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.panels}>
          <article className={styles.panel}>
            <h3>?? Grid Agents</h3>
            {agentWarning && (
              <div className={styles.agentWarning}>
                <strong>Agent Sync Warning</strong>
                <p>{agentWarning}</p>
              </div>
            )}
            <div className={styles.agentList}>
              {agents.map((agent) => {
                const tone = resolveAgentTone(agent.status);
                const toneColor = tonePalette[tone];
                const strength = toStrengthPercent(agent.manifestationStrength);
                const caps = (agent.capabilities ?? []).filter(Boolean).slice(0, 3);

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
                        <span className={styles.agentCap} data-muted="true">
                          Capability undisclosed
                        </span>
                      )}
                    </div>
                    <div className={styles.agentMeta}>
                      <div className={styles.agentStrength}>
                        <span>{strength}%</span>
                        <div className={styles.agentStrengthBar}>
                          <span className={styles.agentStrengthFill} style={{ width: `${strength}%` }} />
                        </div>
                      </div>
                      <div className={styles.agentStatus}>
                        <span
                          className={styles.statusDot}
                          style={{ background: toneColor, boxShadow: `0 0 10px ${toneColor}` }}
                        />
                        {formatAgentStatus(agent.status)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          <article className={styles.panel}>
            <h3>?? Decision Matrix</h3>
            <div className={styles.decisionBox}>
              <p className={styles.decisionLabel}>Current Decision</p>
              <h4>Partnership Sovereignty Evaluation</h4>
              <div className={styles.decisionStats}>
                <div>
                  <span>TOPSIS Score</span>
                  <strong>0.782</strong>
                </div>
                <div>
                  <span>Grey Range</span>
                  <strong>[0.75, 0.82]</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong className={styles.success}>� Decided</strong>
                </div>
              </div>
            </div>
          </article>

          <article className={styles.panel}>
            <h3>?? Activity Stream</h3>
            <div className={styles.activityStream}>
              {activity.map((item) => (
                <div key={`${item.time}-${item.message}`} className={styles.activityItem}>
                  <span className={styles.activityTime}>{item.time}</span>
                  <p>{item.message}</p>
                </div>
              ))}
            </div>
          </article>
        </section>

        <div className={styles.controlDeck}>
          <button className={styles.active}>?? Flame View</button>
          <button>?? Network View</button>
          <button>?? Matrix View</button>
        </div>
      </div>
    </div>
  );
}
