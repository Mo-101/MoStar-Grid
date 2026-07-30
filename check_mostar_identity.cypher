MATCH (m:MoStarMoment)
RETURN
  count(m) AS totalMoments,
  count(m.id) AS momentsWithId,
  count(DISTINCT m.id) AS distinctIds,
  count(m.quantum_id) AS momentsWithQuantumId,
  count(DISTINCT m.quantum_id) AS distinctQuantumIds;

MATCH (m:MoStarMoment)
WHERE m.id IS NOT NULL
WITH m.id AS id, count(*) AS occurrences
WHERE occurrences > 1
RETURN id, occurrences
ORDER BY occurrences DESC
LIMIT 50;
