MATCH (n:RuntimeEvent)
WHERE NOT n:CanonicalComponent AND n.timestamp IS NULL
RETURN id(n) AS internalId, properties(n) AS props;
