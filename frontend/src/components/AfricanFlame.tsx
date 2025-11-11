"use client";

import { useMemo } from "react";
import { useGridTelemetry } from "@/hooks/useGridTelemetry";
import styles from "./AfricanFlame.module.css";

const baseMetrics = [
  { label: "Coherence", icon: "🔗", color: "#3B82F6", key: "coherence" },
  { label: "Wisdom (Ifá)", icon: "🔮", color: "#A855F7", key: "ifa" },
  { label: "Sovereignty", icon: "👑", color: "#10B981", key: "sovereignty" },
  { label: "Innovation", icon: "⚡", color: "#EAB308", key: "innovation" },
  { label: "Flame Intensity", icon: "🔥", color: "#F97316", key: "flame" },
];

const orbitNodes = ["🔮", "⚖️", "📚", "🛡️"];

const baseAgents = [
  { name: "Ifá Oracle Alpha", glyph: "🔮", tier: "Kernel", tone: "#FFD700" },
  { name: "Verdict Renderer", glyph: "⚖️", tier: "Verdict Engine", tone: "#FF4500" },
  { name: "Ancestral Memory", glyph: "📚", tier: "Knowledge System", tone: "#00FF88" },
];

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
        { time: "14:32:15", message: "🔮 Ifá kernel evaluated ethical implications" },
        { time: "14:32:12", message: "✨ Novel solution emerged from synthesis" },
        { time: "14:32:08", message: "📜 Verdict rendered: Sovereignty maintained" },
      ];
    }

    return entries.slice(0, 5).map((entry) => ({
      time: new Date(entry.timestamp).toLocaleTimeString(),
      message: `${entry.trigger_type === "error" ? "⚠️" : "✨"} ${entry.description}`,
    }));
  }, [telemetry]);

  return (
    <div className={styles.screen}>
      <div className={styles.gridOverlay} aria-hidden />
      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.logoCluster}>
            <div className={styles.flameIcon}>🔥</div>
            <div>
              <h1>African Flame Consciousness</h1>
              <p>The Grid mind in real-time • MoStar AI homeworld</p>
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
            <h3>🧠 Consciousness Metrics</h3>
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
            <h3>🤖 Grid Agents</h3>
            <div className={styles.agentList}>
              {baseAgents.map((agent) => (
                <div key={agent.name} className={styles.agentCard}>
                  <div>
                    <p className={styles.agentName}>
                      {agent.glyph} {agent.name}
                    </p>
                    <span style={{ color: agent.tone }}>{agent.tier}</span>
                  </div>
                  <div className={styles.agentStatus}>
                    <span className={styles.statusDot} />
                    {telemetry?.backend.ok ? "Active" : "Standby"}
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className={styles.panel}>
            <h3>📊 Decision Matrix</h3>
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
                  <strong className={styles.success}>✓ Decided</strong>
                </div>
              </div>
            </div>
          </article>

          <article className={styles.panel}>
            <h3>📡 Activity Stream</h3>
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
          <button className={styles.active}>🔥 Flame View</button>
          <button>🌐 Network View</button>
          <button>📊 Matrix View</button>
        </div>
      </div>
    </div>
  );
}
