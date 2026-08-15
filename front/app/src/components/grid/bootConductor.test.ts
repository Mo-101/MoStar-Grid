import { describe, expect, it } from "vitest";
import { deriveCeremonyProgress, deriveNodeCues } from "./bootConductor";

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
