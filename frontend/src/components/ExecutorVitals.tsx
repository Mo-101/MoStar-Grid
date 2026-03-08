'use client';

import React, { useEffect, useState } from 'react';
import styles from './ExecutorVitals.module.css';

interface Heartbeat {
    executor_id: string;
    last_heartbeat: string;
    cycle_count: number;
    total_processed: number;
    status: string;
}

interface ExecutionEvent {
    id: string;
    processed_at: string;
    action: string;
    reasoning_summary: string;
}

interface ExecutorStatus {
    status: 'ALIVE' | 'STALLED' | 'NEVER_RUN';
    is_alive: boolean;
    stalled_ms: number;
    heartbeat: Heartbeat | null;
    recent_events: ExecutionEvent[];
    pending_moments: number;
}

export function ExecutorVitals() {
    const [data, setData] = useState<ExecutorStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = async () => {
        try {
            const res = await fetch('/api/executor-status');
            if (!res.ok) throw new Error('Failed to fetch pulse');
            const json = await res.json();
            setData(json.executor);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000); // 3s refresh
        return () => clearInterval(interval);
    }, []);

    if (loading && !data) return (
        <div className={styles.vitalsCard} style={{ opacity: 0.5 }}>
            <div className={styles.empty}>Connecting to Nervous System...</div>
        </div>
    );

    const isStalled = data?.status === 'STALLED' || data?.status === 'NEVER_RUN';

    return (
        <div className={styles.vitalsCard}>
            {!isStalled && <div className={styles.pulseOverlay} />}

            <div className={styles.content}>
                <div className={styles.header}>
                    <div>
                        <div className={styles.eyebrow}>MoStar Executor</div>
                        <div className={styles.statusWrapper}>
                            <div className={`${styles.indicator} ${isStalled ? styles.stalled : ''}`} />
                            <span className={`${styles.statusText} ${isStalled ? styles.stalled : styles.alive}`}>
                                {data?.status || 'OFFLINE'}
                            </span>
                        </div>
                    </div>
                    <div className={styles.totalProcessed}>
                        <div className={styles.eyebrow}>Processed</div>
                        <div className={styles.count}>{data?.heartbeat?.total_processed || 0}</div>
                    </div>
                </div>

                <div className={styles.metricsGrid}>
                    <div className={styles.metricCell}>
                        <div className={styles.metricLabel}>Cycle Count</div>
                        <div className={styles.metricValue}>{data?.heartbeat?.cycle_count || 0}</div>
                    </div>
                    <div className={styles.metricCell}>
                        <div className={styles.metricLabel}>Pending</div>
                        <div className={styles.metricValue}>{data?.pending_moments || 0}</div>
                    </div>
                </div>

                <div>
                    <h4 className={styles.sectionTitle}>Recent Cognition</h4>
                    <div className={styles.eventList}>
                        {data?.recent_events.length === 0 ? (
                            <div className={styles.empty}>No recent events recorded.</div>
                        ) : (
                            data?.recent_events.map((event) => (
                                <div key={event.id} className={styles.eventRow}>
                                    <div className={styles.eventMeta}>
                                        <span>{new Date(event.processed_at).toLocaleTimeString()}</span>
                                        <span>#{event.id.slice(-4)}</span>
                                    </div>
                                    <div className={styles.eventAction}>{event.action}</div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
