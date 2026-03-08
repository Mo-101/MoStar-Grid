"use client";

import { useGridTelemetry } from "@/hooks/useGridTelemetry";
import styles from "./Neo4jMonitor.module.css";
import { CSSProperties, useMemo, useState, useEffect } from "react";

export default function Neo4jMonitor() {
    const { telemetry } = useGridTelemetry();
    const [pulse, setPulse] = useState(false);

    const neo4jStatus = telemetry?.backend?.data?.neo4j || "unknown";
    const ok = telemetry?.graph?.ok;
    const isStreaming = ok && neo4jStatus === "connected";

    // When node counts or moment counts change, trigger a pulse
    const moments = telemetry?.graph.stats?.totalMoments || 0;
    useEffect(() => {
        if (moments > 0) {
            setPulse(true);
            const t = setTimeout(() => setPulse(false), 800);
            return () => clearTimeout(t);
        }
    }, [moments]);

    const layerNodes = telemetry?.graph?.layer_nodes || {};
    const totalNodesMapped = Object.values(layerNodes).reduce((sum, count) => sum + count, 0);

    const entries = Object.entries(layerNodes).sort((a, b) => b[1] - a[1]).slice(0, 6);

    return (
        <article className={styles.monitorPanel}>
            <header className={styles.header}>
                <div>
                    <p className={styles.eyebrow}>Graph Infrastructure</p>
                    <h2 className={styles.title}>Neo4j Data Core</h2>
                </div>
                <div className={`${styles.statusBadge} ${isStreaming ? styles.online : styles.offline}`}>
                    <div className={`${styles.dot} ${pulse ? styles.pulsing : ''}`} />
                    <span>{isStreaming ? 'Streaming Live' : 'Link Pending'}</span>
                </div>
            </header>

            <div className={styles.metricsGrid}>
                <div className={styles.metricCard}>
                    <span className={styles.metricLabel}>Total MoStar Moments</span>
                    <span className={styles.metricValue}>{moments.toLocaleString()}</span>
                </div>
                <div className={styles.metricCard}>
                    <span className={styles.metricLabel}>Active Entities</span>
                    <span className={styles.metricValue}>{totalNodesMapped.toLocaleString()}</span>
                </div>
                <div className={styles.metricCard}>
                    <span className={styles.metricLabel}>Connection Stream</span>
                    <span className={styles.metricValue}>{neo4jStatus}</span>
                </div>
            </div>

            <div className={styles.distributionSection}>
                <h3 className={styles.distTitle}>Top Sovereign Labels</h3>
                <div className={styles.bars}>
                    {entries.length > 0 ? entries.map(([label, count]) => {
                        const percentage = Math.max(5, Math.min(100, (count / totalNodesMapped) * 100));
                        return (
                            <div key={label} className={styles.barRow}>
                                <div className={styles.barLabelGroup}>
                                    <span className={styles.barLabel}>{label}</span>
                                    <span className={styles.barCount}>{count.toLocaleString()}</span>
                                </div>
                                <div className={styles.barTrack}>
                                    <div
                                        className={styles.barFill}
                                        style={{ width: `${percentage}%` } as CSSProperties}
                                    />
                                </div>
                            </div>
                        );
                    }) : (
                        <p className={styles.empty}>Awaiting graph node telemetry...</p>
                    )}
                </div>
            </div>
        </article>
    );
}
