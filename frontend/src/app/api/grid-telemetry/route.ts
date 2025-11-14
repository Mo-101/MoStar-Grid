import { NextResponse } from "next/server";
import neo4j, { Driver } from "neo4j-driver";
import { promises as fs } from "fs";
import path from "path";

type MomentRecord = {
  initiator: string;
  receiver: string;
  description: string;
  trigger_type: string;
  resonance_score: number;
  timestamp: string;
  quantum_id: string;
};

type AgentTelemetry = {
  id: string;
  name: string;
  status: string;
  manifestationStrength: number;
  capabilities: string[];
};

const LOG_PATH =
  process.env.MOSTAR_MOMENTS_LOG ??
  path.resolve(process.cwd(), "..", "logs", "mostar_moments.jsonl");

const STATUS_ENDPOINT =
  process.env.CORE_ENGINE_STATUS_URL ??
  "http://localhost:8001/api/v1/status";

const TELEMETRY_WINDOW = Number(process.env.MOSTAR_TELEMETRY_WINDOW ?? "12");

async function fetchBackendStatus() {
  try {
    const response = await fetch(STATUS_ENDPOINT, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Backend status ${response.status}`);
    }
    const data = await response.json();
    return { ok: true, data };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Status fetch failed",
    };
  }
}

async function readLocalMoments(): Promise<MomentRecord[]> {
  try {
    const file = await fs.readFile(LOG_PATH, "utf-8");
    const lines = file
      .trim()
      .split("\n")
      .filter(Boolean)
      .slice(-TELEMETRY_WINDOW);

    return lines
      .map((line) => JSON.parse(line) as MomentRecord)
      .reverse();
  } catch {
    return [];
  }
}

async function fetchGraphSummary() {
  if (!process.env.NEO4J_URI || !process.env.NEO4J_PASSWORD) {
    return { ok: false, error: "Neo4j environment not configured" };
  }

  let driver: Driver | null = null;
  try {
    driver = neo4j.driver(
      process.env.NEO4J_URI,
      neo4j.auth.basic(
        process.env.NEO4J_USER ?? "neo4j",
        process.env.NEO4J_PASSWORD
      ),
      {
        disableLosslessIntegers: true,
      }
    );

    const session = driver.session();
    try {
      const summaryResult = await session.run(
        `
        MATCH (m:MostarMoment)
        WITH m
        ORDER BY m.timestamp DESC
        RETURN count(m) AS totalMoments,
               avg(m.resonance_score) AS avgResonance,
               count(DISTINCT m.initiator) AS distinctInitiators,
               collect({
                 quantum_id: m.quantum_id,
                 initiator: m.initiator,
                 receiver: m.receiver,
                 description: m.description,
                 trigger_type: m.trigger_type,
                 resonance_score: m.resonance_score,
                 timestamp: m.timestamp
               })[0..12] AS latest
        `
      );

      const record = summaryResult.records[0];
      let agents: AgentTelemetry[] = [];
      let agentWarning: string | undefined;

      try {
        const agentResult = await session.run(
          `
          MATCH (agent:Agent)
          RETURN {
            id: coalesce(agent.id, agent.name, toString(id(agent))),
            name: coalesce(agent.name, agent.id, "Unnamed Agent"),
            status: coalesce(agent.status, "UNKNOWN"),
            manifestationStrength: coalesce(agent.manifestationStrength, 0.0),
            capabilities: coalesce(agent.capabilities, [])
          } AS agent
          ORDER BY toUpper(agent.name)
          `
        );

        agents = agentResult.records.map((agentRecord) => agentRecord.get("agent") as AgentTelemetry);
        if (!agents.length) {
          agentWarning =
            "Neo4j is online but returned zero Agent nodes. Re-run the Palaver System seeding ritual.";
        }
      } catch (agentError) {
        console.error("Agent telemetry query failed", agentError);
      }

      return {
        ok: true,
        stats: {
          totalMoments: record?.get("totalMoments") ?? 0,
          avgResonance: record?.get("avgResonance") ?? 0,
          distinctInitiators: record?.get("distinctInitiators") ?? 0,
        },
        latest: (record?.get("latest") as MomentRecord[]) ?? [],
        agents,
        agentWarning,
      };
    } finally {
      await session.close();
    }
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Neo4j summary failed",
    };
  } finally {
    if (driver) {
      await driver.close();
    }
  }
}

export async function GET() {
  const [backend, logEntries, graph] = await Promise.all([
    fetchBackendStatus(),
    readLocalMoments(),
    fetchGraphSummary(),
  ]);

  return NextResponse.json({
    backend,
    graph,
    log: {
      entries: logEntries,
      path: LOG_PATH,
    },
    generatedAt: new Date().toISOString(),
  });
}
