/**
 * Grid Voice Console — sovereign system surface for MoStar's voice.
 *
 * This is NOT a TTS widget. The browser never synthesizes audio. It calls
 * external Grid services (MoStar Voice / Personality / DCX / Ollama). In
 * preview, all calls run through deterministic mocks unless
 * VITE_ENABLE_LIVE_GRID_SERVICES=true.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { Glyph } from "@/components/grid/glyph";
import {
  GRID_SERVICES, LIVE_GRID_SERVICES, SERVICE_LABEL, type ServiceKey,
} from "@/config/gridServices";
import {
  speak, voiceHealth, type SpeakResponse,
} from "@/services/gridVoiceClient";
import {
  choosePersona, personalityHealth, PERSONAS, type Persona,
} from "@/services/personalityClient";
import { dcxThink, dcxHealth, ollamaHealth, type DCXLayer } from "@/services/dcxClient";

type BackendId = "piper" | "dcx" | "ollama" | "mock";
type HealthStatus = "healthy" | "degraded" | "down" | "unknown";

const BACKENDS: { id: BackendId; label: string; sub: string }[] = [
  { id: "piper",  label: "PIPER",   sub: "MoStar Voice · sovereign TTS" },
  { id: "dcx",    label: "DCX",     sub: "Trinity · Mind/Soul/Body" },
  { id: "ollama", label: "OLLAMA",  sub: "Local model gateway" },
  { id: "mock",   label: "MOCK",    sub: "No backend · preview only" },
];

const STATUS_COLOR: Record<HealthStatus, string> = {
  healthy:  "var(--color-neon-green)",
  degraded: "var(--color-neon-gold)",
  down:     "#ff5a2e",
  unknown:  "var(--muted-foreground)",
};

function StatusDot({ s }: { s: HealthStatus }) {
  return (
    <span
      className="inline-block h-2 w-2 rounded-full"
      style={{ background: STATUS_COLOR[s], boxShadow: `0 0 8px ${STATUS_COLOR[s]}` }}
    />
  );
}

/* ----------------------------- Waveform ----------------------------- */

