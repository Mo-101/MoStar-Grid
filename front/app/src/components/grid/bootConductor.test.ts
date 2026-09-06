import { describe, expect, it } from "vitest";
import {
  BootConductor,
  deriveCeremonyProgress,
  deriveNodeCues,
  isDcxMindBound,
} from "./bootConductor";

describe("BootConductor narration contract", () => {
  it("requests exactly one narration segment source for every orb, in orb order", async () => {
    const requested: string[][] = [];
    const nodes = [
      { id: "first", label: "FIRST ORB", probe: async () => true },
      { id: "second", label: "SECOND ORB", probe: async () => true },
    ];
    const conductor = new BootConductor(nodes, async (labels) => {
      requested.push(labels);
      return { audioUrl: null, audioMs: 2_000, segments: [] };
    });

    await conductor.arm();

    expect(requested).toEqual([["FIRST ORB", "SECOND ORB"]]);
  });

  it("arms without starting: no probe runs until the operator begins", async () => {
    // The Grid must wait to be woken deliberately. Arming only gathers
    // narration and builds the clock — if this ever starts the ceremony, the
    // START AWAKENING button becomes unreachable and boot runs on its own.
    let probes = 0;
    const nodes = [
      {
        id: "first",
        label: "FIRST ORB",
        probe: async () => {
          probes += 1;
          return true;
        },
      },
    ];
    const conductor = new BootConductor(nodes, async () => ({
      audioUrl: null,
      audioMs: 2_000,
      segments: [],
    }));

    const frames: string[] = [];
    conductor.subscribe((frame) => frames.push(frame.phase));

    await conductor.arm();

    expect(probes).toBe(0);
    expect(frames.at(-1)).toBe("ARMED");
    expect(frames).not.toContain("RUNNING");
    // No teardown needed: an armed-but-unstarted conductor holds no frame loop
    // and no playing audio, which is precisely what this test asserts.
  });
});

describe("deriveNodeCues", () => {
  it("places nodes inside measured narration segments", () => {
    const cues = deriveNodeCues(
      [
        { text: "one", startMs: 0, endMs: 3_000 },
        { text: "two", startMs: 3_000, endMs: 6_000 },
      ],
      4,
      6_000,
    );

    expect(cues).toEqual([1_000, 2_000, 4_000, 5_000]);
  });

  it("uses a deterministic silent timeline without measured speech", () => {
    expect(deriveNodeCues([], 2, 10_000)).toEqual([4_100, 8_200]);
  });

  it("starts one real probe at each measured orb utterance", () => {
    const segments = Array.from({ length: 8 }, (_, index) => ({
      text: `orb ${index + 1}`,
      startMs: index * 1_000,
      endMs: (index + 1) * 1_000,
    }));

    expect(deriveNodeCues(segments, 8, 8_000)).toEqual([
      0, 1_000, 2_000, 3_000, 4_000, 5_000, 6_000, 7_000,
    ]);
  });
});

describe("deriveCeremonyProgress", () => {
  it("jumps to the next sequence point exactly when its utterance begins, not mid-span", () => {
    const segments = [
      { text: "short", startMs: 0, endMs: 1_000 },
      { text: "long", startMs: 1_000, endMs: 4_000 },
    ];

    expect(deriveCeremonyProgress(0, 4_000, segments, 2)).toBe(0.5);
    expect(deriveCeremonyProgress(500, 4_000, segments, 2)).toBe(0.5);
    expect(deriveCeremonyProgress(999, 4_000, segments, 2)).toBe(0.5);
    expect(deriveCeremonyProgress(1_000, 4_000, segments, 2)).toBe(1);
    expect(deriveCeremonyProgress(4_000, 4_000, segments, 2)).toBe(1);
  });
});

describe("DCX cognitive binding", () => {
  it("does not treat a loaded process as a sealed Grid mind", () => {
    expect(isDcxMindBound({ state: "LOADED", sealed: false })).toBe(false);
  });

  it("requires process seal and binding seal together", () => {
    expect(isDcxMindBound({ state: "SEALED", sealed: true })).toBe(false);
    expect(isDcxMindBound({ state: "SEALED", sealed: true, binding: "SEALED" })).toBe(true);
  });
});
