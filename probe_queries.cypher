MATCH (p:Philosophy)
RETURN p.name, count(*) AS copies, collect(id(p))[..4] AS ids
ORDER BY copies DESC, p.name;

MATCH (m:MoStarMoment)
RETURN id(m), m.name, m.title, keys(m) LIMIT 10;

MATCH (a)-[r]->(b)
WITH labels(a) AS source_labels, type(r) AS rel_type, labels(b) AS target_labels
RETURN source_labels, rel_type, target_labels, count(*) AS count
ORDER BY count DESC LIMIT 30;

MATCH (n) WHERE NOT (n)--()
WITH labels(n) AS orphan_labels
RETURN orphan_labels, count(*) AS count
ORDER BY count DESC;

CALL gds.graph.list() YIELD graphName, nodeCount, relationshipCount, memoryUsage
RETURN graphName, nodeCount, relationshipCount, memoryUsage;
