MATCH (m:MoStarMoment {canonical_id: 'moment:mo_executor_activation:v1'})-[r]-(n)
RETURN type(r) AS relType, labels(n) AS nodeLabels, n.id AS nodeId, n.name AS nodeName
