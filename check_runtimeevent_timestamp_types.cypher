MATCH (n:RuntimeEvent)
WHERE NOT n:CanonicalComponent
RETURN valueType(n.timestamp) AS timestampType, count(*) AS c
ORDER BY c DESC;
