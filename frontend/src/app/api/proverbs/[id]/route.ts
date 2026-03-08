/**
 * Proverb Detail API — returns a single proverb with full provenance
 * Enforces the Grid's truth gate: no proverb without valid provenance is served
 */

import { NextResponse } from "next/server";
import { driver } from "../../../../lib/neo4j";
import { randomUUID } from "crypto";

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const provenanceRunId = randomUUID();
  const timestamp = new Date().toISOString();
  const proverbId = params.id;

  try {
    const session = driver.session();
    const query = `
      MATCH (p:Proverb {id: $proverbId})-[:BELONGS_TO]->(c:Culture)
      WHERE p.validation_status IN ['community_reviewed', 'scholarly']
      OPTIONAL MATCH (p)-[:RELATED_TO]->(odu:OduIfa)
      OPTIONAL MATCH (p)<-[:REFERENCES]-(moment:MoStarMoment)
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
      c {
        .name,
        .region,
        .language
      } AS culture,
      collect(DISTINCT odu.name) AS related_odus,
      count(DISTINCT moment) AS referenced_by_moments
    `;

    const result = await session.run(query, { proverbId });
    
    if (result.records.length === 0) {
      await session.close();
      return NextResponse.json(
        {
          error: "Proverb not found",
          provenance: {
            source: "error",
            timestamp,
            upstream_id: proverbId,
            ingestion_run_id: provenanceRunId,
            error: "No proverb found with given ID or validation status insufficient",
            error_type: "not_found"
          }
        },
        { status: 404 }
      );
    }

    const record = result.records[0];
    const proverb = {
      ...record.get("proverb"),
      culture: record.get("culture"),
      related_odus: record.get("related_odus").filter(Boolean),
      referenced_by_moments: record.get("referenced_by_moments"),
      provenance: {
        source: "neo4j",
        timestamp,
        upstream_id: proverbId,
        ingestion_run_id: provenanceRunId
      }
    };

    await session.close();

    return NextResponse.json({
      data: proverb,
      meta: {
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
          upstream_id: proverbId,
          ingestion_run_id: provenanceRunId,
          error: error instanceof Error ? error.message : String(error),
          error_type: "neo4j_query_error"
        }
      },
      { status: 503 }
    );
  }
}
