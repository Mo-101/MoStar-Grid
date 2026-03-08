"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import GridNav from "@/components/GridNav";

// ═══════════════════════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════════════════════
const THEME = {
    bg: "#06070b",
    layers: {
        COVENANT_KERNEL: {
            stroke: "#22c55e",
            fill: "rgba(34,197,94,0.05)",
            glow: "rgba(34,197,94,0.35)",
            text: "#d1fae5",
            label: "LAYER 1 \u2014 COVENANT KERNEL",
        },
        MESH_INTELLIGENCE: {
            stroke: "#60a5fa",
            fill: "rgba(96,165,250,0.04)",
            glow: "rgba(96,165,250,0.30)",
            text: "#dbeafe",
            label: "LAYER 2 \u2014 DISTRIBUTED INTELLIGENCE",
        },
        EXECUTION_RING: {
            stroke: "#fb7185",
            fill: "rgba(251,113,133,0.04)",
            glow: "rgba(251,113,133,0.30)",
            text: "#ffe4e6",
            label: "LAYER 3 \u2014 EXECUTION RING",
        },
        LEDGER_SPINE: {
            stroke: "#a78bfa",
            fill: "rgba(167,139,250,0.04)",
            glow: "rgba(167,139,250,0.30)",
            text: "#ede9fe",
            label: "LAYER 4 \u2014 SOVEREIGN LEDGER",
        },
        PUBLIC_INTERFACE: {
            stroke: "#fbbf24",
            fill: "rgba(251,191,36,0.04)",
            glow: "rgba(251,191,36,0.25)",
            text: "#fffbeb",
            label: "LAYER 5 \u2014 PUBLIC INTERFACE",
        },
        ORBITALS: {
            stroke: "#94a3b8",
            fill: "rgba(148,163,184,0.03)",
            glow: "rgba(148,163,184,0.18)",
            text: "#e2e8f0",
            label: "HYPER-INTELLIGENCE ORBITALS",
        },
    },
    edges: {
        constraint: "#22c55e",
        governance: "#f59e0b",
        insight: "#64748b",
        signal: "#60a5fa",
        tasking: "#fb7185",
        attestation: "#fb7185",
        record: "#a78bfa",
        publish: "#fbbf24",
        feedback: "#38bdf8",
        alarm: "#ef4444",
    } as Record<string, string>,
};

const GLYPHS: Record<string, { sym: string; name: string; desc: string }> = {
    COVENANT_GATE: {
        sym: "\u27C1",
        name: "Covenant Gate",
        desc: "Immutable execution barrier \u2014 Truth + Scope + Compliance",
    },
    MESH_CONSENSUS: {
        sym: "\u27E1",
        name: "Mesh Consensus",
        desc: "Distributed intelligence \u2014 no central brain",
    },
    CLOSED_LOOP: {
        sym: "\u25C9",
        name: "Closed Loop",
        desc: "Request \u2192 gate \u2192 execute \u2192 log \u2192 witness \u2192 feedback",
    },
    LEDGER_SPINE: {
        sym: "\u2394",
        name: "Ledger Spine",
        desc: "Tamper-evident accounting backbone",
    },
    PUBLIC_WITNESS: {
        sym: "\u2609",
        name: "Public Witness",
        desc: "Distributed memory + capture deterrence",
    },
    DRIFT: {
        sym: "\u0394",
        name: "Drift Detector",
        desc: "Detects bias/drift/governance decay",
    },
    CAPTURE_ALARM: {
        sym: "\u26A0",
        name: "Capture Alarm",
        desc: "Triggers on prohibited purpose/extraction",
    },
    SELF_ATTACK: {
        sym: "\u260D",
        name: "Self-Attack",
        desc: "Simulates abuse vectors before adversaries do",
    },
    KEY_ROTATION: {
        sym: "\u21C4",
        name: "Key Rotation",
        desc: "Founder-less ops + multisig rotation ritual",
    },
};

type NodeDef = {
    id: string;
    label: string;
    layer: string;
    glyph: string | null;
    tags: string[];
};

type EdgeDef = {
    id: string;
    s: string;
    t: string;
    type: string;
    label: string;
    anim?: boolean;
    dash?: boolean;
};

