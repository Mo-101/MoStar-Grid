MATCH (n:RuntimeEvent)
WHERE NOT n:CanonicalComponent
WITH n, coalesce(n.timestamp, n.created_at) AS effectiveClock
RETURN valueType(effectiveClock) AS clockType, count(*) AS c
ORDER BY c DESC;
