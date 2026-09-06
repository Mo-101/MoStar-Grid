import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  CloudRain,
  Compass,
  Database,
  Droplets,
  RefreshCw,
  ShieldCheck,
  Wind,
} from "lucide-react";
import {
  getAfricaSenses,
  type AfricaWeatherLocation,
  type EpistemicState,
} from "@/services/gridApiClient";
import { GRID_REFRESH } from "@/lib/grid-refresh-policy";
import { WeatherSky } from "./weather-sky";

const STATE_TONE: Record<string, string> = {
  CONSENSUS:
    "text-[var(--color-neon-green)] border-[var(--color-neon-green)]/30 bg-[oklch(0.22_0.08_155/0.2)]",
  HEALTHY:
    "text-[var(--color-neon-green)] border-[var(--color-neon-green)]/30 bg-[oklch(0.22_0.08_155/0.2)]",
  LIVE: "text-[var(--color-neon-green)] border-[var(--color-neon-green)]/30 bg-[oklch(0.22_0.08_155/0.2)]",
  RECENT:
    "text-[var(--color-neon-cyan)] border-[var(--color-neon-cyan)]/30 bg-[oklch(0.2_0.06_220/0.2)]",
  PARTIAL:
    "text-[var(--color-neon-gold)] border-[var(--color-neon-gold)]/30 bg-[oklch(0.24_0.07_80/0.2)]",
  DIVERGENT:
    "text-[var(--color-neon-orange)] border-[var(--color-neon-orange)]/35 bg-[oklch(0.24_0.08_55/0.2)]",
  STALE:
    "text-[var(--color-neon-orange)] border-[var(--color-neon-orange)]/35 bg-[oklch(0.24_0.08_55/0.2)]",
  UNAVAILABLE: "text-[var(--muted-foreground)] border-white/10 bg-white/[0.025]",
};

function StateBadge({ state }: { state: string }) {
  return (
    <span
      className={`rounded-sm border px-2 py-1 text-[10px] font-semibold tracking-[0.16em] ${STATE_TONE[state] ?? STATE_TONE.UNAVAILABLE}`}
    >
      {state}
    </span>
  );
}

function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Wind }) {
  return (
    <div className="min-w-0">
      <div className="mb-1 flex items-center gap-1.5 text-[10px] tracking-[0.15em] text-[var(--muted-foreground)]">
        <Icon size={12} />
        {label}
      </div>
      <div className="truncate text-base font-semibold text-[var(--foreground)]">{value}</div>
    </div>
  );
}

function WeatherTrace({ values, color }: { values: Array<number | null>; color: string }) {
  const points = values.filter((value): value is number => typeof value === "number");
  if (points.length < 2) return <div className="h-12 border-y border-white/5" />;
  const low = Math.min(...points);
  const high = Math.max(...points);
  const range = Math.max(1, high - low);
  const path = points
    .map(
      (value, index) =>
        `${index ? "L" : "M"} ${(index / (points.length - 1)) * 100} ${38 - ((value - low) / range) * 28}`,
    )
    .join(" ");
  return (
    <svg viewBox="0 0 100 44" preserveAspectRatio="none" className="h-12 w-full" aria-hidden="true">
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="1.4"
        vectorEffect="non-scaling-stroke"
      />
      <path
        d={`${path} L 100 44 L 0 44 Z`}
        fill={`color-mix(in oklab, ${color} 14%, transparent)`}
        stroke="none"
      />
    </svg>
  );
}

