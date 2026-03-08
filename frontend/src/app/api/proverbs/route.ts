/**
 * Proverbs API — returns only real proverbs with provenance
 * Enforces the Grid's truth gate: no proverbs without valid provenance are served
 */

import { NextResponse } from "next/server";
import { driver } from "../../../lib/neo4j";
import { randomUUID } from "crypto";

export async function GET(_request: Request) {
  const provenanceRunId = randomUUID();
  const timestamp = new Date().toISOString();

  try {
    const session = driver.session();
    const query = `
      MATCH (p:Proverb)-[:BELONGS_TO]->(c:Culture)
      WHERE p.validation_status IN ['community_reviewed', 'scholarly']
      OPTIONAL MATCH (p)-[:RELATED_TO]->(odu:OduIfa)
      RETURN p {
        .id,
        .text,
        .translation,
        .language,
        .culture,
        .region,
        .meaning,
        .usage_context,
        .source,
        .validated_by,
        .validation_status,
        .related_odu: odu.name
      } AS proverb,
      c.name AS culture_name,
      c.region AS culture_region
      ORDER BY p.provenance_timestamp DESC
      LIMIT 50
    `;

    const result = await session.run(query);
    const proverbs = result.records.map(record => ({
      ...record.get("proverb"),
      culture: {
        name: record.get("culture_name"),
        region: record.get("culture_region")
      },
      provenance: {
        source: "neo4j",
        timestamp,
        upstream_id: record.get("proverb").id,
        ingestion_run_id: provenanceRunId
      }
    }));

    await session.close();

    return NextResponse.json({
      data: proverbs,
      meta: {
        count: proverbs.length,
        source: "neo4j",
        timestamp,
        ingestion_run_id: provenanceRunId
      }
    });

  } catch (error) {
    return NextResponse.json(
      {
        error: "Service unavailable",
        provenance: {
          source: "error",
          timestamp,
          upstream_id: "proverbs:list",
          ingestion_run_id: provenanceRunId,
          error: error instanceof Error ? error.message : String(error),
          error_type: "neo4j_query_error"
        }
      },
      { status: 503 }
    );
  }
}
