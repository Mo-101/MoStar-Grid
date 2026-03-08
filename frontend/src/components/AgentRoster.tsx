"use client";

import { useEffect, useState, useMemo } from "react";
import styles from "./AgentRoster.module.css";

const AGENTS_PER_PAGE = 12;

// Safely parse capabilities from Neo4j data
function parseCapabilities(raw: any): string[] {
    if (!raw) return [];
    if (Array.isArray(raw)) return raw;
    if (typeof raw === "string") {
        try {
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) return parsed;
        } catch (_) { }
        try {
            const cleaned = raw
                .replace(/'/g, '"')
                .replace(/,(\\s*[}]])/g, "$1")
                .replace(/(\w):/g, '"$1":');
            const parsed2 = JSON.parse(cleaned);
            if (Array.isArray(parsed2)) return parsed2;
            if (typeof parsed2 === "object") return Object.keys(parsed2);
        } catch (_) { }
    }
    return [];
}

// Safe date formatting
function formatDate(value: any): string {
    if (!value) return "Active";
    try {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return "Active";
        return date.toLocaleTimeString();
    } catch {
        return "Active";
    }
}

export default function AgentRoster() {
    const [agents, setAgents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [filter, setFilter] = useState("");

    useEffect(() => {
        const load = async () => {
            try {
                const res = await fetch("/api/grid-telemetry");
                const data = await res.json();
                const rawAgents = data?.graph?.agents ?? [];

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

    // Filter agents by search term
    const filteredAgents = useMemo(() => {
        if (!filter.trim()) return agents;
        const term = filter.toLowerCase();
        return agents.filter(a => 
            a.name.toLowerCase().includes(term) ||
            a.id.toLowerCase().includes(term) ||
            a.capabilities.some((c: string) => c.toLowerCase().includes(term))
        );
    }, [agents, filter]);

    // Paginate
    const totalPages = Math.ceil(filteredAgents.length / AGENTS_PER_PAGE);
    const paginatedAgents = useMemo(() => {
        const start = (currentPage - 1) * AGENTS_PER_PAGE;
        return filteredAgents.slice(start, start + AGENTS_PER_PAGE);
    }, [filteredAgents, currentPage]);

    // Reset page when filter changes - use deferred update to avoid cascading renders
    useEffect(() => {
        const timer = setTimeout(() => setCurrentPage(1), 0);
        return () => clearTimeout(timer);
    }, [filter]);

    if (loading) return <div className={styles.loading}>Accessing the lattice...</div>;
    if (error) return <div className={styles.error}>Connection disrupted: {error}</div>;

    return (
        <div className={styles.rosterContainer}>
            <div className={styles.rosterHeader}>
                <h2>Palaver Sentinels</h2>
                <span className={styles.agentCount}>{agents.length} nodes online</span>
            </div>

            {/* Search/Filter */}
            <div className={styles.filterBar}>
                <input
                    type="text"
                    placeholder="Search agents by name, ID, or capability..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className={styles.searchInput}
                />
                <span className={styles.filterCount}>
                    Showing {Math.min(paginatedAgents.length, AGENTS_PER_PAGE)} of {filteredAgents.length}
                </span>
            </div>

            {/* Agent Grid */}
            <div className={styles.agentGrid}>
                {paginatedAgents.map((a) => (
                    <div key={a.id} className={styles.agentCard}>
                        <div className={styles.cardHeader}>
                            <span className={styles.agentName}>{a.name}</span>
                            <span className={`${styles.statusBadge} ${styles[`status-${a.status}`] || styles['status-unknown']}`}>
                                {a.status}
                            </span>
                        </div>
                        <div className={styles.agentId}>ID: {a.id}</div>
                        <div className={styles.capabilitiesSection}>
                            <div className={styles.sectionLabel}>Capabilities</div>
                            {a.capabilities.length === 0 ? (
                                <div className={styles.fallbackText}>(No capabilities detected)</div>
                            ) : (
                                <div className={styles.capabilityList}>
                                    {a.capabilities.slice(0, 3).map((cap: string) => (
                                        <span key={cap} className={styles.capabilityBadge}>{cap}</span>
                                    ))}
                                    {a.capabilities.length > 3 && (
                                        <span className={styles.moreBadge}>+{a.capabilities.length - 3}</span>
                                    )}
                                </div>
                            )}
                        </div>
                        <div className={styles.cardFooter}>
                            <div className={styles.taskCount}>Tasks: <span>{a.task_count}</span></div>
                            <div className={styles.timestamp}>{formatDate(a.updated_at)}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className={styles.pagination}>
                    <button 
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className={styles.pageBtn}
                    >
                        ← Prev
                    </button>
                    <span className={styles.pageInfo}>
                        Page {currentPage} of {totalPages}
                    </span>
                    <button 
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className={styles.pageBtn}
                    >
                        Next →
                    </button>
                </div>
            )}
        </div>
    );
}
