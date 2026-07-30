"""RP_Telemetry_v1 retention policy: non-destructive upsert, read-only census/sample,
and the export/delete eligibility gate.

Confirmed against live schema 2026-07-21: RP_Telemetry_v1 already exists
(sealed 2026-07-20T21:11:51Z) with archive_location and max_age_days=90 set
for real. The upsert here must never clobber those with defaults — every
field is coalesced against the existing node, so re-running this only fills
gaps on a node that doesn't exist yet. It does not perform export, manifest
creation, receipt writes, or delete; those remain separate, gated steps.
"""

import logging
from datetime import date

logger = logging.getLogger("grid_telemetry_retention")

NEO4J_DATABASE = "neo4j"

RP_TELEMETRY_V1_DEFAULTS = {
    "id": "RP_Telemetry_v1",
    "domain": "Metric|BodyLayer|ExecutorHeartbeat|RuntimeEvent",
    "strategy": "ARCHIVE_THEN_RELEASE",
    "archive_format": "jsonl.gz + sha256 manifest",
    "archive_location": "dell:/home/idona/MoStar/archives/telemetry/",
    "max_age_days": 90,
    "immutable_flag": False,
    "reason": "Orphaned telemetry grains; graph holds thought, archive holds pulse",
    "authored_by": "Flame",
}

_UPSERT_RETENTION_POLICY = """
MERGE (r:RetentionPolicy {id: $id})
SET r.domain          = coalesce(r.domain, $domain),
    r.strategy         = coalesce(r.strategy, $strategy),
    r.archive_format   = coalesce(r.archive_format, $archive_format),
    r.archive_location = coalesce(r.archive_location, $archive_location),
    r.max_age_days     = coalesce(r.max_age_days, $max_age_days),
    r.immutable_flag   = coalesce(r.immutable_flag, $immutable_flag),
    r.reason           = coalesce(r.reason, $reason),
    r.authored_by      = coalesce(r.authored_by, $authored_by),
    r.created_at       = coalesce(r.created_at, datetime())
RETURN r { .* } AS policy
"""

_TELEMETRY_CENSUS = """
MATCH (n)
WHERE ((n:Metric AND n:BodyLayer) OR n:ExecutorHeartbeat OR n:RuntimeEvent)
  AND NOT n:CanonicalComponent
WITH n, coalesce(n.timestamp, n.created_at,
                  CASE WHEN n.last_heartbeat IS NOT NULL THEN datetime(n.last_heartbeat) END
             ) AS effectiveClock
RETURN labels(n) AS labelSet,
       count(n) AS total,
       min(effectiveClock) AS earliest,
       max(effectiveClock) AS latest,
       count(effectiveClock) AS haveTimestamp
ORDER BY total DESC
"""
# ExecutorHeartbeat's clock lives under created_at (current schema) or
# last_heartbeat (node 77692, the one pre-migration legacy heartbeat);
# RuntimeEvent/Metric+BodyLayer use timestamp. coalesce() picks whichever
# is present rather than assuming one property name across all classes.

# Node 101797 (runtime-event-template.backbone.activation.bootstrap) is a schema
# scaffold node, not a telemetry instance: status=EVENT_TEMPLATE, canonical=false,
# attested=false, wired via ENABLED_BY into the component architecture. It shares
# the RuntimeEvent label but is not sweepable telemetry, so every query here
# excludes :CanonicalComponent explicitly rather than relying on label alone.

_SAMPLE_BY_LABEL = {
    "executorHeartbeat": """
        MATCH (n:ExecutorHeartbeat)
        WHERE NOT n:CanonicalComponent
        RETURN id(n) AS internalId, labels(n) AS labels, properties(n) AS properties
        LIMIT 5
    """,
    "runtimeEvent": """
        MATCH (n:RuntimeEvent)
        WHERE NOT n:CanonicalComponent
        RETURN id(n) AS internalId, labels(n) AS labels, properties(n) AS properties
        LIMIT 5
    """,
    "metricBodyLayer": """
        MATCH (n)
        WHERE n:Metric AND n:BodyLayer AND NOT n:CanonicalComponent
        RETURN id(n) AS internalId, labels(n) AS labels, properties(n) AS properties
        LIMIT 5
    """,
}


async def upsert_telemetry_retention_policy(driver) -> dict:
    """Non-destructive: only fills fields absent on the existing RP_Telemetry_v1 node."""
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(_UPSERT_RETENTION_POLICY, **RP_TELEMETRY_V1_DEFAULTS)
        record = await result.single()
    if not record:
        raise RuntimeError("Failed to upsert RP_Telemetry_v1")
    return dict(record["policy"])


async def census_telemetry(driver) -> list[dict]:
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(_TELEMETRY_CENSUS)
        return await result.data()


async def sample_telemetry(driver) -> dict:
    samples = {}
    async with driver.session(database=NEO4J_DATABASE) as session:
        for key, query in _SAMPLE_BY_LABEL.items():
            result = await session.run(query)
            samples[key] = await result.data()
    return samples


async def assess_telemetry_retention(driver) -> dict:
    """Read-only assessment plus policy upsert. Never exports, archives, or deletes."""
    policy = await upsert_telemetry_retention_policy(driver)
    census = await census_telemetry(driver)
    samples = await sample_telemetry(driver)

    timestamp_coverage_complete = all(
        row["haveTimestamp"] == row["total"] for row in census
    )

    archive_location = str(policy.get("archive_location", "")).strip()
    archive_path_confirmed = archive_location not in ("", "PENDING_CONFIRMATION")

    blockers = []
    if not timestamp_coverage_complete:
        blockers.append(
            "Telemetry timestamp coverage is incomplete; policy needs fallback rules before export/delete."
        )
    if not archive_path_confirmed:
        blockers.append(
            "Archive location is not confirmed; export/delete is blocked."
        )

    return {
        "policy": policy,
        "census": census,
        "samples": samples,
        "timestampCoverageComplete": timestamp_coverage_complete,
        "archivePathConfirmed": archive_path_confirmed,
        "exportEligible": len(blockers) == 0,
        "blockers": blockers,
        "assessed_at": date.today().isoformat(),
    }