function WeatherCommand({ weather }: { weather: AfricaWeatherLocation }) {
  const temperatures = weather.forecast?.temperature_c ?? [];
  const rain = weather.forecast?.precipitation_probability ?? [];
  const observedAge = weather.observed_at
    ? Math.max(0, Math.floor((Date.now() - new Date(weather.observed_at).getTime()) / 1_000))
    : null;
  return (
    <section className="relative isolate overflow-hidden rounded-md border border-[var(--color-neon-cyan)]/30 bg-[oklch(0.13_0.035_245/0.86)] px-5 py-5 shadow-[0_18px_60px_oklch(0.03_0.03_250/0.55)] sm:px-7 sm:py-6">
      <WeatherSky reading={weather} className="-z-10" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-[var(--color-neon-cyan)]/70" />
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] tracking-[0.24em] text-[var(--color-neon-cyan)]">
            WEATHER COMMAND · {weather.region.toUpperCase()} AFRICA
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[0.08em] text-[var(--foreground)] sm:text-3xl">
            {weather.location}
          </h2>
          <p className="mt-1 text-xs tracking-[0.12em] text-[var(--muted-foreground)]">
            {weather.country} · {weather.summary.toUpperCase()}
          </p>
        </div>
        <StateBadge state={weather.epistemic_state} />
      </header>

      <div className="mt-7 grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <div className="flex items-end gap-4">
          <div className="text-6xl font-semibold leading-none tracking-[-0.06em] text-[var(--foreground)] sm:text-7xl">
            {weather.temperature_c == null ? "—" : Math.round(weather.temperature_c)}
            <span className="ml-1 text-2xl font-normal text-[var(--color-neon-cyan)]">°C</span>
          </div>
          <div className="pb-1 text-xs leading-5 text-[var(--muted-foreground)]">
            Feels{" "}
            {weather.feels_like_c == null ? "unknown" : `${Math.round(weather.feels_like_c)}°`}
            <br />
            {weather.provider_count} measured source{weather.provider_count === 1 ? "" : "s"}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
          <Metric
            icon={Droplets}
            label="HUMIDITY"
            value={weather.humidity_pct == null ? "No source" : `${weather.humidity_pct}%`}
          />
          <Metric
            icon={Wind}
            label="WIND"
            value={weather.wind_kph == null ? "No source" : `${weather.wind_kph} km/h`}
          />
          <Metric
            icon={Compass}
            label="DIRECTION"
            value={
              weather.wind_direction_deg == null
                ? "No source"
                : `${Math.round(weather.wind_direction_deg)}°`
            }
          />
          <Metric
            icon={CloudRain}
            label="RAIN"
            value={
              weather.precipitation_probability == null
                ? "No source"
                : `${weather.precipitation_probability}%`
            }
          />
        </div>
      </div>

      <div className="mt-7 grid gap-4 border-t border-white/8 pt-5 sm:grid-cols-2">
        <div>
          <div className="mb-1 text-[9px] tracking-[0.2em] text-[var(--muted-foreground)]">
            12H TEMPERATURE TRACE
          </div>
          <WeatherTrace values={temperatures} color="var(--color-neon-cyan)" />
        </div>
        <div>
          <div className="mb-1 text-[9px] tracking-[0.2em] text-[var(--muted-foreground)]">
            12H PRECIPITATION PROBABILITY
          </div>
          <WeatherTrace values={rain} color="var(--color-neon-blue)" />
        </div>
      </div>

      <footer className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-white/8 pt-4 text-[10px] tracking-[0.12em] text-[var(--muted-foreground)]">
        <span>
          SOURCES · {weather.providers_used.join(" · ").toUpperCase() || "NO CURRENT SOURCE"}
        </span>
        <span>
          AGREEMENT {Math.round(weather.agreement_score * 100)}% · OBSERVATION AGE{" "}
          {observedAge ?? "—"} SEC
        </span>
      </footer>
    </section>
  );
}

