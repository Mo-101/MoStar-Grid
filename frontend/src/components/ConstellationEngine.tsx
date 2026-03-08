"use client";

import React, { useEffect, useState, useMemo, useRef } from "react";
import dynamic from "next/dynamic";
import * as THREE from "three";
import styles from "./ConstellationEngine.module.css";

// Dynamically import ForceGraph3D to avoid SSR issues
const ForceGraph3D = dynamic(
    () => import("react-force-graph-3d").then((mod) => mod.default),
    { ssr: false }
);

// Type for the ref - use any since ForceGraphMethods is complex
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ForceGraphRef = any;

interface GraphNode {
    id: string | number;
    name: string;
    labels: string[];
    resonance: number;
    timestamp?: string;
    x?: number;
    y?: number;
    z?: number;
}

interface GraphLink {
    source: string | number;
    target: string | number;
    rel: string;
}

export default function ConstellationEngine() {
    const fgRef = useRef<ForceGraphRef>(null);
    const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const [isClient, setIsClient] = useState(false);

    const GRID_API = process.env.NEXT_PUBLIC_GRID_API_BASE || "http://localhost:8001";

    // Ensure client-side only rendering - deferred to avoid cascading renders
    useEffect(() => {
        const timer = setTimeout(() => setIsClient(true), 0);
        return () => clearTimeout(timer);
    }, []);

    const fetchGraph = async () => {
        try {
            const res = await fetch(`${GRID_API}/api/v1/graph/constellation?limit=1500`, { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                setGraphData(data);
                setLoading(false);
            }
        } catch (err) {
            console.error("Constellation Fetch Error:", err);
        }
    };

    useEffect(() => {
        if (!isClient) return;
        fetchGraph();
        const interval = setInterval(fetchGraph, 10000);
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isClient]);

    const getNodeColor = (labels: string[]) => {
        if (labels.includes("Agent")) return "#00F5FF";       // Electric Cyan
        if (labels.includes("KnowledgeArtifact")) return "#FFD700"; // Solar Gold
        if (labels.includes("MoStarMoment")) return "#FFB347";      // Amber
        if (labels.includes("Archetype")) return "#FF006E";         // Crimson
        if (labels.includes("OduIfa")) return "#9D4EDD";            // Oracle Violet
        if (labels.includes("CovenantKernel")) return "#fbbf24";    // Gold
        return "#ffffff";
    };

    const getLinkColor = (rel: string) => {
        switch (rel) {
            case "INFLUENCES": return "#00c2ff";
            case "CONTRIBUTES_TO": return "#ffd700";
            case "CONSULTS_ORACLE": return "#9d4edd";
            case "TRIGGERS": return "#ffb347";
            case "EVOLVES_FROM": return "#10b981";
            default: return "rgba(255,255,255,0.2)";
        }
    };

    // Create node 3D object - only on client
    const nodeThreeObject = useMemo(() => {
        if (!isClient) return undefined;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return (node: any) => {
            const color = getNodeColor(node.labels);
            const size = 3 + (node.resonance * 4);
            const group = new THREE.Group();
            const geometry = new THREE.SphereGeometry(size, 16, 16);
            const material = new THREE.MeshBasicMaterial({ color });
            const sphere = new THREE.Mesh(geometry, material);
            group.add(sphere);
            if (node.resonance > 0.7) {
                const glowGeometry = new THREE.SphereGeometry(size * 1.5, 16, 16);
                const glowMaterial = new THREE.MeshBasicMaterial({
                    color,
                    transparent: true,
                    opacity: 0.15
                });
                const glow = new THREE.Mesh(glowGeometry, glowMaterial);
                group.add(glow);
            }
            return group;
        };
    }, [isClient]);

    return (
        <div className={styles.container}>
            <header className={styles.overlay}>
                <div className={styles.hudLeft}>
                    <p className={styles.eyebrow}>NEO4J COGNITIVE SUBSTRATE</p>
                    <h2 className={styles.title}>Knowledge Constellation</h2>
                </div>
                <div className={styles.hudRight}>
                    <div className={styles.status}>
                        <div className={styles.dot} />
                        <span>Resonance Tracking Active</span>
                    </div>
                </div>
            </header>

            {loading && (
                <div className={styles.loadingOverlay}>
                    <div className={styles.spinner} />
                    <span>Syncing with Neo4j constellation...</span>
                </div>
            )}

            {isClient && (
                <ForceGraph3D
                    ref={fgRef}
                    graphData={graphData}
                    backgroundColor="#020617"
                    showNavInfo={false}
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    nodeLabel={(node: any) => `
                        <div style="background: rgba(0,0,0,0.8); padding: 8px; border: 1px solid #06b6d4; border-radius: 4px; color: white;">
                            <b style="color: #fbbf24">${node.labels[0]}</b><br/>
                            ${node.name}<br/>
                            <small>Resonance: ${node.resonance.toFixed(3)}</small>
                        </div>
                    `}
                    nodeThreeObject={nodeThreeObject}
                    linkWidth={1}
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    linkColor={(link: any) => getLinkColor(link.rel)}
                    linkDirectionalParticles={2}
                    linkDirectionalParticleSpeed={0.005}
                    linkDirectionalParticleWidth={1.5}
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    linkDirectionalParticleColor={(link: any) => getLinkColor(link.rel)}
                    d3VelocityDecay={0.3}
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    onNodeClick={(node: any) => {
                        const distance = 40;
                        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
                        if (fgRef.current) {
                            fgRef.current.cameraPosition(
                                { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                                node,
                                3000
                            );
                        }
                    }}
                />
            )}

            <footer className={styles.footerOverlay}>
                <div className={styles.controlInfo}>
                    <span>[LMB] ROTATE</span>
                    <span>[RMB] PAN</span>
                    <span>[SCROLL] ZOOM</span>
                </div>
                <div className={styles.metrics}>
                    <span>Sovereign Entities: {graphData.nodes.length}</span>
                    <span>Knowledge Filaments: {graphData.links.length}</span>
                </div>
            </footer>
        </div>
    );
}

