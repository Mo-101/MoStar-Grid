"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useGridTelemetry } from "@/hooks/useGridTelemetry";
import GridNav from "@/components/GridNav";

// ═══════════════════════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════════════════════
const THEME = {
    bg: "#06070b",
    layers: {
        COVENANT_KERNEL: { stroke: "#22c55e", fill: "rgba(34,197,94,0.05)", glow: "rgba(34,197,94,0.35)", text: "#d1fae5", label: "LAYER 1 — COVENANT KERNEL" },
        MESH_INTELLIGENCE: { stroke: "#60a5fa", fill: "rgba(96,165,250,0.04)", glow: "rgba(96,165,250,0.30)", text: "#dbeafe", label: "LAYER 2 — DISTRIBUTED INTELLIGENCE MESH" },
        EXECUTION_RING: { stroke: "#fb7185", fill: "rgba(251,113,133,0.04)", glow: "rgba(251,113,133,0.30)", text: "#ffe4e6", label: "LAYER 3 — OPERATIONAL EXECUTION RING" },
        LEDGER_SPINE: { stroke: "#a78bfa", fill: "rgba(167,139,250,0.04)", glow: "rgba(167,139,250,0.30)", text: "#ede9fe", label: "LAYER 4 — SOVEREIGN LEDGER SPINE" },
        PUBLIC_INTERFACE: { stroke: "#fbbf24", fill: "rgba(251,191,36,0.04)", glow: "rgba(251,191,36,0.25)", text: "#fffbeb", label: "LAYER 5 — PUBLIC SOVEREIGNTY INTERFACE" },
        ORBITALS: { stroke: "#94a3b8", fill: "rgba(148,163,184,0.03)", glow: "rgba(148,163,184,0.18)", text: "#e2e8f0", label: "HYPER-INTELLIGENCE ORBITALS" },
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
    },
};

const GLYPHS: Record<string, { sym: string; name: string; desc: string }> = {
    COVENANT_GATE: { sym: "⟁", name: "Covenant Gate", desc: "Immutable execution barrier — Truth + Scope + Compliance" },
    MESH_CONSENSUS: { sym: "⟡", name: "Mesh Consensus", desc: "Distributed intelligence — no central brain" },
    CLOSED_LOOP: { sym: "◉", name: "Closed Loop", desc: "Request → gate → execute → log → witness → feedback" },
    LEDGER_SPINE: { sym: "⎔", name: "Ledger Spine", desc: "Tamper-evident accounting backbone" },
    PUBLIC_WITNESS: { sym: "☉", name: "Public Witness", desc: "Distributed memory + capture deterrence" },
    DRIFT: { sym: "Δ", name: "Drift Detector", desc: "Detects bias/drift/governance decay" },
    CAPTURE_ALARM: { sym: "⚠", name: "Capture Alarm", desc: "Triggers on prohibited purpose/extraction" },
    SELF_ATTACK: { sym: "☍", name: "Self-Attack", desc: "Simulates abuse vectors before adversaries do" },
    KEY_ROTATION: { sym: "⇄", name: "Key Rotation", desc: "Founder-less ops + multisig rotation ritual" },
};

