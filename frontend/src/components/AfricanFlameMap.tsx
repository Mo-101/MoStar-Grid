"use client";

import { useMemo } from "react";
import Link from "next/link";
import Map, { Marker } from "react-map-gl";
import { useGridTelemetry } from "@/hooks/useGridTelemetry";
import styles from "./AfricanFlameMap.module.css";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

const baseMetrics = [
  { label: "Coherence", icon: "🔗", color: "#3B82F6", key: "coherence" },
  { label: "Wisdom (Ifá)", icon: "🔮", color: "#A855F7", key: "ifa" },
  { label: "Sovereignty", icon: "👑", color: "#10B981", key: "sovereignty" },
  { label: "Innovation", icon: "⚡", color: "#EAB308", key: "innovation" },
  { label: "Flame Intensity", icon: "🔥", color: "#F97316", key: "flame" },
];

const gridSites = [
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

const agentRoster = [
  { glyph: "🔮", name: "Ifá Oracle Alpha", tier: "Kernel", accent: "#FFD700" },
  { glyph: "⚖️", name: "Verdict Renderer", tier: "Verdict Engine", accent: "#FF8C00" },
  { glyph: "📚", name: "Ancestral Memory", tier: "Knowledge System", accent: "#00FF88" },
  { glyph: "🛡️", name: "Guardian Weave", tier: "Security Mesh", accent: "#60A5FA" },
];

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

  return (
    <div className={styles.screen}>
      <div className={styles.consciousnessGrid} aria-hidden="true" />
      <div className={styles.mainContainer}>
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
            <Link href="/" className={styles.navButton} aria-label="Return to the Oracle's Sanctum">
              <span>◁</span> Sanctum
            </Link>
          </div>
        </header>

        <section className={styles.visualizationArea}>
          {MAPBOX_TOKEN ? (
            <Map
              mapboxAccessToken={MAPBOX_TOKEN}
              initialViewState={{
                longitude: 15,
                latitude: 2,
                zoom: 3,
              }}
              mapStyle="mapbox://styles/mapbox/dark-v11"
              reuseMaps
              attributionControl={false}
              style={{ width: "100%", height: "100%" }}
            >
              {gridSites.map((site) => (
                <Marker key={site.name} longitude={site.lon} latitude={site.lat} anchor="center">
                  <div className={styles.marker}>
                    <span>{site.glyph}</span>
                    <p>{site.name}</p>
                    <small>{site.status}</small>
                  </div>
                </Marker>
              ))}
            </Map>
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
            <h3>🤖 Grid Agents</h3>
            <div className={styles.agentsList}>
              {agentRoster.map((agent) => (
                <div key={agent.name} className={styles.agentItem}>
                  <div className={styles.agentHeader}>
                    <div>
                      <p className={styles.agentName}>
                        {agent.glyph} {agent.name}
                      </p>
                      <small style={{ color: agent.accent }}>{agent.tier}</small>
                    </div>
                    <div className={styles.agentStatus}>
                      <span className={styles.agentDot} />
                      {telemetry?.backend.ok ? "Active" : "Listening"}
                    </div>
                  </div>
                </div>
              ))}
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
