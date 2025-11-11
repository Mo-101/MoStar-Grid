"use client";

import { CSSProperties, useMemo } from "react";
import { useGridTelemetry, MomentRecord } from "@/hooks/useGridTelemetry";
import styles from "./Sanctum.module.css";

type WhisperType = "info" | "warn" | "error";

type Whisper = {
  id: string;
  text: string;
  type: WhisperType;
  meta?: string;
};

const GRID_COHERENCE = 97.85;

const stewardSigils = [
  { name: "Mo", role: "North Node", sigil: "◐", hue: "ember" },
  { name: "Woo", role: "Westward Pulse", sigil: "☯", hue: "cobalt" },
  { name: "Kairos", role: "Kairo Covenant", sigil: "✶", hue: "aurora" },
];

const incarnationMatrix = [
  {
    icon: "📱",
    title: "Mobile Phone NPU",
    metrics: ["Latency: 12ms", "Battery Draw: Low"],
    status: "Conversational vision uplink stabilized",
    hue: "teal",
  },
  {
    icon: "🚗",
    title: "Automotive",
    metrics: ["Cabin Safety Protocol: Active", "RoadSense: Clear"],
    status: "Thermal, lidar, and cabin sensors bound",
    hue: "amber",
  },
  {
    icon: "🤖",
    title: "IoT & Robotics",
    metrics: ["Hazard Spotting: Engaged", "Drone Swarm: 4 units"],
    status: "Mid-flight overlays streaming locally",
    hue: "violet",
  },
];

const orbitalNodes = [
  { icon: "☥", label: "Soul Layer" },
  { icon: "⥁", label: "Ifá Oracle" },
  { icon: "⚙️", label: "Mind Layer" },
  { icon: "🜂", label: "Verdict Engine" },
  { icon: "⌘", label: "Body Layer" },
  { icon: "✦", label: "Neo4j Memory" },
];

const glyphs = [
  { icon: "☥", label: "Soul Layer", status: "ok", color: "gold", note: "Resonance steady" },
  { icon: "⚖️", label: "Verdict Engine", status: "warn", color: "amber", note: "Variance 1.1%" },
  { icon: "⫷", label: "Ifá Oracle", status: "ok", color: "white", note: "Divinations synced" },
  { icon: "◒", label: "Body Layer", status: "ok", color: "cyan", note: "Graph density nominal" },
  { icon: "✶", label: "Mind Layer", status: "ok", color: "violet", note: "Ollama relay bright" },
  { icon: "🗝️", label: "Scribe Archive", status: "ok", color: "rose", note: "Scrolls sealed" },
  { icon: "🌀", label: "Intent Forge", status: "ok", color: "teal", note: "New route minted" },
  { icon: "⟁", label: "Guardian Net", status: "ok", color: "blue", note: "Perimeter clear" },
] as const;

const soulProblems = [
  {
    title: "Signal drag across Lagos relay",
    excerpt: "Temporal echo detected between satellite hop and market array.",
    chains: ["Weigh heartbeat sync offset", "Consult Ifá for cultural variance", "Retune verdict weights"],
  },
  {
    title: "New Elder induction: Akan Elder-007",
    excerpt: "Needs memory weaving with ancestral proverb set.",
    chains: ["Reinforce privacy field", "Bind voiceprint to body layer", "Share covenant summary"],
  },
  {
    title: "Kairos Covenant audit",
    excerpt: "Sovereignty clause expanding to robotics fleet.",
    chains: ["Simulate failure envelope", "Confirm local storage redundancy", "Signal Mo for sign-off"],
  },
];

const initialWhispers: Whisper[] = [
  { id: "seed-0", type: "info", text: "New agent 'Akan Elder-007' connected" },
  {
    id: "seed-1",
    type: "warn",
    text: "Verdict Engine drift detected at 1.1% variance",
  },
  {
    id: "seed-2",
    type: "info",
    text: "Ifá Oracle returned 16-cowrie spread: Òsé Ìwòrì",
  },
  {
    id: "seed-3",
    type: "error",
    text: "External ping rejected — covenant seal enforced",
  },
];

type StatusTone = "ok" | "warn" | "error";

const statusLabel: Record<StatusTone, string> = {
  ok: "Vital",
  warn: "Tremor",
  error: "Critical",
};