const NODES = [
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

const EDGES = [
    { id: "e1", s: "truth_engine", t: "scope_firewall", type: "constraint", label: "truth → scope", anim: true },
    { id: "e2", s: "scope_firewall", t: "compliance_gate", type: "constraint", label: "scope → compliance", anim: true },
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

type XY = { x: number; y: number };

type Layout = {
    pos: Record<string, XY>;
    viewBox: string;
    dims: { nodeW: number; nodeH: number };
};

const LAYERS_ORDER = ["COVENANT_KERNEL", "MESH_INTELLIGENCE", "EXECUTION_RING", "LEDGER_SPINE", "PUBLIC_INTERFACE"] as const;

function clamp(n: number, a: number, b: number) {
    return Math.max(a, Math.min(b, n));
}

function computeLayeredLayout(width: number, height: number): Layout {
    const padX = Math.max(24, width * 0.03);
    const padY = Math.max(24, height * 0.06);

    const usableW = Math.max(320, width - padX * 2);
    const usableH = Math.max(240, height - padY * 2);

    const cols = LAYERS_ORDER.length;
    const colGap = usableW * 0.03;
    const colW = (usableW - colGap * (cols - 1)) / cols;

    const nodeW = clamp(Math.floor(colW * 0.9), 170, 240);
    const nodeH = clamp(Math.floor(usableH * 0.09), 54, 72);

    const byLayer: Record<string, any[]> = {};
    for (const n of NODES) (byLayer[n.layer] ||= []).push(n);

    const pos: Record<string, XY> = {};

    // layout columns
    LAYERS_ORDER.forEach((layerId, idx) => {
        const nodes = (byLayer[layerId] || []).slice();
        const x = padX + idx * (colW + colGap) + (colW - nodeW) / 2;

        const count = Math.max(1, nodes.length);
        const rowGap = clamp((usableH - nodeH * count) / (count + 1), 10, 40);

        nodes.forEach((n, i) => {
            const y = padY + rowGap * (i + 1) + nodeH * i;
            pos[n.id] = { x, y };
        });
    });

    // orbitals pinned top/bottom within the same frame
    const orbitalPad = 10;
    const orbitalXLeft = padX + 1 * (colW + colGap) + (colW - nodeW) / 2;
    const orbitalXRight = padX + 3 * (colW + colGap) + (colW - nodeW) / 2;

    pos.drift_engine = { x: orbitalXLeft, y: padY + orbitalPad };
    pos.capture_alarm = { x: orbitalXRight, y: padY + orbitalPad };
    pos.self_attack = { x: orbitalXLeft, y: padY + usableH - nodeH - orbitalPad };
    pos.key_rotation = { x: orbitalXRight, y: padY + usableH - nodeH - orbitalPad };

    const all = Object.values(pos);
    const minX = Math.min(...all.map((p) => p.x)) - 40;
    const minY = Math.min(...all.map((p) => p.y)) - 90;
    const maxX = Math.max(...all.map((p) => p.x)) + nodeW + 40;
    const maxY = Math.max(...all.map((p) => p.y)) + nodeH + 110;

    return {
        pos,
        viewBox: `${minX} ${minY} ${maxX - minX} ${maxY - minY}`,
        dims: { nodeW, nodeH },
    };
}

function fmt(n: number) {
    return n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n ?? 0);
}

function ago(ts: string) {
    if (!ts) return "—";
    const d = Date.now() - new Date(ts).getTime();
    if (d < 60000) return `${Math.floor(d / 1000)}s ago`;
    if (d < 3600000) return `${Math.floor(d / 60000)}m ago`;
    return `${Math.floor(d / 3600000)}h ago`;
}

export default function HyperSpinePage() {
    const { telemetry, loading } = useGridTelemetry(12000);
    const graph = telemetry?.graph;
    const backend = telemetry?.backend;
    const moments = telemetry?.log?.entries ?? [];
    const isLive = backend?.ok && graph?.ok;

    const rootRef = useRef<HTMLDivElement | null>(null);
    const [size, setSize] = useState({ w: 1400, h: 800 });

    useEffect(() => {
        if (!rootRef.current) return;
        const ro = new ResizeObserver((entries) => {
            const r = entries[0]?.contentRect;
            if (!r) return;
            setSize({ w: Math.floor(r.width), h: Math.floor(r.height) });
        });
        ro.observe(rootRef.current);
        return () => ro.disconnect();
    }, []);

    const { pos: POS, viewBox, dims } = useMemo(() => computeLayeredLayout(size.w, size.h), [size.w, size.h]);
    const NODE_W = dims.nodeW;
    const NODE_H = dims.nodeH;

    const [selected, setSelected] = useState<string | null>(null);
    const [hovEdge, setHovEdge] = useState<string | null>(null);
    const [activeFilter, setActiveFilter] = useState<string | null>(null);

    const selNode = NODES.find((n) => n.id === selected);
    const selGlyph = selNode?.glyph ? GLYPHS[selNode.glyph] : null;
    const selLayer = selNode ? THEME.layers[selNode.layer as keyof typeof THEME.layers] : null;

    const connEdges = useMemo(() => {
        if (!selected) return new Set<string>();
        return new Set(EDGES.filter((e) => e.s === selected || e.t === selected).map((e) => e.id));
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

    const edgeTypes = [...new Set(EDGES.map((e) => e.type))];

    const layerNodeCount = (lid: string) => {
        const v = graph?.layer_nodes?.[lid];
        return v ? fmt(v) : null;
    };
    const layerMoments = (lid: string) => graph?.layer_moments?.[lid] ?? null;

    const statusDot = loading ? "⏳" : isLive ? "🟢" : "🔴";
    const statusLabel = loading ? "CONNECTING" : isLive ? "LIVE" : "OFFLINE";

    const nc = (id: string) => {
        const p = POS[id];
        return p ? { x: p.x + NODE_W / 2, y: p.y + NODE_H / 2 } : { x: 0, y: 0 };
    };

    const edgePath = (sid: string, tid: string) => {
        const s = nc(sid), t = nc(tid);
        const dy = t.y - s.y;
        const dx = t.x - s.x;
        if (Math.abs(dx) > Math.abs(dy) * 0.6) {
            return `M${s.x} ${s.y} C${s.x + dx * 0.4} ${s.y},${t.x - dx * 0.4} ${t.y},${t.x} ${t.y}`;
        }
        const my = (s.y + t.y) / 2;
        return `M${s.x} ${s.y} C${s.x} ${my},${t.x} ${my},${t.x} ${t.y}`;
    };

    const layerBounds = (lid: string) => {
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
        const pad = 30;
        return { x: x0 - pad, y: y0 - pad, w: x1 - x0 + pad * 2, h: y1 - y0 + pad * 2 };
    };

    const zones = useMemo(
        () =>
            ["PUBLIC_INTERFACE", "LEDGER_SPINE", "EXECUTION_RING", "MESH_INTELLIGENCE", "COVENANT_KERNEL"]
                .map((l) => ({ layer: l, bounds: layerBounds(l), style: THEME.layers[l as keyof typeof THEME.layers] }))
                .filter((z) => z.bounds),
        [POS, NODE_W, NODE_H]
    );

    return (
        <div ref={rootRef} style={{ position: "fixed", inset: 0, background: THEME.bg, overflow: "hidden", fontFamily: "'SF Mono','Fira Code','Consolas',monospace" }}>
            <style>{`
        @keyframes fadeIn{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
        .ins{animation:fadeIn .18s ease;}
        .nh:hover{filter:brightness(1.25)!important;cursor:pointer;}
        @keyframes orbPulse{0%,100%{opacity:.65;}50%{opacity:.95;}}
        .op{animation:orbPulse 3s ease-in-out infinite;}

        @keyframes edgeFlow { to { stroke-dashoffset: -24; } }
        .edge-anim { stroke-dasharray: 4 8; animation: edgeFlow 1.2s linear infinite; }
        .ed{stroke-dasharray:6 6;}
        @keyframes nodePulseGlow { 0% { opacity: .18; } 50% { opacity: .45; } 100% { opacity: .18; } }
      `}</style>

            {/* Global Nav */}
            <div style={{ position: "absolute", top: 16, right: 20, zIndex: 100, width: "calc(100% - 40px)", display: "flex", justifyContent: "flex-end", pointerEvents: "none" }}>
                <div style={{ pointerEvents: "all" }}>
                    <GridNav />
                </div>
            </div>

            {/* Title bar */}
            <div style={{ position: "absolute", top: 16, left: 20, zIndex: 20, display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ background: "rgba(0,0,0,0.65)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: "9px 16px", backdropFilter: "blur(12px)" }}>
                    <div style={{ color: "#fff", fontSize: 13, fontWeight: 700, letterSpacing: 0.4 }}>⟁ Hyper-Spine Architecture</div>
                    <div style={{ color: "rgba(255,255,255,0.38)", fontSize: 10, marginTop: 2 }}>MoStar Grid · 5 Layers · 27 Nodes · 28 Edges · {statusDot} {statusLabel}</div>
                </div>

                {graph && (
                    <div style={{ display: "flex", gap: 5 }}>
                        {[
                            { label: "NODES", val: fmt(graph.total_nodes ?? 0), color: "#60a5fa" },
                            { label: "MOMENTS", val: fmt(graph.stats?.totalMoments ?? 0), color: "#22c55e" },
                            { label: "24H", val: fmt(graph.moments_24h ?? 0), color: "#fbbf24" },
                            { label: "RES", val: `${((graph.stats?.avgResonance || 0) * 100).toFixed(0)}%`, color: "#a78bfa" },
                            { label: "AGENTS", val: fmt(typeof graph.agents === "number" ? graph.agents : Array.isArray(graph.agents) ? graph.agents.length : 0), color: "#fb7185" },
                        ].map((s) => (
                            <div key={s.label} style={{ background: "rgba(0,0,0,0.55)", border: `1px solid ${s.color}33`, borderRadius: 20, padding: "4px 11px", backdropFilter: "blur(8px)" }}>
                                <span style={{ color: "rgba(255,255,255,0.3)", fontSize: 8, fontWeight: 700, letterSpacing: 0.8 }}>{s.label} </span>
                                <span style={{ color: s.color, fontSize: 11, fontWeight: 700 }}>{s.val}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Edge filter */}
            <div style={{ position: "absolute", top: 16, left: 0, right: 0, display: "flex", justifyContent: "center", zIndex: 18, pointerEvents: "none" }}>
                <div style={{ display: "flex", gap: 4, background: "rgba(0,0,0,0.55)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 30, padding: "5px 12px", backdropFilter: "blur(10px)", pointerEvents: "all", marginTop: 10 }}>
                    <span style={{ color: "rgba(255,255,255,0.22)", fontSize: 8.5, fontWeight: 700, letterSpacing: 1, display: "flex", alignItems: "center", marginRight: 3 }}>EDGES</span>
                    {edgeTypes.map((t) => (
                        <button
                            key={t}
                            onClick={() => setActiveFilter(activeFilter === t ? null : t)}
                            style={{
                                background: activeFilter === t ? (THEME.edges as any)[t] + "22" : "transparent",
                                border: `1px solid ${activeFilter === t ? (THEME.edges as any)[t] : "rgba(255,255,255,0.07)"}`,
                                color: activeFilter === t ? (THEME.edges as any)[t] : "rgba(255,255,255,0.32)",
                                borderRadius: 20,
                                padding: "2px 9px",
                                fontSize: 8.5,
                                cursor: "pointer",
                                fontWeight: 600,
                                transition: "all .15s",
                            }}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {/* Inspector */}
            {selNode && (
                <div
                    className="ins"
                    style={{
                        position: "absolute",
                        top: 80,
                        right: 20,
                        zIndex: 20,
                        width: 288,
                        background: "rgba(0,0,0,0.8)",
                        border: `1px solid ${selLayer?.stroke || "#333"}`,
                        borderRadius: 16,
                        padding: "14px 16px",
                        backdropFilter: "blur(14px)",
                        boxShadow: `0 0 40px ${selLayer?.glow || "transparent"}`,
                    }}
                >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                            {selGlyph && <span style={{ fontSize: 24 }}>{selGlyph.sym}</span>}
                            <div style={{ color: selLayer?.text || "#fff", fontSize: 12, fontWeight: 700, marginTop: 3 }}>{selNode.label}</div>
                            <div style={{ color: selLayer?.stroke || "#999", fontSize: 8, fontWeight: 700, letterSpacing: 1.2, marginTop: 2 }}>{selNode.layer.replace(/_/g, " ")}</div>
                        </div>
                        <button onClick={() => setSelected(null)} style={{ background: "rgba(255,255,255,0.07)", border: "none", color: "#fff", borderRadius: 8, padding: "3px 8px", cursor: "pointer", fontSize: 10 }}>✕</button>
                    </div>

                    {selGlyph && (
                        <div style={{ marginTop: 10, padding: "7px 8px", background: "rgba(255,255,255,0.02)", borderRadius: 7, border: "1px solid rgba(255,255,255,0.05)" }}>
                            <div style={{ color: "rgba(255,255,255,0.28)", fontSize: 8, fontWeight: 700, letterSpacing: 1 }}>GLYPH</div>
                            <div style={{ color: "rgba(255,255,255,0.68)", fontSize: 10, marginTop: 3, lineHeight: 1.45 }}>{selGlyph.desc}</div>
                        </div>
                    )}

                    {selNode.tags.length > 0 && (
                        <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 4 }}>
                            {selNode.tags.map((t) => (
                                <span key={t} style={{ fontSize: 8, padding: "2px 7px", borderRadius: 20, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)", color: selLayer?.text || "#ccc" }}>{t}</span>
                            ))}
                        </div>
                    )}

                    <div style={{ marginTop: 12 }}>
                        <div style={{ color: "rgba(255,255,255,0.25)", fontSize: 8, fontWeight: 700, letterSpacing: 1, marginBottom: 3 }}>
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
                                    style={{
                                        fontSize: 9,
                                        marginTop: 4,
                                        display: "flex",
                                        gap: 5,
                                        alignItems: "center",
                                        cursor: "pointer",
                                        padding: "2px 5px",
                                        borderRadius: 5,
                                        background: "rgba(255,255,255,0.025)",
                                    }}
                                >
                                    <span style={{ color: (THEME.edges as any)[e.type], fontSize: 8, minWidth: 14 }}>{out ? "→" : "←"}</span>
                                    <span style={{ color: (THEME.edges as any)[e.type], fontSize: 8 }}>{e.type}</span>
                                    <span style={{ color: "rgba(255,255,255,0.6)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{on?.label || oid}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* SVG */}
            <svg viewBox={viewBox} preserveAspectRatio="xMidYMid meet" style={{ width: "100%", height: "100%", display: "block" }}>
                <defs>
                    {Object.entries(THEME.layers).map(([k, v]) => (
                        <g key={`defs-${k}`}>
                            <filter id={`glow-${k}`} x="-50%" y="-50%" width="200%" height="200%">
                                <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b" />
                                <feFlood floodColor={(v as any).stroke} floodOpacity=".35" result="c" />
                                <feComposite in="c" in2="b" operator="in" result="g" />
                                <feMerge>
                                    <feMergeNode in="g" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                            <linearGradient id={`grad-zone-${k}`} x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor={(v as any).stroke} stopOpacity="0.10" />
                                <stop offset="100%" stopColor={(v as any).stroke} stopOpacity="0.01" />
                            </linearGradient>
                            <linearGradient id={`grad-node-${k}`} x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor={(v as any).stroke} stopOpacity="0.22" />
                                <stop offset="100%" stopColor={(v as any).stroke} stopOpacity="0.04" />
                            </linearGradient>
                        </g>
                    ))}
                    <filter id="ge" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" />
                    </filter>
                </defs>

                {/* Zones */}
                {zones.map((z) => (
                    <g key={z.layer}>
                        <rect x={z.bounds!.x} y={z.bounds!.y} width={z.bounds!.w} height={z.bounds!.h} rx={24} fill={`url(#grad-zone-${z.layer})`} stroke={z.style.stroke} strokeWidth={1} strokeOpacity={0.25} />
                        <path d={`M ${z.bounds!.x + 24} ${z.bounds!.y} L ${z.bounds!.x + z.bounds!.w - 24} ${z.bounds!.y}`} stroke={z.style.stroke} strokeWidth={1.5} opacity={0.4} strokeLinecap="round" />
                        <text x={z.bounds!.x + 18} y={z.bounds!.y + 20} fill={z.style.stroke} opacity={0.4} fontSize={7.5} fontWeight={700} letterSpacing={2}>
                            {z.style.label}
                        </text>
                        {layerNodeCount(z.layer) && (
                            <text x={z.bounds!.x + z.bounds!.w - 18} y={z.bounds!.y + 20} fill={z.style.stroke} opacity={0.5} fontSize={8} fontWeight={700} textAnchor="end">
                                {layerNodeCount(z.layer)}
                            </text>
                        )}
                    </g>
                ))}

                {/* Edges */}
                {EDGES.map((e) => {
                    const path = edgePath(e.s, e.t);
                    const color = (THEME.edges as any)[e.type] || "#555";
                    const conn = connEdges.has(e.id);
                    const hov = hovEdge === e.id;
                    const off = activeFilter && e.type !== activeFilter;
                    const op = off ? 0.04 : conn ? 0.9 : hov ? 0.8 : 0.35;
                    const sw = conn ? 2.8 : hov ? 2.2 : 1.4;
                    const animating = !off && (e.anim || conn);

                    return (
                        <g key={e.id} onMouseEnter={() => setHovEdge(e.id)} onMouseLeave={() => setHovEdge(null)}>
                            <path d={path} fill="none" stroke={color} strokeWidth={sw} opacity={op} className={animating ? "edge-anim" : (e as any).dash ? "ed" : ""} strokeLinecap="round" />
                            {animating && <path d={path} fill="none" stroke={color} strokeWidth={sw + 6} opacity={0.12} filter="url(#ge)" />}

                            {/* packet dot */}
                            {animating && (
                                <circle r={2.2} fill={color} opacity={0.7}>
                                    <animateMotion dur="1.8s" repeatCount="indefinite" path={path} />
                                </circle>
                            )}

                            {(hov || conn) && !off && e.label && (() => {
                                const s = nc(e.s), t = nc(e.t);
                                const mx = (s.x + t.x) / 2, my = (s.y + t.y) / 2;
                                const w = e.label.length * 6;
                                return (
                                    <g>
                                        <rect x={mx - w / 2} y={my - 15} width={w} height={13} rx={4} fill="rgba(6,7,11,0.9)" stroke={color} strokeWidth={0.5} strokeOpacity={0.4} />
                                        <text x={mx} y={my - 4} fill={color} fontSize={7.5} textAnchor="middle" opacity={1} fontWeight={600}>{e.label}</text>
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

                    const lm = layerMoments(n.layer);
                    const hasActivity = lm && lm.count > 0;

                    return (
                        <g
                            key={n.id}
                            className={`nh ${orb ? "op" : ""}`}
                            onClick={() => setSelected(n.id === selected ? null : n.id)}
                            filter={sel ? `url(#glow-${n.layer})` : undefined}
                            opacity={dim ? 0.22 : 1}
                            style={{ transition: "opacity .2s" }}
                        >
                            {hasActivity && !sel && (
                                <rect x={p.x - 4} y={p.y - 4} width={NODE_W + 8} height={NODE_H + 8} rx={16} fill="none" stroke={ls.stroke} strokeWidth={1.5} opacity={0.3} style={{ animation: "nodePulseGlow 2.5s ease-in-out infinite" }} />
                            )}

                            {sel && (
                                <rect x={p.x - 3} y={p.y - 3} width={NODE_W + 6} height={NODE_H + 6} rx={15} fill="none" stroke={ls.stroke} strokeWidth={1.5} strokeOpacity={0.8} strokeDasharray="4 4" />
                            )}

                            {conn && (
                                <rect x={p.x - 2} y={p.y - 2} width={NODE_W + 4} height={NODE_H + 4} rx={14} fill="none" stroke={ls.stroke} strokeWidth={0.8} strokeOpacity={0.5} />
                            )}

                            <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx={12} fill={`url(#grad-node-${n.layer})`} stroke={ls.stroke} strokeWidth={sel ? 2 : 1} strokeOpacity={sel ? 1 : 0.45} />
                            <path d={`M ${p.x + 14} ${p.y + 1} L ${p.x + NODE_W - 14} ${p.y + 1}`} stroke={ls.stroke} strokeWidth={1.5} opacity={0.6} strokeLinecap="round" />

                            {g && <text x={p.x + 16} y={p.y + 31} fontSize={19} fill={ls.stroke} opacity={0.85}>{g.sym}</text>}

                            <text x={p.x + (g ? 42 : 14)} y={p.y + 19} fontSize={7} fontWeight={700} letterSpacing={1.2} fill={ls.stroke} opacity={0.55}>
                                {orb ? "ORBITAL" : n.layer.replace(/_/g, " ")}
                            </text>

                            <text x={p.x + (g ? 42 : 14)} y={p.y + 34} fontSize={10} fontWeight={600} fill={ls.text}>
                                {n.label.length > 27 ? n.label.slice(0, 26) + "…" : n.label}
                            </text>

                            {lm && (
                                <text x={p.x + (g ? 40 : 12)} y={p.y + 47} fontSize={7} fill={ls.stroke} opacity={0.45}>
                                    ● {lm.count} moments · {((lm.avg_resonance || 0) * 100).toFixed(0)}% res
                                </text>
                            )}

                            <circle cx={p.x + NODE_W / 2} cy={p.y} r={2.5} fill={ls.stroke} opacity={0.2} />
                            <circle cx={p.x + NODE_W / 2} cy={p.y + NODE_H} r={2.5} fill={ls.stroke} opacity={0.2} />
                        </g>
                    );
                })}

                {!loading && !isLive && (
                    <g>
                        <rect x={-180} y={-30} width={360} height={56} rx={12} fill="rgba(0,0,0,0.88)" stroke="#ef4444" strokeWidth={1} />
                        <text x={0} y={-5} fill="#ef4444" fontSize={11} fontWeight={700} textAnchor="middle">⚠ Grid offline</text>
                        <text x={0} y={12} fill="rgba(255,255,255,0.38)" fontSize={9} textAnchor="middle">Backend not responding · start Neo4j + uvicorn</text>
                    </g>
                )}

                <text x={0} y={-80} fontSize={8} fill="rgba(255,255,255,0.07)" textAnchor="middle" fontWeight={700} letterSpacing={3}>
                    MSTR-⚡ · AFRICAN FLAME INITIATIVE · SOVEREIGN GRID
                </text>
            </svg>

            {/* minimal footer */}
            <div style={{ position: "absolute", bottom: 12, left: 20, color: "rgba(255,255,255,0.18)", fontSize: 10 }}>
                Tip: click nodes to inspect • filter edges • animated packets indicate active/selected flows
            </div>

            {/* Live feed (compact) */}
            {moments.length > 0 && (
                <div style={{ position: "absolute", bottom: 16, right: 20, zIndex: 20, width: 320, background: "rgba(0,0,0,0.6)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 12, padding: "10px 13px", backdropFilter: "blur(10px)", maxHeight: 210, overflow: "hidden" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                        <span style={{ color: "rgba(255,255,255,0.38)", fontSize: 9, fontWeight: 700, letterSpacing: 1 }}>LIVE MOMENTS</span>
                        <span style={{ color: "#22c55e", fontSize: 8, fontWeight: 700 }}>● {ago(telemetry?.generatedAt ?? "")}</span>
                    </div>
                    {moments.slice(0, 5).map((m: any, i: number) => (
                        <div key={m.quantum_id || i} style={{ borderLeft: `2px solid ${THEME.edges.signal}`, paddingLeft: 7, marginBottom: 5 }}>
                            <div style={{ fontSize: 9, color: "rgba(255,255,255,0.6)" }}>
                                <span style={{ color: THEME.edges.signal }}>{m.initiator}</span>
                                <span style={{ color: "rgba(255,255,255,0.25)" }}> → </span>
                                <span style={{ color: "rgba(255,255,255,0.45)" }}>{m.receiver}</span>
                            </div>
                            <div style={{ color: "rgba(255,255,255,0.3)", fontSize: 7.5, marginTop: 1 }}>
                                {(m.description || "").slice(0, 68)}{(m.description || "").length > 68 ? "…" : ""}
                            </div>
                            <div style={{ display: "flex", gap: 7, marginTop: 1 }}>
                                <span style={{ color: "#a78bfa", fontSize: 7.5 }}>{m.trigger_type}</span>
                                <span style={{ color: "rgba(255,255,255,0.22)", fontSize: 7.5 }}>{ago(m.timestamp)}</span>
                                {m.resonance_score != null && <span style={{ color: "#22c55e", fontSize: 7.5 }}>{(m.resonance_score * 100).toFixed(0)}%</span>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
