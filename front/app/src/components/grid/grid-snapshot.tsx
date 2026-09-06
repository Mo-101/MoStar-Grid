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
import { useQuery } from "@tanstack/react-query";
import { Glyph } from "./glyph";
import { narrate } from "@/services/gridVoiceClient";
import { useGridStatus, useAdvisors, useHealthChecks, useLiveFeed } from "./parts";
import {
  buildOverviewSegments,
  buildSnapshotSegments,
  deriveContinentOptics,
  type SnapshotMetrics,
} from "@/lib/gridSnapshot";
import { getAfricaSenses } from "@/services/gridApiClient";
import { GRID_REFRESH } from "@/lib/grid-refresh-policy";

const AUTO_BRIEF_DELAY_MS = 1_500;
const AUTO_BRIEF_INTERVAL_MS = GRID_REFRESH.CANONICAL_MS;

function timeAgoShort(date: Date | null): string {
  if (!date) return "—";
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1_000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.round(seconds / 60)}m ago`;
}

export function GridSnapshotPanel({
  source = "operational",
}: {
  source?: "grid" | "continent" | "operational";
}) {
  const { data: status } = useGridStatus();
  const { data: advisors } = useAdvisors();
  const { verdict, sealed, total, degradedLabels, asOf } = useHealthChecks();
  const { items } = useLiveFeed();
  const { data: africaSenses } = useQuery({
    queryKey: ["africa-senses"],
    queryFn: getAfricaSenses,
    refetchInterval: GRID_REFRESH.WEATHER_MS,
    staleTime: GRID_REFRESH.WEATHER_STALE_MS,
    refetchOnWindowFocus: true,
  });

  const metrics: SnapshotMetrics = useMemo(
    () => ({
      // Raw TOTAL population. Knowledge scale may only come from the backend
      // classification layer below — never derived from this number here.
      totalNodes: status?.mindgraph.nodes ?? null,
      relationships: status?.mindgraph.relationships ?? null,
      semanticAccounting: status?.mindgraph.semantic_accounting ?? null,
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
  const africaRef = useRef(africaSenses);
  africaRef.current = africaSenses;
  const previousRef = useRef<SnapshotMetrics | null>(null);
  const lastAfricaDigestRef = useRef<string | null>(null);
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

    // Every briefing opens with the executive overview: the ruling, the scale
    // behind it, the continental picture, then the exceptions by name. The
    // detail segments below are evidence for that overview — including the
    // canonical Africa report, which is always appended verbatim so its
    // server-side digest still describes exactly what was spoken.
    const optics = deriveContinentOptics(africaRef.current);
    const africaSegments = africaRef.current?.canonical_report.segments ?? [];

    let segments: string[];
    if (source === "continent") {
      segments = [...buildOverviewSegments(null, optics), ...africaSegments];
    } else if (source === "operational") {
      segments = [
        ...buildOverviewSegments(metricsRef.current, optics),
        ...buildSnapshotSegments(metricsRef.current, previousRef.current, {
          precededByOverview: true,
        }),
        ...africaSegments,
      ];
    } else {
      segments = [
        ...buildOverviewSegments(metricsRef.current, null),
        ...buildSnapshotSegments(metricsRef.current, previousRef.current, {
          precededByOverview: true,
        }),
      ];
    }
    if (!segments.length) {
      setCaptions(["No current canonical Africa report is available."]);
      setSpeaking(false);
      busyRef.current = false;
      return;
    }
    setCaptions(segments);
    setActiveIndex(0);

    // narrate() never throws: a voice failure or preview mode comes back as
    // `silent: true` with real per-segment timing already computed (see
    // silentSegmentPlan in @/lib/gridSnapshot) — not as an exception to
    // catch and re-estimate ourselves.
    const plan = await narrate(segments, "reflective");
    if (source !== "continent") previousRef.current = metricsRef.current;
    if (africaRef.current?.canonical_report.source_digest) {
      lastAfricaDigestRef.current = africaRef.current.canonical_report.source_digest;
    }
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

  useEffect(() => {
    const digest = africaSenses?.canonical_report.source_digest;
    if (!digest || digest === lastAfricaDigestRef.current || busyRef.current) return;
    const updateTimer = window.setTimeout(() => void runBriefing.current(), 500);
    return () => window.clearTimeout(updateTimer);
  }, [africaSenses?.canonical_report.source_digest]);

  return (
    <div className="flex min-w-0 flex-1 items-center gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[var(--color-neon-gold)]/40">
        <Glyph name="venus" size={18} />
      </div>
      <div className="min-w-0 flex-1 leading-tight">
        <div className="flex items-center gap-2 text-[9px] tracking-[0.22em] text-muted-foreground">
          <span className="neon-text-gold">
            {source === "continent"
              ? "CANONICAL AFRICA VOICE"
              : source === "operational"
                ? "GRID OPERATIONAL REPORT"
                : "GRID VOICE"}
          </span>
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              speaking ? "bg-[var(--color-neon-green)] animate-blink" : "bg-white/20"
            }`}
          />
          <span>
            {speaking
              ? "BRIEFING"
              : lastBriefedAt
                ? `LAST BRIEFED ${timeAgoShort(lastBriefedAt)}`
                : "AWAITING FIRST BRIEFING"}
          </span>
          {source !== "grid" && africaSenses?.canonical_report ? (
            <span>
              CANON {africaSenses.canonical_report.source_digest.slice(0, 10).toUpperCase()} ·{" "}
              {africaSenses.canonical_report.source_refs.length} SOURCES
            </span>
          ) : null}
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
