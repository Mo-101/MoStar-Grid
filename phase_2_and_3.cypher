MATCH (p:Philosophy) WHERE p.name IS NULL
RETURN id(p),
       left(p.core_principle, 150) AS principle,
       left(p.manifestation, 100)  AS manifestation
ORDER BY id(p) LIMIT 6;

MATCH (p) WHERE id(p) = 256
MATCH (p)-[r]-(x)
RETURN type(r) AS rel, labels(x) AS neighbor, count(*) AS c
ORDER BY c DESC;

CREATE (r:RetentionPolicy {
  id: 'RP_Telemetry_v1',
  domain: 'Metric|BodyLayer|ExecutorHeartbeat|RuntimeEvent',
  strategy: 'ARCHIVE_THEN_RELEASE',
  archive_format: 'jsonl.gz + sha256 manifest',
  archive_location: 'dell:/home/idona/MoStar/archives/telemetry/',
  max_age_days: 90,
  immutable_flag: false,
  reason: 'Orphaned telemetry grains; graph holds thought, archive holds pulse',
  authored_by: 'Flame',
  created_at: datetime()
});