const NODES: NodeDef[] = [
    { id: "truth_engine", label: "MoStar Truth Engine", layer: "COVENANT_KERNEL", glyph: "COVENANT_GATE", tags: ["VERIFIED"] },
    { id: "scope_firewall", label: "Scope Firewall", layer: "COVENANT_KERNEL", glyph: "COVENANT_GATE", tags: ["HARD_GATE"] },
    { id: "compliance_gate", label: "Compliance Gate (Kenya DPA)", layer: "COVENANT_KERNEL", glyph: "COVENANT_GATE", tags: ["REQUIRED"] },
    { id: "radx_consensus", label: "RAD-X Mesh Consensus Engine", layer: "MESH_INTELLIGENCE", glyph: "MESH_CONSENSUS", tags: ["CORE"] },
    { id: "fl_ministry", label: "Ministry FL Node", layer: "MESH_INTELLIGENCE", glyph: null, tags: ["OP:REQUIRED"] },
    { id: "fl_university", label: "University FL Node", layer: "MESH_INTELLIGENCE", glyph: null, tags: ["OP:REQUIRED"] },
    { id: "fl_community", label: "Community FL Node", layer: "MESH_INTELLIGENCE", glyph: null, tags: ["OP:REQUIRED"] },
    { id: "satellite", label: "Satellite Sensing", layer: "MESH_INTELLIGENCE", glyph: null, tags: [] },
    { id: "iot_sensors", label: "IoT Water / Vector Sensors", layer: "MESH_INTELLIGENCE", glyph: null, tags: [] },
    { id: "ussd_gateway", label: "USSD + Mobile App Gateway", layer: "MESH_INTELLIGENCE", glyph: null, tags: [] },
    { id: "ascc", label: "ASCC (Elders+Scientists+Youth)", layer: "EXECUTION_RING", glyph: "CLOSED_LOOP", tags: ["GOV_GATE"] },
    { id: "dao", label: "Ethical AI Council (DAO)", layer: "EXECUTION_RING", glyph: "CLOSED_LOOP", tags: ["GOV_GATE"] },
    { id: "mosquito_shield", label: "Operation MOSQUITO SHIELD", layer: "EXECUTION_RING", glyph: "CLOSED_LOOP", tags: [] },
    { id: "water_guardians", label: "Water Guardians Response", layer: "EXECUTION_RING", glyph: "CLOSED_LOOP", tags: [] },
    { id: "sankofa", label: "SANKOFA Protocol", layer: "EXECUTION_RING", glyph: "CLOSED_LOOP", tags: [] },
    { id: "libs", label: "Looted Infrastructure Bonds", layer: "EXECUTION_RING", glyph: "CLOSED_LOOP", tags: [] },
    { id: "ledger_audit", label: "Audit Hash Chain", layer: "LEDGER_SPINE", glyph: "LEDGER_SPINE", tags: [] },
    { id: "ledger_gov", label: "Governance Voting Log", layer: "LEDGER_SPINE", glyph: "LEDGER_SPINE", tags: [] },
    { id: "ledger_treasury", label: "Dividend Treasury Log", layer: "LEDGER_SPINE", glyph: "LEDGER_SPINE", tags: [] },
    { id: "ledger_bonds", label: "Bond Issuance Log", layer: "LEDGER_SPINE", glyph: "LEDGER_SPINE", tags: [] },
    { id: "zk_policy", label: "ZK Privacy Engine", layer: "PUBLIC_INTERFACE", glyph: null, tags: ["GATE"] },
    { id: "api_layer", label: "API Layer (Ministries/Banks)", layer: "PUBLIC_INTERFACE", glyph: null, tags: [] },
    { id: "public_dashboard", label: "Public Dashboard (Witness)", layer: "PUBLIC_INTERFACE", glyph: "PUBLIC_WITNESS", tags: ["WITNESS"] },
    { id: "drift_engine", label: "Drift Detection Engine", layer: "ORBITALS", glyph: "DRIFT", tags: [] },
    { id: "capture_alarm", label: "Capture Alarm System", layer: "ORBITALS", glyph: "CAPTURE_ALARM", tags: [] },
    { id: "self_attack", label: "Adversarial Simulation", layer: "ORBITALS", glyph: "SELF_ATTACK", tags: [] },
    { id: "key_rotation", label: "Key Rotation Protocol", layer: "ORBITALS", glyph: "KEY_ROTATION", tags: [] },
];

const EDGES: EdgeDef[] = [
    { id: "e1", s: "truth_engine", t: "scope_firewall", type: "constraint", label: "truth \u2192 scope", anim: true },
    { id: "e2", s: "scope_firewall", t: "compliance_gate", type: "constraint", label: "scope \u2192 compliance", anim: true },
    { id: "e3", s: "compliance_gate", t: "radx_consensus", type: "constraint", label: "execute only if lawful", anim: true },
    { id: "e4", s: "fl_ministry", t: "radx_consensus", type: "insight", label: "encrypted insights", dash: true },
    { id: "e5", s: "fl_university", t: "radx_consensus", type: "insight", label: "encrypted insights", dash: true },
    { id: "e6", s: "fl_community", t: "radx_consensus", type: "insight", label: "encrypted insights", dash: true },
    { id: "e7", s: "satellite", t: "radx_consensus", type: "signal", label: "hotspots" },
    { id: "e8", s: "iot_sensors", t: "radx_consensus", type: "signal", label: "local vectors" },
    { id: "e9", s: "ussd_gateway", t: "radx_consensus", type: "signal", label: "community reports" },
    { id: "e10", s: "radx_consensus", t: "ascc", type: "governance", label: "co-sign / veto", dash: true },
    { id: "e11", s: "radx_consensus", t: "dao", type: "governance", label: "model approvals", dash: true },
    { id: "e12", s: "ascc", t: "mosquito_shield", type: "governance", label: "co-sign gate", anim: true },
    { id: "e13", s: "dao", t: "mosquito_shield", type: "governance", label: "algorithm gate", anim: true },
    { id: "e14", s: "mosquito_shield", t: "water_guardians", type: "tasking", label: "dispatch + bounties", anim: true },
    { id: "e15", s: "water_guardians", t: "ledger_audit", type: "attestation", label: "proof-of-action", anim: true },
    { id: "e16", s: "sankofa", t: "libs", type: "record", label: "issue reparative finance" },
    { id: "e17", s: "libs", t: "ledger_bonds", type: "record", label: "bond ledger" },
    { id: "e18", s: "ascc", t: "ledger_gov", type: "record", label: "votes + veto", dash: true },
    { id: "e19", s: "dao", t: "ledger_gov", type: "record", label: "approvals + veto", dash: true },
    { id: "e20", s: "api_layer", t: "ledger_treasury", type: "record", label: "dividend logs", dash: true },
    { id: "e21", s: "ledger_audit", t: "zk_policy", type: "publish", label: "hash roots", dash: true },
    { id: "e22", s: "zk_policy", t: "api_layer", type: "constraint", label: "purpose-bound access", anim: true },
    { id: "e23", s: "api_layer", t: "public_dashboard", type: "publish", label: "redacted metrics" },
    { id: "e24", s: "public_dashboard", t: "radx_consensus", type: "feedback", label: "witness feedback", dash: true },
    { id: "e25", s: "drift_engine", t: "radx_consensus", type: "feedback", label: "drift blocks promotion", dash: true },
    { id: "e26", s: "capture_alarm", t: "public_dashboard", type: "alarm", label: "capture events", anim: true },
    { id: "e27", s: "self_attack", t: "capture_alarm", type: "alarm", label: "simulate abuse", dash: true },
    { id: "e28", s: "key_rotation", t: "ledger_gov", type: "record", label: "rotation + founder-less", dash: true },
];

