"use client";

import { useEffect, useState } from "react";
import styles from "./AgentRoster.module.css";

// ---------------------------------------------------------------------------
// SAFELY PARSE CAPABILITIES (your Neo4j data contains corrupted strings)
// ---------------------------------------------------------------------------
function parseCapabilities(raw: any): string[] {
    if (!raw) return [];

    if (Array.isArray(raw)) return raw;

    if (typeof raw === "string") {
        // First: try JSON
        try {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) return parsed;
        } catch (_) { }

        // Second: attempt to normalize Python-/broken-like syntax
        try {
            const cleaned = raw
                .replace(/'/g, '"')
                .replace(/,(\s*[}\]])/g, "$1") // remove trailing commas
                .replace(/(\w):/g, '"$1":');   // ensure keys are quoted

            const parsed2 = JSON.parse(cleaned);
            if (Array.isArray(parsed2)) return parsed2;
            if (typeof parsed2 === "object") return Object.keys(parsed2);
        } catch (_) { }
    }

    return [];
}

// ---------------------------------------------------------------------------
// THE AGENT ROSTER COMPONENT
// ---------------------------------------------------------------------------
export default function AgentRoster() {
    const [agents, setAgents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Fetch from your real API route: /api/grid-telemetry
    useEffect(() => {
        const load = async () => {
            try {
                const res = await fetch("/api/grid-telemetry");
                const data = await res.json();

                const rawAgents = data?.graph?.agents ?? [];

                // Normalize each agent
                const normalized = rawAgents.map((agent: any) => ({
                    id: agent.id,
                    name: agent.name || agent.agent_id || "Unnamed Sentinel",
                    status: agent.status?.toLowerCase() || "unknown",
                    capabilities: parseCapabilities(agent.capabilities),
                    task_count: agent.task_count?.low ?? agent.task_count ?? 0,
                    updated_at: agent.updated_at,
                }));

                setAgents(normalized);
            } catch (err: any) {
                setError(err.message);
            }

            setLoading(false);
        };

        load();
    }, []);

    // -------------------------------------------------------------------------
    // UI STATES
    // -------------------------------------------------------------------------
    if (loading) return <div className={styles.loading}>Accessing the lattice...</div>;
    if (error) return <div className={styles.error}>Connection disrupted: {error}</div>;

    return (
        <div className={styles.rosterContainer}>
            <div className={styles.rosterHeader}>
                <h2>Palaver Sentinels — {agents.length} nodes online</h2>
            </div>

            <div className={styles.agentGrid}>
                {agents.map((a) => (
                    <div
                        key={a.id}
                        className={styles.agentCard}
                    >
                        <div className={styles.cardHeader}>
                            <span className={styles.agentName}>{a.name}</span>
                            <span
                                className={`${styles.statusBadge} ${styles[`status-${a.status}`] || styles['status-unknown']}`}
                            >
                                {a.status}
                            </span>
                        </div>

                        <div className={styles.agentId}>
                            ID: {a.id}
                        </div>

                        <div className={styles.capabilitiesSection}>
                            <div className={styles.sectionLabel}>
                                Capabilities
                            </div>

                            {a.capabilities.length === 0 ? (
                                <div className={styles.fallbackText}>
                                    (No capabilities detected)
                                </div>
                            ) : (
                                <div className={styles.capabilityList}>
                                    {a.capabilities.map((cap: string) => (
                                        <span
                                            key={cap}
                                            className={styles.capabilityBadge}
                                        >
                                            {cap}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className={styles.cardFooter}>
                            <div className={styles.taskCount}>
                                Tasks: <span>{a.task_count}</span>
                            </div>
                            <div className={styles.timestamp}>
                                {a.updated_at ? new Date(a.updated_at).toLocaleTimeString() : 'Active'}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
