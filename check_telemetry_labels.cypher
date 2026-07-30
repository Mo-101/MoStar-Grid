// read-only: does the graph actually have BodyLayer/RuntimeEvent labels, and any existing RetentionPolicy?
CALL db.labels() YIELD label
WHERE label IN ['Metric','BodyLayer','ExecutorHeartbeat','RuntimeEvent','KnowledgeGraphTriple','RetentionPolicy']
RETURN label
ORDER BY label;

MATCH (r:RetentionPolicy)
RETURN r.id AS id, keys(r) AS propKeys;

MATCH (n) WHERE n:Metric OR n:ExecutorHeartbeat
RETURN labels(n) AS labelSet, count(n) AS c
ORDER BY c DESC
LIMIT 10;