// ═══════════════════════════════════════════════════════════════
// LAYOUT ENGINE
// ═══════════════════════════════════════════════════════════════
const LAYERS_ORDER = [
    "COVENANT_KERNEL",
    "MESH_INTELLIGENCE",
    "EXECUTION_RING",
    "LEDGER_SPINE",
    "PUBLIC_INTERFACE",
] as const;

type XY = { x: number; y: number };
type Layout = {
    pos: Record<string, XY>;
    viewBox: string;
    dims: { nodeW: number; nodeH: number };
};

function computeLayout(): Layout {
    // Fixed coordinate-space layout (SVG viewBox handles scaling)
    const W = 1800;
    const H = 1000;
    const padX = 60;
    const padTop = 80; // leave room for layer labels
    const padBot = 60;
    const usableW = W - padX * 2;
    const usableH = H - padTop - padBot;

    const cols = LAYERS_ORDER.length;
    const colGap = 24;
    const colW = (usableW - colGap * (cols - 1)) / cols;

    const nodeW = 200;
    const nodeH = 62;

    const byLayer: Record<string, NodeDef[]> = {};
    for (const n of NODES) {
        if (n.layer !== "ORBITALS") {
            (byLayer[n.layer] ||= []).push(n);
        }
    }

    const pos: Record<string, XY> = {};

    LAYERS_ORDER.forEach((layerId, idx) => {
        const nodes = byLayer[layerId] || [];
        const colX = padX + idx * (colW + colGap);
        const nodeX = colX + (colW - nodeW) / 2;
        const count = nodes.length;
        const totalNodeH = count * nodeH;
        const gap = Math.min(18, (usableH - totalNodeH) / (count + 1));
        const blockH = totalNodeH + gap * (count - 1);
        const startY = padTop + (usableH - blockH) / 2;

        nodes.forEach((n, i) => {
            pos[n.id] = { x: nodeX, y: startY + i * (nodeH + gap) };
        });
    });

    // Orbitals: place them in the gaps between columns, at top and bottom
    const col1Center = padX + 0.5 * (colW + colGap) + (colW - nodeW) / 2;
    const col3Center = padX + 2.5 * (colW + colGap) + (colW - nodeW) / 2;

    pos.drift_engine = { x: col1Center, y: padTop - 10 };
    pos.capture_alarm = { x: col3Center, y: padTop - 10 };
    pos.self_attack = { x: col1Center, y: padTop + usableH - nodeH + 10 };
    pos.key_rotation = { x: col3Center, y: padTop + usableH - nodeH + 10 };

    // Compute viewBox from actual positions
    const allPos = Object.values(pos);
    const minX = Math.min(...allPos.map((p) => p.x)) - 50;
    const minY = Math.min(...allPos.map((p) => p.y)) - 60;
    const maxX = Math.max(...allPos.map((p) => p.x)) + nodeW + 50;
    const maxY = Math.max(...allPos.map((p) => p.y)) + nodeH + 60;

    return {
        pos,
        viewBox: `${minX} ${minY} ${maxX - minX} ${maxY - minY}`,
        dims: { nodeW, nodeH },
    };
}

// ═══════════════════════════════════════════════════════════════
// Simulated live telemetry (client-side only)
// ═══════════════════════════════════════════════════════════════
type Moment = {
    quantum_id: string;
    initiator: string;
    receiver: string;
    description: string;
    trigger_type: string;
    elapsed_label: string;
    resonance_score: number;
};

