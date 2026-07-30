MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS count ORDER BY count DESC;
MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count ORDER BY count DESC;
