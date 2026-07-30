MATCH (m:MoStarMoment)
RETURN m.id AS id, m.canonical_id AS canonical_id, m.name AS name
ORDER BY id IS NULL DESC, id