const INITIATORS = ["RAD-X Engine", "Ministry FL", "IoT Sensor", "Satellite Feed", "ASCC Council", "DAO Vote", "ZK Engine", "Drift Monitor"];
const RECEIVERS = ["Mesh Consensus", "Mosquito Shield", "Water Guardians", "Ledger Spine", "Public Dashboard", "Audit Chain", "Treasury Log", "Bond Issuance"];
const DESCRIPTIONS = [
    "Malaria vector density anomaly detected in Lake Victoria basin",
    "Federated model update aggregated from 12 community nodes",
    "Governance vote completed: 94% consensus on water allocation",
    "Zero-knowledge proof verified for Nairobi health data batch",
    "Drift detection triggered: bias threshold exceeded in Region 4",
    "Key rotation ceremony initiated for multisig wallet #7",
    "Bond issuance: 500 LIBs for Mombasa infrastructure recovery",
    "Proof-of-action attestation from 3 field validators",
    "SANKOFA protocol activated: historical reparative analysis",
    "Capture alarm: unusual extraction pattern flagged and blocked",
];
const TRIGGERS = ["SENSOR", "GOVERNANCE", "FEDERATED", "ATTESTATION", "ALARM", "ROUTINE"];
const ELAPSED_LABELS = ["2s ago", "14s ago", "38s ago", "1m ago", "2m ago", "5m ago", "12m ago"];

