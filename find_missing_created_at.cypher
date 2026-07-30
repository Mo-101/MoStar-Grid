MATCH (n:ExecutorHeartbeat)
WHERE n.created_at IS NULL
RETURN id(n) AS internalId, labels(n) AS labels, properties(n) AS props;
