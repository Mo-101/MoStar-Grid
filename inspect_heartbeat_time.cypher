// 1) What time-like properties exist, if any?
MATCH (n:ExecutorHeartbeat)
UNWIND keys(n) AS k
WITH k, count(*) AS c
WHERE k CONTAINS 'time' OR k CONTAINS 'date' OR k ENDS WITH '_at' OR k = 'ts'
RETURN k, c
ORDER BY c DESC, k;

// 2) Sample real nodes to see the actual shape
MATCH (n:ExecutorHeartbeat)
RETURN id(n) AS internalId, properties(n) AS props
LIMIT 10;

// 3) Check whether time is implied via relationships instead of properties
MATCH (n:ExecutorHeartbeat)-[r]-(other)
RETURN type(r) AS relType, labels(other) AS otherLabels, count(*) AS c
ORDER BY c DESC;

// 4) If there is a candidate fallback field, measure coverage explicitly
MATCH (n:ExecutorHeartbeat)
RETURN
  count(*) AS total,
  count(n.created_at) AS haveCreatedAt,
  count(n.updated_at) AS haveUpdatedAt,
  count(n.ts) AS haveTs,
  count(n.occurred_at) AS haveOccurredAt;
