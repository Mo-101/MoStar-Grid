/**
 * Grid Snapshot — the dashboard's living voice. Five seconds after the
 * dashboard mounts (i.e. right after the boot sequence hands off), and
 * again every few minutes after that, it composes a coherent status
 * briefing from the same live data the KPI/health/council/feed panels
 * render, sends it to MoStar Voice, and reveals the captions in lockstep
 * with the measured narration — the same byte-accurate segment sync used
 * by the boot ring in awakening.tsx.
 *
 * If the voice service is unreachable (or disabled in preview), captions
 * still advance on a deterministic reading-time clock so the briefing
 * remains legible without audio.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Glyph } from "./glyph";
import { narrate } from "@/services/gridVoiceClient";
import { useGridStatus, useAdvisors, useHealthChecks, useLiveFeed } from "./parts";
import { buildSnapshotSegments, type SnapshotMetrics } from "@/lib/gridSnapshot";

const AUTO_BRIEF_DELAY_MS = 3_000;
const AUTO_BRIEF_INTERVAL_MS = 3 * 60 * 1_000;

function timeAgoShort(date: Date | null): string {
  if (!date) return "—";
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1_000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.round(seconds / 60)}m ago`;
}

export function GridSnapshotPanel() {
  const { data: status } = useGridStatus();
  const { data: advisors } = useAdvisors();
  const { verdict, sealed, total, degradedLabels, asOf } = useHealthChecks();
  const { items } = useLiveFeed();

  const metrics: SnapshotMetrics = useMemo(
    () => ({
      nodes: status?.mindgraph.nodes ?? null,
      relationships: status?.mindgraph.relationships ?? null,
      sealedChecks: sealed,
      totalChecks: total,
      verdict,
      degradedLabels,
      advisorCount: advisors ? Object.keys(advisors).length : null,
      queuePending: status?.queue.pending ?? null,
      queueCommittedToday: status?.queue.committed_today ?? null,
      latestFeed: items[0] ? { agent: items[0].agent, text: items[0].text, at: items[0].at } : null,
      asOf,
    }),
    [status, advisors, verdict, sealed, total, degradedLabels, asOf, items],
  );

  const metricsRef = useRef(metrics);
  metricsRef.current = metrics;
  const previousRef = useRef<SnapshotMetrics | null>(null);
  const busyRef = useRef(false);
  const timersRef = useRef<number[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [captions, setCaptions] = useState<string[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const [lastBriefedAt, setLastBriefedAt] = useState<Date | null>(null);
  const [, forceTick] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => forceTick((t) => t + 1), 1_000);
    return () => window.clearInterval(id);
  }, []);

  const clearTimers = () => {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current = [];
  };

  const runBriefing = useRef(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    clearTimers();
    setSpeaking(true);

    const segments = buildSnapshotSegments(metricsRef.current, previousRef.current);
    setCaptions(segments);
    setActiveIndex(0);

    // narrate() never throws: a voice failure or preview mode comes back as
    // `silent: true` with real per-segment timing already computed (see
    // silentSegmentPlan in @/lib/gridSnapshot) — not as an exception to
    // catch and re-estimate ourselves.
    const plan = await narrate(segments, "reflective");
    previousRef.current = metricsRef.current;
    setLastBriefedAt(new Date());

    let playedAudio = false;
    const audio = audioRef.current;
    if (!plan.silent && plan.audio_url && audio) {
      try {
        audio.src = plan.audio_url;
        const onTimeUpdate = () => {
          const elapsedMs = audio.currentTime * 1_000;
          let idx = 0;
          for (let i = plan.segments.length - 1; i >= 0; i -= 1) {
            if (elapsedMs >= plan.segments[i].start_ms) {
              idx = i;
              break;
            }
          }
          setActiveIndex(idx);
        };
        const onEnded = () => {
          setSpeaking(false);
          busyRef.current = false;
          audio.removeEventListener("timeupdate", onTimeUpdate);
          audio.removeEventListener("ended", onEnded);
        };
        audio.addEventListener("timeupdate", onTimeUpdate);
        audio.addEventListener("ended", onEnded);
        await audio.play();
        playedAudio = true;
      } catch {
        playedAudio = false;
      }
    }

    if (!playedAudio) {
      // Silent path — schedule against the plan's own segment timing
      // (measured reading-time estimates when silent, real WAV-measured
      // cues when audio exists but simply failed to play).
      plan.segments.forEach((seg, index) => {
        timersRef.current.push(window.setTimeout(() => setActiveIndex(index), seg.start_ms));
      });
      timersRef.current.push(
        window.setTimeout(() => {
          setSpeaking(false);
          busyRef.current = false;
        }, plan.audio_ms),
      );
    }
  });

  useEffect(() => {
    const openTimer = window.setTimeout(() => void runBriefing.current(), AUTO_BRIEF_DELAY_MS);
    const liveInterval = window.setInterval(
      () => void runBriefing.current(),
      AUTO_BRIEF_INTERVAL_MS,
    );
    return () => {
      window.clearTimeout(openTimer);
      window.clearInterval(liveInterval);
      clearTimers();
      audioRef.current?.pause();
    };
  }, []);

  return (
    <div className="flex min-w-0 flex-1 items-center gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[var(--color-neon-gold)]/40">
        <Glyph name="venus" size={18} glow="var(--color-neon-gold)" />
      </div>
      <div className="min-w-0 flex-1 leading-tight">
        <div className="flex items-center gap-2 text-[9px] tracking-[0.22em] text-muted-foreground">
          <span className="neon-text-gold">GRID VOICE</span>
          <span
            className={`h-1.5 w-1.5 rounded-full ${speaking ? "bg-[var(--color-neon-green)] animate-blink" : "bg-white/20"
              }`}
          />
          <span>
            {speaking
              ? "BRIEFING"
              : lastBriefedAt
                ? `LAST BRIEFED ${timeAgoShort(lastBriefedAt)}`
                : "AWAITING FIRST BRIEFING"}
          </span>
        </div>
        <div className="truncate text-xs text-foreground/90" aria-live="polite">
          {captions[activeIndex] ?? "The Grid is gathering its first status snapshot…"}
        </div>
      </div>
      <button
        type="button"
        onClick={() => void runBriefing.current()}
        disabled={speaking}
        className="shrink-0 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-[10px] tracking-[0.22em] text-muted-foreground transition hover:bg-white/5 disabled:opacity-40"
      >
        BRIEF NOW
      </button>
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
