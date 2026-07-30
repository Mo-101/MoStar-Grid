// probe_phase1b.cypher
// 1. What do the 27 not-blanks actually say
MATCH (p:Philosophy) WHERE p.name IS NULL
RETURN id(p),
       left(p.core_principle, 150) AS principle,
       left(p.manifestation, 100)  AS manifestation
ORDER BY id(p) LIMIT 6;

// 2. Node 256's thousand-edge shape
MATCH (p) WHERE id(p) = 256
MATCH (p)-[r]-(x)
RETURN type(r) AS rel, labels(x) AS neighbor, count(*) AS c
ORDER BY c DESC;
