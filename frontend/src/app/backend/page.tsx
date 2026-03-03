"use client";

import { useEffect, useState } from "react";
import styles from "../../components/Sanctum.module.css";
import GridNav from "@/components/GridNav";

interface BackendMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_connections: number;
  request_count: number;
  avg_response_time: number;
  neo4j_nodes: number;
  neo4j_relationships: number;
  last_updated: string;
}

export default function BackendPage() {
  const [metrics, setMetrics] = useState<BackendMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch("http://localhost:7001/api/v1/telemetry");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Transform backend telemetry to our metrics format
        const transformedMetrics: BackendMetrics = {
          cpu_usage: data.backend?.cpu_usage || 0,
          memory_usage: data.backend?.memory_usage || 0,
          active_connections: data.backend?.active_connections || 0,
          request_count: data.backend?.request_count || 0,
          avg_response_time: data.backend?.avg_response_time || 0,
          neo4j_nodes: data.graph?.stats?.totalNodes || 0,
          neo4j_relationships: data.graph?.stats?.totalRelationships || 0,
          last_updated: new Date().toISOString(),
        };

        setMetrics(transformedMetrics);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch metrics");
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <GridNav />
        <h1 style={{ marginTop: "2rem" }}>🔧 Backend Operations</h1>
        <p>Loading backend metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        <GridNav />
        <h1 style={{ marginTop: "2rem" }}>🔧 Backend Operations</h1>
        <p style={{ color: "#ff6e96" }}>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className={styles.sanctum}>
      <div style={{ marginTop: "1rem" }}><GridNav /></div>
      <section className={styles.council}>
        <header>
          <p className={styles.eyebrow}>Backend Operations</p>
          <h1>🔧 Backend Tracking</h1>
          <p>Real-time system monitoring and performance metrics</p>
        </header>

        <div className={styles.matrixGrid}>
          <article className={styles.matrixCard}>
            <h3>🖥️ System Resources</h3>
            <div className={styles.matrixContent}>
              <div className={styles.matrixRow}>
                <span>CPU Usage</span>
                <strong>{metrics?.cpu_usage.toFixed(1)}%</strong>
              </div>
              <div className={styles.matrixRow}>
                <span>Memory Usage</span>
                <strong>{metrics?.memory_usage.toFixed(1)}%</strong>
              </div>
              <div className={styles.matrixRow}>
                <span>Active Connections</span>
                <strong>{metrics?.active_connections}</strong>
              </div>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <h3>📊 Request Metrics</h3>
            <div className={styles.matrixContent}>
              <div className={styles.matrixRow}>
                <span>Total Requests</span>
                <strong>{metrics?.request_count}</strong>
              </div>
              <div className={styles.matrixRow}>
                <span>Avg Response Time</span>
                <strong>{metrics?.avg_response_time.toFixed(2)}ms</strong>
              </div>
              <div className={styles.matrixRow}>
                <span>Last Updated</span>
                <strong>{new Date(metrics?.last_updated || "").toLocaleTimeString()}</strong>
              </div>
            </div>
          </article>

          <article className={styles.matrixCard}>
            <h3>🕸️ Neo4j Database</h3>
            <div className={styles.matrixContent}>
              <div className={styles.matrixRow}>
                <span>Total Nodes</span>
                <strong>{metrics?.neo4j_nodes}</strong>
              </div>
              <div className={styles.matrixRow}>
                <span>Total Relationships</span>
                <strong>{metrics?.neo4j_relationships}</strong>
              </div>
              <div className={styles.matrixRow}>
                <span>Database Status</span>
                <strong style={{ color: "#10B981" }}>Connected</strong>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
