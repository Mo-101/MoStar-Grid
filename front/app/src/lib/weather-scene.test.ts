import { describe, expect, it } from "vitest";
import { classifyCondition, deriveScene, solarPosition } from "./weather-scene";

const NAIROBI = { latitude: -1.2864, longitude: 36.8172 };

describe("classifyCondition", () => {
  it("prefers the machine-readable WMO code over prose", () => {
    // Code 95 is a thunderstorm even if the prose summary disagrees.
    expect(classifyCondition({ weather_code: 95, summary: "clear sky" })).toEqual({
      condition: "THUNDERSTORM",
      confidence: "wmo",
    });
  });

  it("reads the OpenWeather prose the Grid actually receives", () => {
    expect(classifyCondition({ summary: "overcast clouds" })).toEqual({
      condition: "OVERCAST",
      confidence: "text",
    });
  });

  it("resolves compound prose to its most severe term", () => {
    expect(classifyCondition({ summary: "thunderstorm with heavy rain" }).condition).toBe(
      "THUNDERSTORM",
    );
    expect(classifyCondition({ summary: "heavy intensity rain" }).condition).toBe("HEAVY_RAIN");
    expect(classifyCondition({ summary: "light rain" }).condition).toBe("DRIZZLE");
  });

  it("falls back to a measured gauge when there is no code and no readable prose", () => {
    expect(classifyCondition({ summary: "Observed conditions", precipitation_mm: 4 })).toEqual({
      condition: "HEAVY_RAIN",
      confidence: "measurement",
    });
  });

  it("reports no confidence rather than inventing a condition", () => {
    expect(classifyCondition({ summary: "Observed conditions" }).confidence).toBe("none");
  });
});

describe("solarPosition", () => {
  it("puts the sun below the horizon over Nairobi before dawn", () => {
    // 00:00 UTC is roughly 02:30 solar time at 36.8°E.
    const { elevationDeg } = solarPosition(
      NAIROBI.latitude,
      NAIROBI.longitude,
      new Date("2026-08-16T00:00:00Z"),
    );
    expect(elevationDeg).toBeLessThan(-20);
  });

  it("puts the sun high over Nairobi at local midday", () => {
    const { elevationDeg } = solarPosition(
      NAIROBI.latitude,
      NAIROBI.longitude,
      new Date("2026-08-16T09:30:00Z"),
    );
    expect(elevationDeg).toBeGreaterThan(60);
  });

  it("keeps the two hemispheres genuinely out of step", () => {
    const at = new Date("2026-12-21T10:00:00Z");
    const cairo = solarPosition(30.0444, 31.2357, at).elevationDeg;
    const capeTown = solarPosition(-33.9249, 18.4241, at).elevationDeg;
    // Southern-hemisphere summer solstice: Cape Town must be higher than Cairo.
    expect(capeTown).toBeGreaterThan(cairo);
  });
});

describe("deriveScene", () => {
  it("marks night from the hub's own position, not the viewer's clock", () => {
    const scene = deriveScene({
      ...NAIROBI,
      summary: "clear sky",
      observed_at: "2026-08-16T00:00:00Z",
    });
    expect(scene.night).toBe(true);
    expect(scene.daylight).toBe(0);
  });

  it("scales rain intensity with the measured gauge", () => {
    const light = deriveScene({ ...NAIROBI, weather_code: 61, precipitation_mm: 0.2 });
    const heavy = deriveScene({ ...NAIROBI, weather_code: 61, precipitation_mm: 8 });
    expect(heavy.rainRate).toBeGreaterThan(light.rainRate);
  });

  it("damps rain when the forecast probability is low", () => {
    const certain = deriveScene({ ...NAIROBI, weather_code: 61, precipitation_probability: 100 });
    const unlikely = deriveScene({ ...NAIROBI, weather_code: 61, precipitation_probability: 0 });
    expect(unlikely.rainRate).toBeLessThan(certain.rainRate);
  });

  it("drives drift from the direction the wind blows toward", () => {
    // 270° is a westerly — air travels west to east, so cloud moves rightward.
    const westerly = deriveScene({ ...NAIROBI, summary: "cloudy", wind_direction_deg: 270 });
    expect(westerly.windX).toBeGreaterThan(0);
    const easterly = deriveScene({ ...NAIROBI, summary: "cloudy", wind_direction_deg: 90 });
    expect(easterly.windX).toBeLessThan(0);
  });

  it("never rains or flashes on a clear reading", () => {
    const scene = deriveScene({ ...NAIROBI, weather_code: 0 });
    expect(scene.rainRate).toBe(0);
    expect(scene.lightning).toBe(false);
  });

  it("renders the live Nairobi reading the Grid is currently serving", () => {
    // Captured from the running /api/senses/africa payload: OpenWeather prose,
    // no WMO code, no precipitation reading, wind from the NNE.
    const scene = deriveScene({
      ...NAIROBI,
      summary: "overcast clouds",
      humidity_pct: 61,
      wind_kph: 10.6,
      wind_direction_deg: 30,
      precipitation_probability: null,
      precipitation_mm: null,
      observed_at: "2026-08-16T12:00:00Z",
    });

    expect(scene.condition).toBe("OVERCAST");
    expect(scene.confidence).toBe("text");
    expect(scene.cloudCover).toBeGreaterThan(0.9);
    // Overcast is not rain — a closed deck must stay dry.
    expect(scene.rainRate).toBe(0);
    expect(scene.lightning).toBe(false);
    expect(scene.hazeDensity).toBe(0);
    // A NNE wind carries the deck toward the south-west, i.e. leftward.
    expect(scene.windX).toBeLessThan(0);
    // Local solar noon at 36.8°E is around 09:30 UTC, so midday UTC is
    // afternoon in Nairobi — still daylight.
    expect(scene.night).toBe(false);
    expect(scene.daylight).toBeGreaterThan(0.5);
  });

  it("only hazes genuinely humid air", () => {
    expect(deriveScene({ ...NAIROBI, summary: "clear sky", humidity_pct: 61 }).hazeDensity).toBe(0);
    expect(
      deriveScene({ ...NAIROBI, summary: "clear sky", humidity_pct: 95 }).hazeDensity,
    ).toBeGreaterThan(0);
  });
});