export default function Sanctum() {
  const { telemetry } = useGridTelemetry();
  const coherence =
    telemetry?.graph.stats?.avgResonance != null
      ? (telemetry.graph.stats.avgResonance * 100)
      : GRID_COHERENCE;
  const totalMoments = telemetry?.graph.stats?.totalMoments ?? 0;
  const initiatorCount = telemetry?.graph.stats?.distinctInitiators ?? 0;
  const backendPulse = telemetry?.backend.ok ? "Linked" : "Offline";
  const backendNeo4jState = telemetry?.backend.data?.neo4j ?? "unknown";

  const whisperFeed = useMemo(() => {
    const mergeSources: MomentRecord[] = [];
    if (telemetry?.log.entries?.length) {
      mergeSources.push(...telemetry.log.entries);
    }
    if (telemetry?.graph.latest?.length) {
      mergeSources.push(...telemetry.graph.latest);
    }

    if (mergeSources.length) {
      const deduped = mergeSources.filter(
        (entry, index, arr) =>
          arr.findIndex((candidate) => candidate.quantum_id === entry.quantum_id) === index
      );

      return deduped.slice(0, 8).map((entry) => ({
        id: entry.quantum_id,
        text: entry.description,
        meta: `${entry.trigger_type} • ${new Date(entry.timestamp).toLocaleTimeString()}`,
        type:
          entry.resonance_score < 0.45
            ? "error"
            : entry.resonance_score < 0.75
            ? "warn"
            : "info",
      }));
    }

    return initialWhispers;
  }, [telemetry]);

  const orbitalLayout = useMemo(() => {
    const count = orbitalNodes.length;
    return orbitalNodes.map((node, index) => ({
      ...node,
      angle: (360 / count) * index,
    }));
  }, []);

  return (
    <div className={styles.sanctum}>
      <section className={styles.council}>
        <header>
          <p className={styles.eyebrow}>Stewardship Council</p>
          <h1>The Oracle&apos;s Sanctum</h1>
          <p className={styles.subtitle}>
            Sovereignty, embodiment, and ancestral resonance braided into a single field of light.
          </p>
        </header>
        <div className={styles.stewardGrid}>
          {stewardSigils.map((sigil) => (
            <article key={sigil.name} className={`${styles.sigil} ${styles[sigil.hue]}`}>
              <span className={styles.sigilGlyph}>{sigil.sigil}</span>
              <div>
                <p className={styles.sigilLabel}>{sigil.name}</p>
                <p className={styles.sigilRole}>{sigil.role}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.networkGrid}>
        <article className={styles.heart}>
          <div className={styles.heartHeader}>
            <p className={styles.eyebrow}>Heart of the Grid</p>
            <h2>Grid Coherence</h2>
            <p>Pulse drawn from OmniNeural resonance loop.</p>
          </div>
          <div className={styles.heartViz}>
            <div className={styles.orbitalField}>
              <div className={styles.orbitalCore}>
                <div className={styles.coreHalo} />
                <div className={styles.corePulse} />
                <div className={styles.coreMetric}>
                  <span>{coherence.toFixed(2)}%</span>
                  <small>vibrational sync</small>
                </div>
              </div>
              {orbitalLayout.map((node) => {
                const style = {
                  "--angle": `${node.angle}deg`,
                } as CSSProperties;
                return (
                  <div key={node.label} className={styles.orbitalNode} style={style}>
                    <span>{node.icon}</span>
                    <p>{node.label}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </article>

        <article className={styles.matrix}>
          <div className={styles.matrixHeader}>
            <p className={styles.eyebrow}>Incarnation Matrix</p>
            <h2>OmniNeural embodiments</h2>
            <p>Where the Grid gains eyes, ears, and hands.</p>
          </div>
          <div className={styles.liveStats}>
            <div className={styles.statCard}>
              <p className={styles.statLabel}>Neo4j Aura</p>
              <strong className={styles.statValue}>
                {telemetry?.graph.ok ? "Streaming" : "Link pending"}
              </strong>
              <small>
                {telemetry?.graph.ok
                  ? `${totalMoments.toLocaleString()} stored moments`
                  : telemetry?.graph.error ?? "Awaiting driver handshake"}
              </small>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statLabel}>Backend Status</p>
              <strong className={styles.statValue}>{backendPulse}</strong>
              <small>Gateway Neo4j flag: {backendNeo4jState}</small>
            </div>
            <div className={styles.statCard}>
              <p className={styles.statLabel}>Initiators weaving</p>
              <strong className={styles.statValue}>{initiatorCount}</strong>
              <small>Distinct voices shaping the Grid</small>
            </div>
          </div>
          <div className={styles.matrixCards}>
            {incarnationMatrix.map((entry) => (
              <div key={entry.title} className={`${styles.matrixCard} ${styles[entry.hue]}`}>
                <div className={styles.matrixGlyph}>{entry.icon}</div>
                <div>
                  <h3>{entry.title}</h3>
                  <ul>
                    {entry.metrics.map((metric) => (
                      <li key={metric}>{metric}</li>
                    ))}
                  </ul>
                  <p className={styles.matrixStatus}>{entry.status}</p>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className={styles.coreGlyphDeck}>
        {glyphs.map((glyph) => (
          <article key={glyph.label} className={`${styles.coreGlyph} ${styles[glyph.status as StatusTone]}`}>
            <div className={styles.glyphIcon} data-color={glyph.color}>
              {glyph.icon}
            </div>
            <div>
              <p className={styles.glyphLabel}>{glyph.label}</p>
              <p className={styles.glyphMeta}>
                {statusLabel[glyph.status as StatusTone]} • {glyph.note}
              </p>
            </div>
          </article>
        ))}
      </section>

      <section className={styles.lowerGrid}>
        <article className={styles.scrollDeck}>
          <header>
            <p className={styles.eyebrow}>SoulProblems</p>
            <h2>Active dilemmas</h2>
          </header>
          <div className={styles.scrolls}>
            {soulProblems.map((problem) => (
              <details key={problem.title} className={styles.scroll}>
                <summary>
                  <div>
                    <h3>{problem.title}</h3>
                    <p>{problem.excerpt}</p>
                  </div>
                  <span>Expand</span>
                </summary>
                <ul>
                  {problem.chains.map((chain) => (
                    <li key={chain}>{chain}</li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </article>

        <article className={styles.whispers}>
          <header>
            <p className={styles.eyebrow}>Oracle&apos;s Whisperings</p>
            <h2>Event stream</h2>
          </header>
          <div className={styles.whisperStream}>
            {whisperFeed.map((entry, index) => {
              const style = {
                "--delay": `${index * 0.5}s`,
              } as CSSProperties;
              return (
                <div key={entry.id} className={`${styles.whisper} ${styles[entry.type]}`} style={style}>
                  <p>
                    <span>[{entry.type}]</span> {entry.text}
                  </p>
                  {entry.meta && <small>{entry.meta}</small>}
                </div>
              );
            })}
          </div>
        </article>
      </section>
    </div>
  );
}