function Waveform({ active, peak = 1 }: { active: boolean; peak?: number }) {
  const bars = 48;
  const seed = useMemo(() => Array.from({ length: bars }, () => Math.random()), []);
  const [t, setT] = useState(0);
  useEffect(() => {
    if (!active) return;
    let raf = 0;
    const tick = () => { setT((x) => x + 0.08); raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active]);

  return (
    <div className="flex h-20 items-end justify-center gap-[3px]">
      {seed.map((s, i) => {
        const phase = Math.sin(t + i * 0.35) * 0.5 + 0.5;
        const h = active
          ? 8 + phase * 56 * peak * (0.4 + s * 0.6)
          : 6 + s * 6;
        const hue = active ? (i / bars) * 60 + 180 : 220;
        return (
          <span
            key={i}
            className="rounded-sm transition-[height] duration-75"
            style={{
              width: 4,
              height: h,
              background: `hsl(${hue} 95% ${active ? 60 : 35}%)`,
              boxShadow: active ? `0 0 8px hsl(${hue} 95% 60%)` : "none",
              opacity: active ? 0.9 : 0.35,
            }}
          />
        );
      })}
    </div>
  );
}

/* ----------------------------- Console ----------------------------- */

export function GridVoiceConsole() {
  const [text, setText] = useState("Honor first. Strike fast. See ahead. Stay untouchable.");
  const [persona, setPersona] = useState<Persona>("ARCHITECT");
  const [backend, setBackend] = useState<BackendId>(LIVE_GRID_SERVICES ? "piper" : "mock");
  const [layer, setLayer] = useState<DCXLayer | "auto">("auto");
  const [busy, setBusy] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<
    { kind: "user" | "system" | "voice" | "dcx"; text: string; meta?: string }[]
  >([]);
  const [health, setHealth] = useState<Record<ServiceKey, HealthStatus>>({
    voice: "unknown", personality: "unknown", dcx: "unknown", ollama: "unknown",
  });
  const audioRef = useRef<HTMLAudioElement | null>(null);

  /* ---- Health probes (always-on; mock-aware) ---- */
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      const [v, p, d, o] = await Promise.all([
        voiceHealth(), personalityHealth(), dcxHealth(), ollamaHealth(),
      ]);
      if (cancelled) return;
      setHealth({
        voice:       (v.status as HealthStatus) ?? "unknown",
        personality: (p.status as HealthStatus) ?? "unknown",
        dcx:         (d.status as HealthStatus) ?? "unknown",
        ollama:      (o.status as HealthStatus) ?? "unknown",
      });
    };
    void run();
    const id = window.setInterval(run, 15_000);
    return () => { cancelled = true; window.clearInterval(id); };
  }, []);

  const log = (entry: typeof transcript[number]) =>
    setTranscript((prev) => [...prev.slice(-49), entry]);

  async function handleSpeak() {
    if (!text.trim() || busy) return;
    setError(null);
    setBusy(true);
    const utterance = text.trim();
    log({ kind: "user", text: utterance });

    try {
      // 1. Personality engine: confirm persona (or accept the user's selection)
      const choice = await choosePersona({
        soulprint: { need: "decision" },
        operational: { domain: "covenant" },
      });
      const finalPersona = persona ?? choice.persona;

      // 2. Route through the chosen backend
      let dcxText = utterance;
      if (backend === "dcx" || backend === "ollama") {
        const r = await dcxThink({
          query: utterance,
          layer: layer === "auto" ? undefined : layer,
        });
        dcxText = r.content;
        log({ kind: "dcx", text: r.content, meta: `${r.layer.toUpperCase()} · ${r.model}` });
      }

      // 3. Send to MoStar Voice (or skip in pure mock-mock)
      let res: SpeakResponse | null = null;
      if (backend !== "mock") {
        res = await speak({ text: dcxText, persona: finalPersona });
        log({
          kind: "voice",
          text: `Generated · ${(res.duration_ms / 1000).toFixed(1)}s`,
          meta: `${res.engine} · ${res.persona}${res.mock ? " · mock" : ""}`,
        });
      } else {
        log({ kind: "system", text: "Mock backend — no audio synthesized." });
      }

      // 4. Play if we got a URL
      if (res?.audio_url) {
        setPlaying(true);
        const a = audioRef.current;
        if (a) {
          a.src = res.audio_url;
          a.onended = () => setPlaying(false);
          await a.play().catch((e) => { setError(`Audio play failed: ${e.message}`); setPlaying(false); });
        }
      } else if (res) {
        // Simulate playback duration so waveform reacts even without audio_url
        setPlaying(true);
        window.setTimeout(() => setPlaying(false), res.duration_ms);
      }
    } catch (e) {
      const msg = (e as Error).message;
      setError(msg);
      log({ kind: "system", text: `ERROR · ${msg}` });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-3">
      {/* Header */}
      <div className="panel flex items-center gap-3 px-4 py-3">
        <Glyph name="sun" size={28} glow="var(--color-neon-gold)" />
        <div className="flex-1">
          <div className="text-xs tracking-[0.3em] neon-text-gold">GRID VOICE CONSOLE</div>
          <div className="text-[10px] tracking-[0.2em] text-muted-foreground">
            The Grid speaks · sovereign service surface · {LIVE_GRID_SERVICES ? "LIVE" : "PREVIEW (MOCK)"}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {(Object.keys(SERVICE_LABEL) as ServiceKey[]).map((k) => (
            <div key={k} className="flex items-center gap-2 text-[10px] tracking-[0.18em]">
              <StatusDot s={health[k]} />
              <span className="text-foreground/80">{SERVICE_LABEL[k]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid flex-1 grid-cols-12 gap-3">
        {/* Composer */}
        <div className="panel col-span-12 flex flex-col gap-3 p-4 lg:col-span-7">
          <label className="text-[10px] tracking-[0.25em] text-muted-foreground">
            UTTERANCE
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className="w-full resize-none rounded-md border border-white/10 bg-black/40 p-3 font-mono text-sm text-foreground outline-none focus:border-[var(--color-neon-cyan)]/60"
            placeholder="Speak through the Grid…"
          />

          {/* Persona / Backend / Layer */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <div className="mb-1 text-[10px] tracking-[0.25em] text-muted-foreground">PERSONA</div>
              <select
                value={persona}
                onChange={(e) => setPersona(e.target.value as Persona)}
                className="w-full rounded-md border border-white/10 bg-black/40 px-2 py-2 text-xs tracking-[0.15em]"
              >
                {PERSONAS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <div className="mb-1 text-[10px] tracking-[0.25em] text-muted-foreground">BACKEND</div>
              <select
                value={backend}
                onChange={(e) => setBackend(e.target.value as BackendId)}
                className="w-full rounded-md border border-white/10 bg-black/40 px-2 py-2 text-xs tracking-[0.15em]"
              >
                {BACKENDS.map((b) => <option key={b.id} value={b.id}>{b.label}</option>)}
              </select>
              <div className="mt-1 text-[10px] text-muted-foreground">
                {BACKENDS.find((b) => b.id === backend)?.sub}
              </div>
            </div>
            <div>
              <div className="mb-1 text-[10px] tracking-[0.25em] text-muted-foreground">DCX LAYER</div>
              <select
                value={layer}
                onChange={(e) => setLayer(e.target.value as DCXLayer | "auto")}
                disabled={backend !== "dcx" && backend !== "ollama"}
                className="w-full rounded-md border border-white/10 bg-black/40 px-2 py-2 text-xs tracking-[0.15em] disabled:opacity-40"
              >
                <option value="auto">AUTO</option>
                <option value="dcx0">DCX0 · MIND</option>
                <option value="dcx1">DCX1 · SOUL</option>
                <option value="dcx2">DCX2 · BODY</option>
              </select>
            </div>
          </div>

          {/* Waveform + Speak */}
          <div className="rounded-md border border-white/10 bg-black/30 p-3">
            <Waveform active={playing || busy} peak={playing ? 1 : 0.4} />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSpeak}
              disabled={busy || !text.trim()}
              className="rounded-md border border-[var(--color-neon-gold)]/60 bg-[oklch(0.22_0.08_80/0.4)] px-5 py-2 text-xs tracking-[0.3em] neon-text-gold transition hover:bg-[oklch(0.30_0.10_80/0.55)] disabled:opacity-40"
            >
              {busy ? "AWAKENING…" : "SPEAK"}
            </button>
            <audio ref={audioRef} className="hidden" />
            <div className="ml-auto text-[10px] tracking-[0.25em] text-muted-foreground">
              {LIVE_GRID_SERVICES
                ? `voice: ${GRID_SERVICES.voice}`
                : "preview · live calls disabled"}
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-[#ff5a2e]/50 bg-[#3a0d0d]/40 p-3 text-xs text-[#ffb4a0]">
              <div className="mb-1 tracking-[0.3em] text-[#ff8a6c]">BACKEND FAILURE</div>
              {error}
            </div>
          )}
        </div>

        {/* Transcript */}
        <div className="panel col-span-12 flex flex-col p-4 lg:col-span-5">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-[10px] tracking-[0.3em] neon-text-cyan">TRANSCRIPT</div>
            <button
              onClick={() => setTranscript([])}
              className="text-[10px] tracking-[0.2em] text-muted-foreground hover:text-foreground"
            >
              CLEAR
            </button>
          </div>
          <div className="flex-1 space-y-2 overflow-y-auto pr-1 font-mono text-xs">
            {transcript.length === 0 && (
              <div className="text-muted-foreground">
                The Grid awaits an utterance. Type and press SPEAK.
              </div>
            )}
            {transcript.map((e, i) => {
              const color =
                e.kind === "user"   ? "var(--color-neon-cyan)"  :
                e.kind === "voice"  ? "var(--color-neon-gold)"  :
                e.kind === "dcx"    ? "var(--color-neon-green)" :
                                      "var(--muted-foreground)";
              return (
                <div key={i} className="rounded-md border border-white/5 bg-black/20 p-2">
                  <div
                    className="mb-1 text-[10px] tracking-[0.3em]"
                    style={{ color }}
                  >
                    {e.kind.toUpperCase()} {e.meta ? `· ${e.meta}` : ""}
                  </div>
                  <div className="text-foreground/90">{e.text}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