function WeatherStrip({
  locations,
  selected,
  onSelect,
}: {
  locations: AfricaWeatherLocation[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="grid gap-px overflow-hidden rounded-md border border-white/10 bg-white/10 sm:grid-cols-2 xl:grid-cols-4">
      {locations.map((location) => (
        <button
          key={location.location_id}
          onClick={() => onSelect(location.location_id)}
          className={`min-h-24 bg-[oklch(0.115_0.025_250)] p-4 text-left transition-colors duration-200 hover:bg-[oklch(0.17_0.045_240)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--color-neon-cyan)] ${selected === location.location_id ? "bg-[oklch(0.18_0.055_235)]" : ""}`}
        >
          <div className="flex items-start justify-between gap-2">
            <span className="text-xs font-semibold tracking-[0.12em]">{location.location}</span>
            <span className="text-xl">
              {location.temperature_c == null ? "—" : `${Math.round(location.temperature_c)}°`}
            </span>
          </div>
          <div className="mt-4 flex items-center justify-between text-[9px] tracking-[0.12em] text-[var(--muted-foreground)]">
            <span>{location.region.toUpperCase()}</span>
            <span>{location.epistemic_state}</span>
          </div>
        </button>
      ))}
    </div>
  );
}

function LoadingSurface() {
  return (
    <div className="space-y-3" aria-label="Loading Africa sensing">
      <div className="h-[360px] animate-pulse rounded-md bg-white/5" />
      <div className="h-28 animate-pulse rounded-md bg-white/[0.035]" />
    </div>
  );
}

export function AfricaCommand() {
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["africa-senses"],
    queryFn: getAfricaSenses,
    refetchInterval: GRID_REFRESH.WEATHER_MS,
    staleTime: GRID_REFRESH.WEATHER_STALE_MS,
    refetchOnWindowFocus: true,
    refetchIntervalInBackground: true,
  });
  const [selectedId, setSelectedId] = useState("nairobi");
  const [, tick] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => tick((value) => value + 1), 1_000);
    return () => window.clearInterval(timer);
  }, []);
  const selected = useMemo(
    () =>
      data?.weather.locations.find((item) => item.location_id === selectedId) ??
      data?.weather.locations[0],
    [data, selectedId],
  );

  if (isLoading) return <LoadingSurface />;
  if (!data || !selected)
    return (
      <div className="rounded-md border border-[var(--color-neon-orange)]/30 bg-[oklch(0.18_0.05_55/0.16)] p-6 text-sm text-[var(--color-neon-orange)]">
        AFRICA SENSING UNAVAILABLE · GRID CORE REMAINS ONLINE
      </div>
    );

  const healthyProviders = Object.values(data.weather.providers).filter(
    (state) => state === "HEALTHY",
  ).length;
  const reportAgeSeconds = Math.max(
    0,
    Math.floor((Date.now() - new Date(data.generated_at).getTime()) / 1_000),
  );
  const reportFreshness =
    reportAgeSeconds < 90 ? "LIVE" : reportAgeSeconds < 300 ? "RECENT" : "STALE";
  return (
    <div className="space-y-4">
      <header className="flex flex-col gap-4 border-b border-white/10 pb-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[10px] tracking-[0.22em] text-[var(--color-neon-green)]">
            <Activity size={13} /> GRID ONLINE · AFRICA SENSING
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-[0.08em] sm:text-3xl">
            CONTINENT COMMAND
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
            Measured conditions across {data.coverage.weather_hubs_observed} hubs and{" "}
            {data.coverage.regions_observed.length} regions. The interface spans{" "}
            {data.coverage.jurisdictions} jurisdictions; unobserved territory remains explicitly
            unclaimed.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[10px] tracking-[0.14em]">
          <StateBadge state={data.weather.state} />
          <StateBadge state={reportFreshness} />
          <span className="rounded-sm border border-white/10 px-2 py-1 text-[var(--muted-foreground)]">
            {healthyProviders}/{Object.keys(data.weather.providers).length} WEATHER SOURCES
          </span>
          <span className="rounded-sm border border-white/10 px-2 py-1 text-[var(--muted-foreground)]">
            OBSERVED {reportAgeSeconds}s AGO · {data.cache}
          </span>
          <button
            type="button"
            onClick={() => void refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-1.5 rounded-sm border border-white/15 px-2 py-1 text-[var(--foreground)] transition-colors hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-neon-cyan)] disabled:opacity-50"
          >
            <RefreshCw size={11} className={isFetching ? "animate-spin" : ""} /> REFRESH
          </button>
        </div>
      </header>

      <WeatherCommand weather={selected} />
      <WeatherStrip
        locations={data.weather.locations}
        selected={selected.location_id}
        onSelect={setSelectedId}
      />

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-md border border-[var(--color-neon-green)]/20 bg-[oklch(0.12_0.025_180/0.64)] p-5 sm:p-6">
          <header className="flex items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] text-[var(--color-neon-green)]">
                <Activity size={13} /> HEALTH SIGNALS
              </div>
              <h2 className="mt-2 text-xl font-semibold tracking-[0.08em]">
                CONTINENTAL SOURCE WATCH
              </h2>
            </div>
            <StateBadge state={data.health.state} />
          </header>
          <div className="mt-6 divide-y divide-white/8 border-y border-white/8">
            {Object.entries(data.health.providers).length ? (
              Object.entries(data.health.providers).map(([provider, state]) => (
                <div key={provider} className="grid grid-cols-[1fr_auto] gap-4 py-4">
                  <div>
                    <div className="text-xs font-semibold tracking-[0.13em]">
                      {provider.replace(/_/g, " ").toUpperCase()}
                    </div>
                    <div className="mt-1 text-xs text-[var(--muted-foreground)]">
                      Reported source · provenance retained · jurisdiction coverage varies
                    </div>
                  </div>
                  <StateBadge state={state === "LIVE" ? "HEALTHY" : state} />
                </div>
              ))
            ) : (
              <div className="py-8 text-sm text-[var(--muted-foreground)]">
                NO CURRENT APPROVED HEALTH SOURCE
              </div>
            )}
          </div>
        </section>

        <section className="rounded-md border border-[var(--color-neon-gold)]/22 bg-[oklch(0.125_0.03_75/0.55)] p-5 sm:p-6">
          <header className="flex items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-[10px] tracking-[0.2em] text-[var(--color-neon-gold)]">
                <ShieldCheck size={13} /> SOVEREIGNTY WATCH
              </div>
              <h2 className="mt-2 text-xl font-semibold tracking-[0.08em]">
                REGIONAL SITUATION REPORTS
              </h2>
            </div>
            <StateBadge state={data.sovereignty.state} />
          </header>
          <div className="mt-6 space-y-1">
            {data.sovereignty.reports.map((report) => (
              <div
                key={report.report_id}
                className="group flex items-center justify-between gap-4 border-b border-white/8 py-3 last:border-0"
              >
                <div className="min-w-0">
                  <div className="truncate text-xs font-semibold tracking-[0.12em]">
                    {report.jurisdiction.toUpperCase()}
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-[10px] text-[var(--muted-foreground)]">
                    <Database size={11} /> {report.source_coverage.length} source classes ·{" "}
                    {report.findings.length} findings
                  </div>
                </div>
                <StateBadge state={report.state} />
              </div>
            ))}
          </div>
          <p className="mt-5 text-xs leading-5 text-[var(--muted-foreground)]">
            Governance findings remain “NO CURRENT SOURCE” until an approved jurisdictional source
            is connected. Weather and health observations never become political claims.
          </p>
        </section>
      </div>
    </div>
  );
}