function generateMoments(): Moment[] {
    const count = 3 + Math.floor(Math.random() * 4);
    return Array.from({ length: count }, (_, i) => ({
        quantum_id: `q-${i}-${Math.random().toString(36).slice(2, 8)}`,
        initiator: INITIATORS[Math.floor(Math.random() * INITIATORS.length)],
        receiver: RECEIVERS[Math.floor(Math.random() * RECEIVERS.length)],
        description: DESCRIPTIONS[Math.floor(Math.random() * DESCRIPTIONS.length)],
        trigger_type: TRIGGERS[Math.floor(Math.random() * TRIGGERS.length)],
        elapsed_label: ELAPSED_LABELS[Math.floor(Math.random() * ELAPSED_LABELS.length)],
        resonance_score: 0.6 + Math.random() * 0.35,
    }));
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════
export default function HyperSpine() {
    const [mounted, setMounted] = useState(false);
    const [moments, setMoments] = useState<Moment[]>([]);
    const [tick, setTick] = useState(0);

    // Only generate on client to avoid hydration mismatches
    useEffect(() => {
        setMounted(true);
        setMoments(generateMoments());
    }, []);

    useEffect(() => {
        if (!mounted) return;
        const interval = setInterval(() => {
            setMoments(generateMoments());
            setTick((t) => t + 1);
        }, 12000);
        return () => clearInterval(interval);
    }, [mounted]);

    const layout = useMemo(() => computeLayout(), []);
    const { pos: POS, viewBox, dims } = layout;
    const NODE_W = dims.nodeW;
    const NODE_H = dims.nodeH;

    const [selected, setSelected] = useState<string | null>(null);
    const [hovEdge, setHovEdge] = useState<string | null>(null);
    const [activeFilter, setActiveFilter] = useState<string | null>(null);

    const selNode = NODES.find((n) => n.id === selected);
    const selGlyph = selNode?.glyph ? GLYPHS[selNode.glyph] : null;
    const selLayer = selNode
        ? THEME.layers[selNode.layer as keyof typeof THEME.layers]
        : null;

    const connEdges = useMemo(() => {
        if (!selected) return new Set<string>();
        return new Set(
            EDGES.filter((e) => e.s === selected || e.t === selected).map((e) => e.id)
        );
    }, [selected]);

    const connNodes = useMemo(() => {
        if (!selected) return new Set<string>();
        const s = new Set<string>([selected]);
        EDGES.forEach((e) => {
            if (e.s === selected) s.add(e.t);
            if (e.t === selected) s.add(e.s);
        });
        return s;
    }, [selected]);

    const edgeTypes = useMemo(() => [...new Set(EDGES.map((e) => e.type))], []);

    const nc = useCallback(
        (id: string) => {
            const p = POS[id];
            return p ? { x: p.x + NODE_W / 2, y: p.y + NODE_H / 2 } : { x: 0, y: 0 };
        },
        [POS, NODE_W, NODE_H]
    );

    const edgePath = useCallback(
        (sid: string, tid: string) => {
            const s = nc(sid);
            const t = nc(tid);
            const dx = t.x - s.x;
            const dy = t.y - s.y;
            if (Math.abs(dx) > Math.abs(dy) * 0.5) {
                const cx = dx * 0.4;
                return `M${s.x} ${s.y} C${s.x + cx} ${s.y},${t.x - cx} ${t.y},${t.x} ${t.y}`;
            }
            const my = (s.y + t.y) / 2;
            return `M${s.x} ${s.y} C${s.x} ${my},${t.x} ${my},${t.x} ${t.y}`;
        },
        [nc]
    );

    const layerBounds = useCallback(
        (lid: string) => {
            const ns = NODES.filter((n) => n.layer === lid);
            if (!ns.length) return null;
            let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
            ns.forEach((n) => {
                const p = POS[n.id];
                if (!p) return;
                x0 = Math.min(x0, p.x);
                y0 = Math.min(y0, p.y);
                x1 = Math.max(x1, p.x + NODE_W);
                y1 = Math.max(y1, p.y + NODE_H);
            });
            const pad = 28;
            return { x: x0 - pad, y: y0 - pad, w: x1 - x0 + pad * 2, h: y1 - y0 + pad * 2 };
        },
        [POS, NODE_W, NODE_H]
    );

    const zones = useMemo(
        () =>
            [...LAYERS_ORDER].reverse().map((l) => ({
                layer: l,
                bounds: layerBounds(l),
                style: THEME.layers[l as keyof typeof THEME.layers],
            })).filter((z) => z.bounds),
        [layerBounds]
    );

    const totalNodes = NODES.length;
    const totalEdges = EDGES.length;
    const totalMoments = 1247 + tick * 3;
    const avgResonance = mounted && moments.length > 0
        ? (moments.reduce((a, m) => a + m.resonance_score, 0) / moments.length * 100).toFixed(0)
        : "87";

    return (
        <>
            <GridNav />
            <div className="fixed inset-0 flex flex-col overflow-hidden font-mono" style={{ background: THEME.bg, top: '48px' }}>
            <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .ins { animation: fadeIn .18s ease; }
        .nh:hover { filter: brightness(1.25) !important; cursor: pointer; }
        @keyframes orbPulse { 0%,100% { opacity: .65; } 50% { opacity: .95; } }
        .op { animation: orbPulse 3s ease-in-out infinite; }
        @keyframes edgeFlow { to { stroke-dashoffset: -24; } }
        .edge-anim { stroke-dasharray: 4 8; animation: edgeFlow 1.2s linear infinite; }
        .ed { stroke-dasharray: 6 6; }
        @keyframes nodePulseGlow { 0% { opacity: .15; } 50% { opacity: .4; } 100% { opacity: .15; } }
        @keyframes scanline { 0% { transform: translateY(-100%); } 100% { transform: translateY(100vh); } }
        .scanline-fx { position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(34,197,94,0.06), transparent); animation: scanline 8s linear infinite; pointer-events: none; z-index: 1; }
      `}</style>

            {/* Scanline */}
            <div className="scanline-fx" />

            {/* Background grid */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ opacity: 0.03 }}>
                <defs>
                    <pattern id="bgGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" />
                    </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#bgGrid)" />
            </svg>

            {/* ── TOP BAR ─────────────────────────────────────── */}
            <header className="relative z-20 flex flex-wrap items-center justify-between gap-3 px-5 pt-4 pb-2">
                {/* Title + stats */}
                <div className="flex items-center gap-3 flex-wrap">
                    <div
                        className="px-4 py-2 rounded-xl"
                        style={{ background: "rgba(0,0,0,0.65)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(12px)" }}
                    >
                        <div className="text-[13px] font-bold tracking-wide" style={{ color: "#fff" }}>
                            {"\u27C1"} Hyper-Spine Architecture
                        </div>
                        <div className="text-[10px] mt-0.5" style={{ color: "rgba(255,255,255,0.38)" }}>
                            {"MoStar Grid \u00B7 5 Layers \u00B7 "}
                            {totalNodes}{" Nodes \u00B7 "}{totalEdges}{" Edges \u00B7 LIVE"}
                        </div>
                    </div>

                    <div className="flex gap-1.5 flex-wrap">
                        {[
                            { label: "NODES", val: String(totalNodes), color: "#60a5fa" },
                            { label: "MOMENTS", val: `${(totalMoments / 1000).toFixed(1)}K`, color: "#22c55e" },
                            { label: "24H", val: "847", color: "#fbbf24" },
                            { label: "RES", val: `${avgResonance}%`, color: "#a78bfa" },
                            { label: "AGENTS", val: "12", color: "#fb7185" },
                        ].map((s) => (
                            <div
                                key={s.label}
                                className="px-3 py-1 rounded-full"
                                style={{ background: "rgba(0,0,0,0.55)", border: `1px solid ${s.color}33`, backdropFilter: "blur(8px)" }}
                            >
                                <span className="text-[8px] font-bold tracking-wider" style={{ color: "rgba(255,255,255,0.3)" }}>
                                    {s.label}{" "}
                                </span>
                                <span className="text-[11px] font-bold" style={{ color: s.color }}>
                                    {s.val}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Edge filter */}
                <div
                    className="flex gap-1 rounded-full px-3 py-1.5"
                    style={{ background: "rgba(0,0,0,0.55)", border: "1px solid rgba(255,255,255,0.06)", backdropFilter: "blur(10px)" }}
                >
                    <span
                        className="text-[8.5px] font-bold tracking-widest flex items-center mr-1"
                        style={{ color: "rgba(255,255,255,0.22)" }}
                    >
                        EDGES
                    </span>
                    {edgeTypes.map((t) => (
                        <button
                            key={t}
                            onClick={() => setActiveFilter(activeFilter === t ? null : t)}
                            className="rounded-full px-2.5 py-0.5 text-[8.5px] font-semibold transition-all"
                            style={{
                                background: activeFilter === t ? THEME.edges[t] + "22" : "transparent",
                                border: `1px solid ${activeFilter === t ? THEME.edges[t] : "rgba(255,255,255,0.07)"}`,
                                color: activeFilter === t ? THEME.edges[t] : "rgba(255,255,255,0.32)",
                                cursor: "pointer",
                            }}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </header>

            {/* ── MAIN CANVAS ────────────────────────────────── */}
            <div className="relative flex-1 min-h-0">
                {/* Inspector panel */}
                {selNode && (
                    <div
                        className="ins absolute top-3 right-5 z-20 w-72 rounded-2xl p-3.5"
                        style={{
                            background: "rgba(0,0,0,0.82)",
                            border: `1px solid ${selLayer?.stroke || "#333"}`,
                            backdropFilter: "blur(14px)",
                            boxShadow: `0 0 40px ${selLayer?.glow || "transparent"}`,
                        }}
                    >
                        <div className="flex justify-between items-start">
                            <div>
                                {selGlyph && <span className="text-2xl">{selGlyph.sym}</span>}
                                <div className="text-xs font-bold mt-1" style={{ color: selLayer?.text || "#fff" }}>
                                    {selNode.label}
                                </div>
                                <div className="text-[8px] font-bold tracking-widest mt-0.5" style={{ color: selLayer?.stroke || "#999" }}>
                                    {selNode.layer.replace(/_/g, " ")}
                                </div>
                            </div>
                            <button
                                onClick={() => setSelected(null)}
                                className="rounded-lg px-2 py-0.5 text-[10px] cursor-pointer"
                                style={{ background: "rgba(255,255,255,0.07)", border: "none", color: "#fff" }}
                            >
                                {"\u2715"}
                            </button>
                        </div>

                        {selGlyph && (
                            <div className="mt-2.5 p-2 rounded-lg" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
                                <div className="text-[8px] font-bold tracking-widest" style={{ color: "rgba(255,255,255,0.28)" }}>GLYPH</div>
                                <div className="text-[10px] mt-1 leading-snug" style={{ color: "rgba(255,255,255,0.68)" }}>{selGlyph.desc}</div>
                            </div>
                        )}

                        {selNode.tags.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                                {selNode.tags.map((t) => (
                                    <span
                                        key={t}
                                        className="text-[8px] px-2 py-0.5 rounded-full"
                                        style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)", color: selLayer?.text || "#ccc" }}
                                    >
                                        {t}
                                    </span>
                                ))}
                            </div>
                        )}

                        <div className="mt-3">
                            <div className="text-[8px] font-bold tracking-widest mb-1" style={{ color: "rgba(255,255,255,0.25)" }}>
                                CONNECTIONS ({EDGES.filter((e) => e.s === selected || e.t === selected).length})
                            </div>
                            {EDGES.filter((e) => e.s === selected || e.t === selected).map((e) => {
                                const out = e.s === selected;
                                const oid = out ? e.t : e.s;
                                const on = NODES.find((n) => n.id === oid);
                                return (
                                    <div
                                        key={e.id}
                                        onClick={() => setSelected(oid)}
                                        className="text-[9px] mt-1 flex gap-1.5 items-center cursor-pointer rounded p-1"
                                        style={{ background: "rgba(255,255,255,0.025)" }}
                                    >
                                        <span className="text-[8px] min-w-3.5" style={{ color: THEME.edges[e.type] }}>
                                            {out ? "\u2192" : "\u2190"}
                                        </span>
                                        <span className="text-[8px]" style={{ color: THEME.edges[e.type] }}>{e.type}</span>
                                        <span className="overflow-hidden text-ellipsis whitespace-nowrap" style={{ color: "rgba(255,255,255,0.6)" }}>
                                            {on?.label || oid}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* SVG Canvas */}
                <svg viewBox={viewBox} preserveAspectRatio="xMidYMid meet" className="w-full h-full block">
                    <defs>
                        {Object.entries(THEME.layers).map(([k, v]) => (
                            <g key={`defs-${k}`}>
                                <filter id={`glow-${k}`} x="-50%" y="-50%" width="200%" height="200%">
                                    <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b" />
                                    <feFlood floodColor={v.stroke} floodOpacity=".35" result="c" />
                                    <feComposite in="c" in2="b" operator="in" result="g" />
                                    <feMerge>
                                        <feMergeNode in="g" />
                                        <feMergeNode in="SourceGraphic" />
                                    </feMerge>
                                </filter>
                                <linearGradient id={`grad-zone-${k}`} x1="0%" y1="0%" x2="100%" y2="100%">
                                    <stop offset="0%" stopColor={v.stroke} stopOpacity="0.08" />
                                    <stop offset="100%" stopColor={v.stroke} stopOpacity="0.01" />
                                </linearGradient>
                                <linearGradient id={`grad-node-${k}`} x1="0%" y1="0%" x2="0%" y2="100%">
                                    <stop offset="0%" stopColor={v.stroke} stopOpacity="0.20" />
                                    <stop offset="100%" stopColor={v.stroke} stopOpacity="0.04" />
                                </linearGradient>
                            </g>
                        ))}
                        <filter id="ge" x="-20%" y="-20%" width="140%" height="140%">
                            <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" />
                        </filter>
                    </defs>

                    {/* Layer zones */}
                    {zones.map((z) => (
                        <g key={z.layer}>
                            <rect
                                x={z.bounds!.x}
                                y={z.bounds!.y}
                                width={z.bounds!.w}
                                height={z.bounds!.h}
                                rx={18}
                                fill={`url(#grad-zone-${z.layer})`}
                                stroke={z.style.stroke}
                                strokeWidth={0.8}
                                strokeOpacity={0.2}
                            />
                            <path
                                d={`M ${z.bounds!.x + 18} ${z.bounds!.y} L ${z.bounds!.x + z.bounds!.w - 18} ${z.bounds!.y}`}
                                stroke={z.style.stroke}
                                strokeWidth={1.2}
                                opacity={0.35}
                                strokeLinecap="round"
                            />
                            <text
                                x={z.bounds!.x + 14}
                                y={z.bounds!.y + 16}
                                fill={z.style.stroke}
                                opacity={0.4}
                                fontSize={7}
                                fontWeight={700}
                                letterSpacing={2}
                                fontFamily="monospace"
                            >
                                {z.style.label}
                            </text>
                        </g>
                    ))}

                    {/* Edges */}
                    {EDGES.map((e) => {
                        const path = edgePath(e.s, e.t);
                        const color = THEME.edges[e.type] || "#555";
                        const conn = connEdges.has(e.id);
                        const hov = hovEdge === e.id;
                        const off = activeFilter && e.type !== activeFilter;
                        const op = off ? 0.04 : conn ? 0.9 : hov ? 0.8 : 0.3;
                        const sw = conn ? 2.5 : hov ? 2 : 1.2;
                        const animating = !off && (e.anim || conn);

                        return (
                            <g key={e.id} onMouseEnter={() => setHovEdge(e.id)} onMouseLeave={() => setHovEdge(null)}>
                                <path
                                    d={path}
                                    fill="none"
                                    stroke={color}
                                    strokeWidth={sw}
                                    opacity={op}
                                    className={animating ? "edge-anim" : e.dash ? "ed" : ""}
                                    strokeLinecap="round"
                                />
                                {animating && (
                                    <path d={path} fill="none" stroke={color} strokeWidth={sw + 5} opacity={0.1} filter="url(#ge)" />
                                )}
                                {animating && (
                                    <circle r={2} fill={color} opacity={0.7}>
                                        <animateMotion dur="2s" repeatCount="indefinite" path={path} />
                                    </circle>
                                )}
                                {/* edge label on hover/connect */}
                                {(hov || conn) && !off && e.label && (() => {
                                    const s = nc(e.s), t = nc(e.t);
                                    const mx = (s.x + t.x) / 2, my = (s.y + t.y) / 2;
                                    const w = e.label.length * 5.5 + 12;
                                    return (
                                        <g>
                                            <rect
                                                x={mx - w / 2} y={my - 14} width={w} height={14} rx={4}
                                                fill="rgba(6,7,11,0.92)" stroke={color} strokeWidth={0.5} strokeOpacity={0.4}
                                            />
                                            <text x={mx} y={my - 4} fill={color} fontSize={7} textAnchor="middle" fontWeight={600} fontFamily="monospace">
                                                {e.label}
                                            </text>
                                        </g>
                                    );
                                })()}
                            </g>
                        );
                    })}

                    {/* Nodes */}
                    {NODES.map((n) => {
                        const p = POS[n.id];
                        if (!p) return null;
                        const ls = THEME.layers[n.layer as keyof typeof THEME.layers];
                        const g = n.glyph ? GLYPHS[n.glyph] : null;
                        const sel = selected === n.id;
                        const conn = selected && connNodes.has(n.id) && !sel;
                        const dim = selected && !connNodes.has(n.id);
                        const orb = n.layer === "ORBITALS";

                        return (
                            <g
                                key={n.id}
                                className={`nh ${orb ? "op" : ""}`}
                                onClick={() => setSelected(n.id === selected ? null : n.id)}
                                filter={sel ? `url(#glow-${n.layer})` : undefined}
                                opacity={dim ? 0.18 : 1}
                                style={{ transition: "opacity .2s" }}
                            >
                                {/* pulse ring */}
                                {!sel && !dim && (
                                    <rect
                                        x={p.x - 3} y={p.y - 3} width={NODE_W + 6} height={NODE_H + 6} rx={14}
                                        fill="none" stroke={ls.stroke} strokeWidth={1} opacity={0.25}
                                        style={{ animation: "nodePulseGlow 2.5s ease-in-out infinite" }}
                                    />
                                )}
                                {sel && (
                                    <rect
                                        x={p.x - 3} y={p.y - 3} width={NODE_W + 6} height={NODE_H + 6} rx={14}
                                        fill="none" stroke={ls.stroke} strokeWidth={1.5} strokeOpacity={0.8} strokeDasharray="4 4"
                                    />
                                )}
                                {conn && (
                                    <rect
                                        x={p.x - 2} y={p.y - 2} width={NODE_W + 4} height={NODE_H + 4} rx={13}
                                        fill="none" stroke={ls.stroke} strokeWidth={0.7} strokeOpacity={0.5}
                                    />
                                )}
                                {/* body */}
                                <rect
                                    x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx={11}
                                    fill={`url(#grad-node-${n.layer})`}
                                    stroke={ls.stroke} strokeWidth={sel ? 1.8 : 0.8} strokeOpacity={sel ? 1 : 0.4}
                                />
                                <path
                                    d={`M ${p.x + 12} ${p.y + 1} L ${p.x + NODE_W - 12} ${p.y + 1}`}
                                    stroke={ls.stroke} strokeWidth={1.2} opacity={0.5} strokeLinecap="round"
                                />
                                {/* glyph */}
                                {g && (
                                    <text x={p.x + 14} y={p.y + 28} fontSize={17} fill={ls.stroke} opacity={0.85}>
                                        {g.sym}
                                    </text>
                                )}
                                {/* sublabel */}
                                <text
                                    x={p.x + (g ? 38 : 12)} y={p.y + 18}
                                    fontSize={6.5} fontWeight={700} letterSpacing={1.2}
                                    fill={ls.stroke} opacity={0.5} fontFamily="monospace"
                                >
                                    {orb ? "ORBITAL" : n.layer.replace(/_/g, " ")}
                                </text>
                                {/* label */}
                                <text
                                    x={p.x + (g ? 38 : 12)} y={p.y + 32}
                                    fontSize={9.5} fontWeight={600} fill={ls.text} fontFamily="monospace"
                                >
                                    {n.label.length > 28 ? n.label.slice(0, 27) + "\u2026" : n.label}
                                </text>
                                {/* tags */}
                                {n.tags.length > 0 && (
                                    <text
                                        x={p.x + (g ? 38 : 12)} y={p.y + 44}
                                        fontSize={5.5} fontWeight={700} letterSpacing={0.8}
                                        fill={ls.stroke} opacity={0.35} fontFamily="monospace"
                                    >
                                        {n.tags.join(" \u00B7 ")}
                                    </text>
                                )}
                                {/* connector dots */}
                                <circle cx={p.x + NODE_W / 2} cy={p.y} r={2} fill={ls.stroke} opacity={0.2} />
                                <circle cx={p.x + NODE_W / 2} cy={p.y + NODE_H} r={2} fill={ls.stroke} opacity={0.2} />
                                <circle cx={p.x} cy={p.y + NODE_H / 2} r={2} fill={ls.stroke} opacity={0.15} />
                                <circle cx={p.x + NODE_W} cy={p.y + NODE_H / 2} r={2} fill={ls.stroke} opacity={0.15} />
                            </g>
                        );
                    })}

                    {/* Watermark */}
                    <text
                        x={(parseFloat(viewBox.split(" ")[0]) + parseFloat(viewBox.split(" ")[2])) / 2 + parseFloat(viewBox.split(" ")[0])}
                        y={parseFloat(viewBox.split(" ")[1]) + 14}
                        fontSize={7}
                        fill="rgba(255,255,255,0.06)"
                        textAnchor="middle"
                        fontWeight={700}
                        letterSpacing={3}
                        fontFamily="monospace"
                    >
                        {"MSTR-\u26A1 \u00B7 AFRICAN FLAME INITIATIVE \u00B7 SOVEREIGN GRID"}
                    </text>
                </svg>

                {/* Live feed panel */}
                {mounted && moments.length > 0 && (
                    <div
                        className="ins absolute bottom-3 right-5 z-20 w-80 rounded-xl p-3 max-h-52 overflow-hidden"
                        style={{ background: "rgba(0,0,0,0.65)", border: "1px solid rgba(255,255,255,0.07)", backdropFilter: "blur(10px)" }}
                    >
                        <div className="flex justify-between mb-1.5">
                            <span className="text-[9px] font-bold tracking-widest" style={{ color: "rgba(255,255,255,0.38)" }}>
                                LIVE MOMENTS
                            </span>
                            <span className="text-[8px] font-bold" style={{ color: "#22c55e" }}>
                                {"\u25CF"}{" "}{moments[0]?.elapsed_label ?? "\u2014"}
                            </span>
                        </div>
                        {moments.slice(0, 5).map((m, i) => (
                            <div
                                key={m.quantum_id || i}
                                className="pl-2 mb-1.5"
                                style={{ borderLeft: `2px solid ${THEME.edges.signal}` }}
                            >
                                <div className="text-[9px]" style={{ color: "rgba(255,255,255,0.6)" }}>
                                    <span style={{ color: THEME.edges.signal }}>{m.initiator}</span>
                                    <span style={{ color: "rgba(255,255,255,0.25)" }}>{" \u2192 "}</span>
                                    <span style={{ color: "rgba(255,255,255,0.45)" }}>{m.receiver}</span>
                                </div>
                                <div className="text-[7.5px] mt-0.5" style={{ color: "rgba(255,255,255,0.3)" }}>
                                    {m.description.slice(0, 68)}{m.description.length > 68 ? "\u2026" : ""}
                                </div>
                                <div className="flex gap-2 mt-0.5">
                                    <span className="text-[7.5px]" style={{ color: "#a78bfa" }}>{m.trigger_type}</span>
                                    <span className="text-[7.5px]" style={{ color: "rgba(255,255,255,0.22)" }}>{m.elapsed_label}</span>
                                    <span className="text-[7.5px]" style={{ color: "#22c55e" }}>{(m.resonance_score * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* ── FOOTER ──────────────────────────────────────── */}
            <footer className="relative z-20 px-5 py-2">
                <div className="text-[10px]" style={{ color: "rgba(255,255,255,0.18)" }}>
                    Click nodes to inspect / filter edges above / animated packets indicate active flows
                </div>
            </footer>
        </>
    );
}
