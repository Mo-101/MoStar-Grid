// 🔥 MoStar REMOSTAR Model Definition
// Core MoScript structure for REMOSTAR symbolic + analytic operations.

export type MoScript = {
  id: string;
  name: string;
  trigger: string;
  inputs: string[];
  logic: (inputs: Record<string, any>) => any;
  voiceLine?: (result: any) => string;
  sass?: boolean;
};

// === REMOSTAR Core ===
export const REMOSTAR_CORE: MoScript = {
  id: "mo-remostar-core-001",
  name: "REMOSTAR Cognitive Core",
  trigger: "onTrainingRequest",
  inputs: ["data", "criteria"],

  /**
   * Process data and criteria to generate a list of processed items and a summary object.
   * If data is empty, returns an empty list and a summary object with count and avg_weight set to 0.
   * Otherwise, maps over the data array and assigns a random weight to each item, along with the criteria.
   * Returns an object with a processed array and a summary object containing count and avg_weight.
   * @param {{ data: any[], criteria: string }}
   * @returns {{ processed: { id: number, weight: string, criteria: string }[], summary: { count: number, avg_weight: string } }}
   */
  logic: ({ data, criteria }) => {
    const processed = data.length
      ? data.map((d: any, i: number) => ({
        id: i + 1,
        weight: Math.random().toFixed(3),
        criteria,
      }))
      : [];
    return {
      processed,
      summary: {
        count: processed.length,
        avg_weight:
          processed.length > 0
            ? (
<<<<<<< HEAD
              processed.reduce((a: number, b: { weight: string; }) => a + parseFloat(b.weight), 0) /
              processed.length
            ).toFixed(3)
=======
                processed.reduce((a: number, b: { weight: string }) => a + parseFloat(b.weight), 0) /
                processed.length
              ).toFixed(3)
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
            : 0,
      },
    };
  },

  /**
   * Returns a voice line string for the given result object.
   * @param { { processed: { id: number, weight: string, criteria: string }[], summary: { count: number, avg_weight: string } } } r
   * @returns { string } A voice line string describing the result of the REMOSTAR operation.
   */
  voiceLine: (r) =>
    `REMOSTAR: ${r.summary.count} items refined with mean weight ${r.summary.avg_weight}.`,
  sass: false,
};
// === End of REMOSTAR Core ===