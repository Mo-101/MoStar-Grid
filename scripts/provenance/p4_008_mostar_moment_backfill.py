#!/usr/bin/env python3
"""
P4-008 conservative MoStarMoment provenance backfill.

Rules:
- Preserve every existing node.
- Only add missing required provenance fields.
- Never overwrite existing provenance fields.
- Do not promote any legacy/imported/generated node to operational.
- Produce before/after counts.
"""

from __future__ import annotations

import argparse
import os
from typing import Any

from neo4j import GraphDatabase


COUNT_QUERY = """
MATCH (m:MoStarMoment)
RETURN
  count(m) AS total,
  count(m.source_type) AS with_source_type,
  count(m.verification_status) AS with_verification_status,
  count(m.operational_trust) AS with_operational_trust,
  count(m.seal) AS with_seal,
  count(m.source) AS with_source,
  count(m.created_by) AS with_created_by
"""

MISSING_QUERY = """
MATCH (m:MoStarMoment)
WHERE
  m.source_type IS NULL OR
  m.verification_status IS NULL OR
  m.operational_trust IS NULL OR
  m.seal IS NULL OR
  m.source IS NULL OR
  m.created_by IS NULL
RETURN count(m) AS missing_required_context
"""

DISTRIBUTION_QUERY = """
MATCH (m:MoStarMoment)
RETURN
  m.source_type AS source_type,
  m.verification_status AS verification_status,
  m.operational_trust AS operational_trust,
  m.seal AS seal,
  count(m) AS count
ORDER BY count DESC
"""

CLASSIFICATION_PREVIEW_QUERY = """
MATCH (m:MoStarMoment)
WHERE
  m.source_type IS NULL OR
  m.verification_status IS NULL OR
  m.operational_trust IS NULL OR
  m.seal IS NULL OR
  m.source IS NULL OR
  m.created_by IS NULL

WITH
  m,
  CASE
    WHEN "ExecutorHeartbeat" IN labels(m)
      OR "GridEvent" IN labels(m)
      OR "WooUtterance" IN labels(m)
      OR "StartupReport" IN labels(m)
      OR "AgentUtterance" IN labels(m)
      OR (
        "Grid" IN labels(m)
        AND (
          m.trigger_type IS NOT NULL OR
          m.mo_executor_id IS NOT NULL OR
          m.mo_processed IS NOT NULL OR
          m.resonance_score IS NOT NULL
        )
      )
      THEN "runtime_generated"
    ELSE "imported_archive"
  END AS proposed_source_type

WITH
  m,
  proposed_source_type,
  CASE proposed_source_type
    WHEN "runtime_generated" THEN "synthetic"
    ELSE "unverified"
  END AS proposed_verification_status,
  CASE proposed_source_type
    WHEN "runtime_generated" THEN "simulation"
    ELSE "reference"
  END AS proposed_operational_trust

RETURN
  labels(m) AS labels,
  proposed_source_type,
  proposed_verification_status,
  proposed_operational_trust,
  count(m) AS count
ORDER BY count DESC
"""

BACKFILL_QUERY = """
MATCH (m:MoStarMoment)
WHERE
  m.source_type IS NULL OR
  m.verification_status IS NULL OR
  m.operational_trust IS NULL OR
  m.seal IS NULL OR
  m.source IS NULL OR
  m.created_by IS NULL

WITH
  m,
  CASE
    WHEN "ExecutorHeartbeat" IN labels(m)
      OR "GridEvent" IN labels(m)
      OR "WooUtterance" IN labels(m)
      OR "StartupReport" IN labels(m)
      OR "AgentUtterance" IN labels(m)
      OR (
        "Grid" IN labels(m)
        AND (
          m.trigger_type IS NOT NULL OR
          m.mo_executor_id IS NOT NULL OR
          m.mo_processed IS NOT NULL OR
          m.resonance_score IS NOT NULL
        )
      )
      THEN "runtime_generated"
    ELSE "imported_archive"
  END AS proposed_source_type

WITH
  m,
  proposed_source_type,
  CASE proposed_source_type
    WHEN "runtime_generated" THEN "synthetic"
    ELSE "unverified"
  END AS proposed_verification_status,
  CASE proposed_source_type
    WHEN "runtime_generated" THEN "simulation"
    ELSE "reference"
  END AS proposed_operational_trust,
  CASE proposed_source_type
    WHEN "runtime_generated" THEN "grid_runtime_existing_mostar_moment_graph"
    ELSE "legacy_existing_mostar_moment_graph"
  END AS proposed_source,
  CASE proposed_source_type
    WHEN "runtime_generated" THEN "grid_runtime"
    ELSE "unknown_legacy_origin"
  END AS proposed_created_by,
  CASE proposed_source_type
    WHEN "runtime_generated"
      THEN "UNSEALED:P4-008-CONSERVATIVE-BACKFILL:RUNTIME-GENERATED"
    ELSE "UNSEALED:P4-008-CONSERVATIVE-BACKFILL:IMPORTED-ARCHIVE"
  END AS proposed_seal

SET
  m.source_type =
    coalesce(m.source_type, proposed_source_type),

  m.verification_status =
    coalesce(m.verification_status, proposed_verification_status),

  m.operational_trust =
    coalesce(m.operational_trust, proposed_operational_trust),

  m.seal =
    coalesce(m.seal, proposed_seal),

  m.source =
    coalesce(m.source, proposed_source),

  m.created_by =
    coalesce(m.created_by, proposed_created_by),

  m.p4_008_migration_date =
    coalesce(m.p4_008_migration_date, toString(datetime())),

  m.p4_008_migration_tool =
    coalesce(m.p4_008_migration_tool, "p4_008_conservative_backfill_v2_label_aware"),

  m.p4_008_backfill_basis =
    coalesce(
      m.p4_008_backfill_basis,
      "Missing provenance fields were conservatively classified from existing node labels and runtime fields. Runtime Grid labels became runtime_generated/synthetic/simulation. Unknown legacy labels became imported_archive/unverified/reference. No operational trust granted."
    )

RETURN count(m) AS nodes_backfilled
"""


def print_record(title: str, record: Any) -> None:
    print(f"\n== {title} ==")
    for key, value in dict(record).items():
        print(f"{key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually mutate Neo4j. Omit for dry-run.",
    )
    args = parser.parse_args()

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    database = os.getenv("NEO4J_DATABASE")
    password = os.environ["NEO4J_PASSWORD"]

    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session(database=database) if database else driver.session() as session:
            before = session.run(COUNT_QUERY).single()
            print_record("BEFORE COUNTS", before)

            missing = session.run(MISSING_QUERY).single()
            print_record("MISSING REQUIRED CONTEXT", missing)

            print("\n== CLASSIFICATION PREVIEW ==")
            for row in session.run(CLASSIFICATION_PREVIEW_QUERY):
                print(dict(row))

            if not args.apply:
                print("\nDRY RUN ONLY. No Neo4j mutation performed.")
                print("Run again with --apply to backfill missing fields.")
                return

            result = session.execute_write(lambda tx: tx.run(BACKFILL_QUERY).single())
            print_record("BACKFILL RESULT", result)

            after = session.run(COUNT_QUERY).single()
            print_record("AFTER COUNTS", after)

            print("\n== PROVENANCE DISTRIBUTION ==")
            for row in session.run(DISTRIBUTION_QUERY):
                print(dict(row))

    finally:
        driver.close()


if __name__ == "__main__":
    main()
