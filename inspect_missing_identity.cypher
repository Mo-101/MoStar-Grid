MATCH (m:MoStarMoment)
WHERE m.id IS NULL
RETURN m LIMIT 10;

MATCH (m:MoStarMoment)
RETURN
  count(m) AS totalMoments,
  count(m.id) AS withId,
  count(m.quantum_id) AS withQuantumId,
  count(m.canonical_id) AS withCanonicalId,
  count(m.uuid) AS withUuid,
  count(m.moment_id) AS withMomentId
